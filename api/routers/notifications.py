from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from psycopg2.extras import RealDictCursor

from api.models.notifications import EmailSubscribeRequest, NotificationPreferencesRequest
from api.routers.auth import get_current_user
from src.config import settings
from src.notifications.email_policy import DEFAULT_PREFERENCES, build_idempotency_key, normalize_preferences
from src.notifications.email_service import EmailService
from src.notifications.outbox import enqueue_email
from src.storage.database import get_connection
from src.storage.email_schema import ensure_email_schema

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _preferences(row: dict) -> dict:
    return {
        key: row.get(key, DEFAULT_PREFERENCES[key])
        for key in DEFAULT_PREFERENCES
    } | {
        "email": row.get("email"),
        "status": row.get("status"),
        "verified_at": row.get("verified_at"),
    }


@router.post("/subscribe")
def subscribe(req: EmailSubscribeRequest, user=Depends(get_current_user)):
    email = req.email.strip().lower()
    preferences = normalize_preferences(req.model_dump())
    verification_token = secrets.token_urlsafe(32)
    unsubscribe_token = secrets.token_urlsafe(32)
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                INSERT INTO email_subscriptions (
                    user_id, email, status, verification_token_hash,
                    verification_expires_at, unsubscribe_token_hash,
                    daily_brief, risk_alerts, weekly_digest,
                    institutional_data_quality, product_updates, frequency,
                    risk_alert_level, language, timezone
                ) VALUES (%s, %s, 'unverified', %s, NOW() + INTERVAL '24 hours', %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    user_id = COALESCE(EXCLUDED.user_id, email_subscriptions.user_id),
                    verification_token_hash = EXCLUDED.verification_token_hash,
                    verification_expires_at = EXCLUDED.verification_expires_at,
                    unsubscribe_token_hash = EXCLUDED.unsubscribe_token_hash,
                    daily_brief = EXCLUDED.daily_brief,
                    risk_alerts = EXCLUDED.risk_alerts,
                    weekly_digest = EXCLUDED.weekly_digest,
                    institutional_data_quality = EXCLUDED.institutional_data_quality,
                    product_updates = EXCLUDED.product_updates,
                    frequency = EXCLUDED.frequency,
                    risk_alert_level = EXCLUDED.risk_alert_level,
                    language = EXCLUDED.language,
                    timezone = EXCLUDED.timezone,
                    status = CASE WHEN email_subscriptions.status = 'active' THEN 'active' ELSE 'unverified' END,
                    updated_at = NOW()
                RETURNING id, status
                """,
                (
                    user.get("user_id") if user else None,
                    email,
                    _hash_token(verification_token),
                    _hash_token(unsubscribe_token),
                    preferences["daily_brief"],
                    preferences["risk_alerts"],
                    preferences["weekly_digest"],
                    preferences["institutional_data_quality"],
                    preferences["product_updates"],
                    preferences["frequency"],
                    preferences["risk_alert_level"],
                    preferences["language"],
                    preferences["timezone"],
                ),
            )
            row = dict(cur.fetchone())
            verification_url = f"{settings.public_base_url.rstrip('/')}/api/notifications/verify?token={verification_token}"
            if row["status"] != "active":
                enqueue_email(
                    conn,
                    subscription_id=row["id"],
                    kind="verification",
                    idempotency_key=build_idempotency_key(row["id"], "verification", verification_token),
                    to_email=email,
                    subject="Verify your GFCRI email subscription",
                    text_body=f"Verify your GFCRI email subscription: {verification_url}",
                    html_body=f'<p>Verify your GFCRI email subscription.</p><p><a href="{verification_url}">Verify email</a></p>',
                )
            conn.commit()
            service = EmailService()
            return {
                "status": row["status"],
                "subscription_id": row["id"],
                "verification_required": row["status"] != "active",
                "email_delivery_configured": service.configured,
                "verification_url": (
                    f"{settings.public_base_url.rstrip('/')}/api/notifications/verify?token={verification_token}"
                    if service.configured
                    else None
                ),
            }
    finally:
        conn.close()


@router.get("/verify")
def verify(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Missing verification token")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                UPDATE email_subscriptions
                SET status = 'active', verified_at = NOW(), verification_token_hash = NULL,
                    verification_expires_at = NULL, updated_at = NOW()
                WHERE verification_token_hash = %s
                  AND verification_expires_at > NOW()
                RETURNING email
                """,
                (_hash_token(token),)
            )
            row = cur.fetchone()
            conn.commit()
            if not row:
                raise HTTPException(status_code=400, detail="Invalid or expired verification token")
            return RedirectResponse(
                url=f"{settings.public_base_url.rstrip('/')}/pricing?email_verified=1",
                status_code=303,
            )
    finally:
        conn.close()


@router.get("/preferences")
def get_preferences(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_email_schema(conn)
            cur.execute(
                "SELECT * FROM email_subscriptions WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                (int(user["user_id"]),),
            )
            row = cur.fetchone()
            return _preferences(dict(row)) if row else {"status": "none", **DEFAULT_PREFERENCES}
    finally:
        conn.close()


@router.put("/preferences")
def update_preferences(req: NotificationPreferencesRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    preferences = normalize_preferences(req.model_dump())
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                UPDATE email_subscriptions
                SET daily_brief=%s, risk_alerts=%s, weekly_digest=%s,
                    institutional_data_quality=%s, product_updates=%s,
                    frequency=%s, risk_alert_level=%s, language=%s,
                    timezone=%s, updated_at=NOW()
                WHERE user_id=%s
                RETURNING *
                """,
                (
                    preferences["daily_brief"],
                    preferences["risk_alerts"],
                    preferences["weekly_digest"],
                    preferences["institutional_data_quality"],
                    preferences["product_updates"],
                    preferences["frequency"],
                    preferences["risk_alert_level"],
                    preferences["language"],
                    preferences["timezone"],
                    int(user["user_id"]),
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Email subscription not found")
            conn.commit()
            return _preferences(dict(row))
    finally:
        conn.close()


@router.get("/unsubscribe")
def unsubscribe_get(token: str):
    result = unsubscribe(token)
    return RedirectResponse(
        url=f"{settings.public_base_url.rstrip('/')}/pricing?email_unsubscribed=1",
        status_code=303,
    )

@router.post("/unsubscribe")
def unsubscribe(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Missing unsubscribe token")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_email_schema(conn)
            cur.execute(
                """
                UPDATE email_subscriptions
                SET status='unsubscribed', daily_brief=FALSE, risk_alerts=FALSE,
                    weekly_digest=FALSE, institutional_data_quality=FALSE,
                    product_updates=FALSE, updated_at=NOW()
                WHERE unsubscribe_token_hash IN (%s, %s)
                RETURNING email
                """,
                (_hash_token(token), token),
            )
            row = cur.fetchone()
            conn.commit()
            if not row:
                raise HTTPException(status_code=404, detail="Subscription not found")
            return {"status": "unsubscribed"}
    finally:
        conn.close()
