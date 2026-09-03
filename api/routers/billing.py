import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from psycopg2.extras import Json, RealDictCursor

from api.billing.providers.base import normalize_provider_status
from api.resilience import CircuitBreaker, CircuitOpenError
from api.billing.providers.waffo import WaffoProvider, WaffoSettings
from api.routers.auth import (
    _create_token,
    _ensure_auth_schema,
    _user_payload,
    get_current_user,
)
from src.config import settings
from src.storage.database import get_connection

from api.commercial_policy import public_billing_catalog, validate_institutional_lead

router = APIRouter(prefix="/billing", tags=["billing"])
payment_circuit = CircuitBreaker(failure_threshold=3, recovery_seconds=30)


class CheckoutRequest(BaseModel):
    plan: str


class InstitutionalLeadRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    work_email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(default="", max_length=120)
    role: str = Field(default="", max_length=120)
    team_size: str = Field(default="", max_length=40)
    use_case: str = Field(min_length=10, max_length=2000)
    deployment: str = Field(default="", max_length=80)
    message: str = Field(default="", max_length=2000)
    language: str = Field(default="en", max_length=2)


def _ensure_billing_schema(conn) -> None:
    _ensure_auth_schema(conn)
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_provider TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_customer_id TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_subscription_id TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_price_id TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS billing_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'stripe',
                payload JSONB,
                processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS institutional_leads (
                id BIGSERIAL PRIMARY KEY,
                company_name VARCHAR(160) NOT NULL,
                work_email VARCHAR(255) NOT NULL,
                full_name VARCHAR(120),
                role VARCHAR(120),
                team_size VARCHAR(40),
                use_case TEXT NOT NULL,
                deployment VARCHAR(80),
                message TEXT,
                language VARCHAR(2) NOT NULL DEFAULT 'en',
                status VARCHAR(30) NOT NULL DEFAULT 'new',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def _iso_dt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if getattr(value, "tzinfo", None) is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _configured_price_id(plan: str) -> str:
    if plan == "monthly":
        return settings.stripe_monthly_price_id
    if plan == "annual":
        return settings.stripe_annual_price_id
    raise HTTPException(status_code=400, detail="Invalid billing plan")


def _billing_configured(plan: str) -> bool:
    return bool(
        settings.billing_provider == "stripe"
        and settings.stripe_secret_key
        and _configured_price_id(plan)
    )


def _waffo_provider() -> WaffoProvider:
    return WaffoProvider(
        WaffoSettings(
            environment=settings.waffo_environment,
            merchant_id=settings.waffo_merchant_id,
            api_key=settings.waffo_api_key,
            private_key=settings.waffo_private_key,
            public_key=settings.waffo_public_key,
            monthly_plan_id=settings.waffo_monthly_plan_id,
            annual_plan_id=settings.waffo_annual_plan_id,
            notify_url=settings.waffo_notify_url,
        )
    )


def _personal_billing_configured() -> bool:
    if settings.billing_provider == "waffo":
        return _waffo_provider().configured()
    return _billing_configured("monthly") and _billing_configured("annual")


def _default_success_url() -> str:
    return settings.billing_success_url or f"{settings.public_base_url.rstrip('/')}/?checkout=success"


def _default_cancel_url() -> str:
    return settings.billing_cancel_url or f"{settings.public_base_url.rstrip('/')}/pricing?checkout=cancel"


def _stripe_request(path: str, form: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        f"https://api.stripe.com{path}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.stripe_secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    def operation() -> dict[str, Any]:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())

    try:
        return payment_circuit.call(operation)
    except CircuitOpenError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "PAYMENT_PROVIDER_UNAVAILABLE", "message": "Payment provider temporarily unavailable."},
            headers={"Retry-After": "30"},
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stripe checkout failed: {exc}") from exc


def _load_user(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_billing_schema(conn)
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def _activate_subscription(user_id: int, plan: str, stripe_customer_id: str | None = None, status: str = "active", period_end: Any = None) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_billing_schema(conn)
            period_end_dt = None
            if isinstance(period_end, (int, float)):
                period_end_dt = datetime.fromtimestamp(period_end, tz=timezone.utc)
            cur.execute(
                """
                UPDATE users
                SET plan = CASE WHEN %s IN ('active', 'trialing') THEN 'pro' ELSE plan END,
                    stripe_customer_id = COALESCE(%s, stripe_customer_id),
                    subscription_status = %s,
                    subscription_plan = %s,
                    subscription_current_period_end = COALESCE(%s, subscription_current_period_end)
                WHERE id = %s
                RETURNING *
                """,
                (status, stripe_customer_id, status, plan, period_end_dt, user_id),
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
    finally:
        conn.close()


def _cancel_subscription_for_customer(customer_id: str, status: str = "canceled") -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_billing_schema(conn)
            cur.execute(
                """
                UPDATE users
                SET plan = 'free',
                    subscription_status = %s
                WHERE stripe_customer_id = %s
                """,
                (status, customer_id),
            )
            conn.commit()
    finally:
        conn.close()


def _activate_provider_subscription(
    user_id: int,
    plan: str,
    status: str,
    provider: str,
    customer_id: str | None = None,
    subscription_id: str | None = None,
    price_id: str | None = None,
    period_end: Any = None,
) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_billing_schema(conn)
            period_end_dt = None
            if isinstance(period_end, (int, float)):
                period_end_dt = datetime.fromtimestamp(period_end, tz=timezone.utc)
            elif isinstance(period_end, str) and period_end:
                period_end_dt = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
            cur.execute(
                """
                UPDATE users
                SET plan = CASE WHEN %s IN ('active', 'trialing') THEN 'pro' ELSE plan END,
                    billing_provider = %s,
                    provider_customer_id = COALESCE(%s, provider_customer_id),
                    provider_subscription_id = COALESCE(%s, provider_subscription_id),
                    provider_price_id = COALESCE(%s, provider_price_id),
                    subscription_status = %s,
                    subscription_plan = %s,
                    subscription_current_period_end = COALESCE(%s, subscription_current_period_end)
                WHERE id = %s
                RETURNING *
                """,
                (
                    status,
                    provider,
                    customer_id,
                    subscription_id,
                    price_id,
                    status,
                    plan,
                    period_end_dt,
                    user_id,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
    finally:
        conn.close()


def _cancel_provider_subscription(customer_id: str, provider: str, status: str = "canceled") -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_billing_schema(conn)
            cur.execute(
                """
                UPDATE users
                SET plan = 'free', subscription_status = %s
                WHERE billing_provider = %s AND provider_customer_id = %s
                """,
                (status, provider, customer_id),
            )
            conn.commit()
    finally:
        conn.close()

def _record_event_once(event_id: str, event_type: str, payload: dict) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_billing_schema(conn)
            cur.execute(
                """
                INSERT INTO billing_events (event_id, event_type, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (event_id, event_type, Json(payload)),
            )
            inserted = cur.rowcount == 1
            conn.commit()
            return inserted
    finally:
        conn.close()


def _verify_stripe_signature(raw_body: bytes, signature_header: str) -> bool:
    if not settings.stripe_webhook_secret:
        return False
    parts = dict(
        item.split("=", 1)
        for item in signature_header.split(",")
        if "=" in item
    )
    timestamp = parts.get("t")
    expected = parts.get("v1")
    if not timestamp or not expected:
        return False
    signed_payload = f"{timestamp}.{raw_body.decode()}".encode()
    digest = hmac.new(settings.stripe_webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    return hmac.compare_digest(digest, expected)


@router.get("/status")
def billing_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    current = _load_user(int(user["user_id"]))
    if not current:
        raise HTTPException(status_code=404, detail="User not found")
    payload = _user_payload(current)
    token = _create_token(
        current["id"],
        current["email"],
        payload["plan"],
        payload.get("trial_expires_at"),
        payload.get("account_type", "personal"),
    )
    return {
        "billing_configured": _personal_billing_configured(),
        "provider": settings.billing_provider,
        "user": payload,
        "token": token,
        "subscription_status": current.get("subscription_status"),
        "subscription_plan": current.get("subscription_plan"),
        "subscription_current_period_end": _iso_dt(current.get("subscription_current_period_end")),
    }


@router.get("/catalog")
def billing_catalog():
    configured = _personal_billing_configured()
    return public_billing_catalog(personal_checkout_configured=configured)


@router.post("/institutional-leads", status_code=201)
def create_institutional_lead(req: InstitutionalLeadRequest):
    try:
        lead = validate_institutional_lead(req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_billing_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_leads (
                    company_name, work_email, full_name, role, team_size,
                    use_case, deployment, message, language
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    lead["company_name"],
                    lead["work_email"],
                    lead["full_name"],
                    lead["role"],
                    lead["team_size"],
                    lead["use_case"],
                    lead["deployment"],
                    lead["message"],
                    lead["language"],
                ),
            )
            lead_id = cur.fetchone()[0]
            conn.commit()
            return {"status": "received", "lead_id": lead_id}
    finally:
        conn.close()


@router.post("/checkout")
def create_checkout(req: CheckoutRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if req.plan not in {"monthly", "annual"}:
        raise HTTPException(status_code=400, detail="Invalid billing plan")

    current = _load_user(int(user["user_id"]))
    if not current:
        raise HTTPException(status_code=404, detail="User not found")
    if current.get("account_type") == "institutional":
        raise HTTPException(status_code=400, detail="Institutional accounts do not use personal checkout")

    if settings.billing_provider == "waffo":
        provider = _waffo_provider()
        if not provider.configured():
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "BILLING_NOT_CONFIGURED",
                    "message": "Waffo billing is not configured for this environment.",
                },
            )
        try:
            result = payment_circuit.call(lambda: provider.create_subscription_checkout(
                plan=req.plan,
                customer_email=current["email"],
                success_url=_default_success_url(),
                cancel_url=_default_cancel_url(),
                management_url=f"{settings.public_base_url.rstrip('/')}/pricing?billing=manage",
                metadata={"user_id": str(current["id"]), "plan": req.plan},
            ))
        except CircuitOpenError as exc:
            raise HTTPException(
                status_code=503,
                detail={"code": "PAYMENT_PROVIDER_UNAVAILABLE", "message": "Payment provider temporarily unavailable."},
                headers={"Retry-After": "30"},
            ) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Waffo checkout failed: {exc}") from exc
        return {
            "provider": result.provider,
            "checkout_url": result.checkout_url,
            "customer_id": result.customer_id,
            "subscription_id": result.subscription_id,
        }

    if not _billing_configured(req.plan):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "BILLING_NOT_CONFIGURED",
                "message": "Stripe billing is not configured for this environment.",
            },
        )

    session = _stripe_request(
        "/v1/checkout/sessions",
        {
            "mode": "subscription",
            "client_reference_id": str(current["id"]),
            "customer_email": current["email"],
            "line_items[0][price]": _configured_price_id(req.plan),
            "line_items[0][quantity]": "1",
            "metadata[user_id]": str(current["id"]),
            "metadata[plan]": req.plan,
            "subscription_data[metadata][user_id]": str(current["id"]),
            "subscription_data[metadata][plan]": req.plan,
            "success_url": _default_success_url(),
            "cancel_url": _default_cancel_url(),
            "allow_promotion_codes": "true",
        },
    )
    return {
        "provider": "stripe",
        "checkout_url": session.get("url"),
        "session_id": session.get("id"),
    }

@router.post("/waffo/webhook")
async def waffo_webhook(request: Request, waffo_signature: str = Header(default="", alias="X-SIGNATURE")):
    raw = await request.body()
    try:
        event = _waffo_provider().verify_webhook(raw, waffo_signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Waffo webhook: {exc}") from exc

    event_id = str(event.get("id") or event.get("eventId") or event.get("notificationId") or hashlib.sha256(raw).hexdigest())
    event_type = str(event.get("type") or event.get("eventType") or event.get("notificationType") or "unknown")
    if not _record_event_once(event_id, event_type, event):
        return {"ok": True, "duplicate": True}

    data = event.get("data") or event.get("payload") or event
    if not isinstance(data, dict):
        return {"ok": True, "ignored": True}
    metadata = data.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    user_id = int(metadata.get("user_id") or data.get("userId") or 0)
    plan = str(metadata.get("plan") or data.get("plan") or "monthly")
    status = normalize_provider_status(data.get("status") or data.get("subscriptionStatus") or "active")
    customer_id = data.get("customerId") or data.get("customer_id")
    subscription_id = data.get("subscriptionId") or data.get("subscription_id")
    price_id = data.get("priceId") or data.get("price_id")
    period_end = data.get("currentPeriodEnd") or data.get("periodEnd") or data.get("subscriptionCurrentPeriodEnd")

    if user_id and status in {"active", "trialing", "past_due", "paused", "canceled", "incomplete"}:
        _activate_provider_subscription(
            user_id=user_id,
            plan=plan,
            status=status,
            provider="waffo",
            customer_id=customer_id,
            subscription_id=subscription_id,
            price_id=price_id,
            period_end=period_end,
        )
    elif customer_id and status == "canceled":
        _cancel_provider_subscription(customer_id, "waffo", status)

    return {"ok": True}

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="", alias="Stripe-Signature")):
    raw = await request.body()
    if not _verify_stripe_signature(raw, stripe_signature):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    event = json.loads(raw.decode())
    event_id = event.get("id")
    event_type = event.get("type") or "unknown"
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing event id")
    if not _record_event_once(event_id, event_type, event):
        return {"ok": True, "duplicate": True}

    data = (event.get("data") or {}).get("object") or {}
    if event_type == "checkout.session.completed":
        metadata = data.get("metadata") or {}
        user_id = int(metadata.get("user_id") or data.get("client_reference_id") or 0)
        plan = metadata.get("plan") or "monthly"
        if user_id:
            _activate_subscription(user_id, plan, data.get("customer"), "active")
    elif event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        metadata = data.get("metadata") or {}
        user_id = int(metadata.get("user_id") or 0)
        plan = metadata.get("plan") or "monthly"
        status = data.get("status") or "active"
        if user_id:
            _activate_subscription(user_id, plan, data.get("customer"), status, data.get("current_period_end"))
    elif event_type in {"customer.subscription.deleted", "customer.subscription.paused"}:
        customer = data.get("customer")
        if customer:
            _cancel_subscription_for_customer(customer, data.get("status") or "canceled")

    return {"ok": True}
