from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class CheckoutResult:
    checkout_url: str
    provider: str
    customer_id: str | None = None
    subscription_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BillingProvider(Protocol):
    name: str

    def configured(self) -> bool:
        ...

    def create_subscription_checkout(
        self,
        *,
        plan: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        management_url: str,
        metadata: dict[str, str],
    ) -> CheckoutResult:
        ...

    def verify_webhook(self, raw_body: bytes, signature: str) -> dict[str, Any]:
        ...


def normalize_provider_status(status: str | None) -> str:
    normalized = str(status or "").strip().lower().replace("-", "_")
    aliases = {
        "cancelled": "canceled",
        "complete": "active",
        "completed": "active",
        "paid": "active",
        "payment_failed": "past_due",
    }
    return aliases.get(normalized, normalized if normalized in {
        "active",
        "trialing",
        "past_due",
        "canceled",
        "paused",
        "incomplete",
        "unknown",
    } else "unknown")
