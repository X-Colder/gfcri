from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any

from api.billing.providers.base import CheckoutResult


@dataclass(frozen=True)
class WaffoSettings:
    environment: str
    merchant_id: str
    api_key: str
    private_key: str
    public_key: str
    monthly_plan_id: str
    annual_plan_id: str
    notify_url: str

    @property
    def enabled(self) -> bool:
        return bool(
            self.merchant_id
            and self.api_key
            and self.private_key
            and self.public_key
            and self.monthly_plan_id
            and self.annual_plan_id
            and self.notify_url
        )


class WaffoProvider:
    name = "waffo"

    def __init__(self, settings: WaffoSettings):
        self.settings = settings

    def configured(self) -> bool:
        return self.settings.enabled

    def _plan_id(self, plan: str) -> str:
        if plan == "monthly":
            return self.settings.monthly_plan_id
        if plan == "annual":
            return self.settings.annual_plan_id
        raise ValueError("Unsupported Waffo plan")

    def _client(self):
        try:
            from waffo import Environment, Waffo, WaffoConfig
        except ImportError as exc:
            raise RuntimeError("Waffo SDK is not installed") from exc

        environment = (
            Environment.PRODUCTION
            if self.settings.environment.lower() in {"production", "prod"}
            else Environment.SANDBOX
        )
        config = WaffoConfig(
            merchant_id=self.settings.merchant_id,
            api_key=self.settings.api_key,
            private_key=self.settings.private_key,
            waffo_public_key=self.settings.public_key,
            environment=environment,
        )
        return Waffo(config)

    @staticmethod
    def _read_value(value: Any, *keys: str) -> Any:
        data = getattr(value, "data", None)
        if data is not None:
            value = data
        if isinstance(value, dict):
            for key in keys:
                if key in value:
                    return value[key]
        for key in keys:
            if hasattr(value, key):
                return getattr(value, key)
        return None

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
        if not self.configured():
            raise RuntimeError("Waffo billing is not configured")

        plan_config = {
            "monthly": {"amount": "19.00", "periodType": "MONTH", "periodInterval": "1", "name": "GFCRI Pro Monthly"},
            "annual": {"amount": "149.00", "periodType": "YEAR", "periodInterval": "1", "name": "GFCRI Pro Annual"},
        }[plan]
        payload = {
            "subscriptionRequest": uuid.uuid4().hex,
            "merchantSubscriptionId": self._plan_id(plan),
            "currency": "USD",
            "amount": plan_config["amount"],
            "productInfo": {
                "description": plan_config["name"],
                "periodType": plan_config["periodType"],
                "periodInterval": plan_config["periodInterval"],
            },
            "merchantInfo": {
                "merchantId": self.settings.merchant_id,
            },
            "userInfo": {
                "userId": metadata.get("user_id", customer_email),
                "userEmail": customer_email,
            },
            "paymentInfo": {
                "productName": plan_config["name"],
                "cashierLanguage": "en-US",
            },
            "requestedAt": datetime.now(timezone.utc).isoformat(),
            "successRedirectUrl": success_url,
            "failedRedirectUrl": cancel_url,
            "cancelRedirectUrl": cancel_url,
            "notifyUrl": self.settings.notify_url,
            "subscriptionManagementUrl": management_url,
        }
        response = self._client().subscription().create(payload)
        checkout_url = self._read_value(
            response,
            "subscriptionAction",
            "checkoutUrl",
            "checkout_url",
            "action",
        )
        if not checkout_url:
            raise RuntimeError("Waffo did not return a hosted checkout URL")

        return CheckoutResult(
            checkout_url=str(checkout_url),
            provider=self.name,
            customer_id=self._read_value(response, "customerId", "customer_id"),
            subscription_id=self._read_value(response, "subscriptionId", "subscription_id"),
            metadata=metadata,
        )

    def verify_webhook(self, raw_body: bytes, signature: str) -> dict[str, Any]:
        if not signature:
            raise ValueError("Missing Waffo webhook signature")
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError as exc:
            raise RuntimeError("cryptography is required for Waffo webhook verification") from exc

        public_key = serialization.load_pem_public_key(self.settings.public_key.encode())
        public_key.verify(
            base64.b64decode(signature),
            raw_body,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return json.loads(raw_body.decode("utf-8"))
