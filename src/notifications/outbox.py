from __future__ import annotations

import json
from datetime import datetime, timezone

from psycopg2.extras import RealDictCursor

from src.notifications.email_policy import build_idempotency_key, render_subscription_email
from src.notifications.email_service import EmailService
from src.storage.database import get_connection, get_latest_risk_index
from src.storage.email_schema import ensure_email_schema


def enqueue_email(
    conn,
    *,
    subscription_id: int,
    kind: str,
    idempotency_key: str,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO email_outbox (
                subscription_id, kind, idempotency_key, to_email,
                subject, text_body, html_body
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            (subscription_id, kind, idempotency_key, to_email, subject, text_body, html_body),
        )


def queue_scheduled_emails() -> int:
    service = EmailService()
    if not service.configured:
        return 0
    risk = get_latest_risk_index() or {}
    risk_value = float(risk.get("gfcri_value") or risk.get("gfcri") or 0)
    alert_level = str(risk.get("alert_level") or "green")
    today = datetime.now(timezone.utc).date().isoformat()
    conn = get_connection()
    queued = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                SELECT id, email, language, unsubscribe_token_hash,
                       daily_brief, weekly_digest
                FROM email_subscriptions
                WHERE status = 'active' AND verified_at IS NOT NULL
                  AND (daily_brief = TRUE OR (weekly_digest = TRUE AND EXTRACT(ISODOW FROM NOW()) = 1))
                """
            )
            for subscription in cur.fetchall():
                kind = "daily_brief" if subscription["daily_brief"] else "weekly_digest"
                subject, text_body, html_body = render_subscription_email(
                    kind=kind,
                    language=subscription["language"],
                    gfcri_value=risk_value,
                    alert_level=alert_level,
                    unsubscribe_url=f"https://gfcrilabs.com/api/notifications/unsubscribe?token={subscription['unsubscribe_token_hash']}",
                )
                enqueue_email(
                    conn,
                    subscription_id=subscription["id"],
                    kind=kind,
                    idempotency_key=build_idempotency_key(subscription["id"], kind, today),
                    to_email=subscription["email"],
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                )
                queued += 1
            conn.commit()
            return queued
    finally:
        conn.close()


def process_email_outbox(batch_size: int = 20) -> int:
    service = EmailService()
    if not service.configured:
        return 0
    conn = get_connection()
    sent = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                SELECT id, to_email, subject, text_body, html_body
                FROM email_outbox
                WHERE status = 'pending' AND next_attempt_at <= NOW()
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT %s
                """,
                (batch_size,),
            )
            rows = [dict(row) for row in cur.fetchall()]
            conn.commit()

        for row in rows:
            try:
                service.send(
                    to_email=row["to_email"],
                    subject=row["subject"],
                    text_body=row["text_body"],
                    html_body=row["html_body"],
                )
            except Exception as exc:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE email_outbox
                        SET status = CASE WHEN attempts >= 4 THEN 'failed' ELSE 'pending' END,
                            attempts = attempts + 1,
                            next_attempt_at = NOW() + INTERVAL '10 minutes',
                            last_error = %s
                        WHERE id = %s
                        """,
                        (str(exc)[:1000], row["id"]),
                    )
                    conn.commit()
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE email_outbox
                        SET status='sent', sent_at=NOW(), attempts=attempts+1
                        WHERE id = %s
                        """,
                        (row["id"],),
                    )
                    conn.commit()
                sent += 1
        return sent
    finally:
        conn.close()
