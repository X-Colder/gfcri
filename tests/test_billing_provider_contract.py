import unittest

from api.billing.providers.base import CheckoutResult, normalize_provider_status


class BillingProviderContractTests(unittest.TestCase):
    def test_checkout_result_exposes_only_provider_neutral_fields(self):
        result = CheckoutResult(
            checkout_url="https://checkout.example/session",
            provider="waffo",
            customer_id="customer-1",
            subscription_id="subscription-1",
            metadata={"plan": "monthly"},
        )
        self.assertEqual(result.checkout_url, "https://checkout.example/session")
        self.assertEqual(result.provider, "waffo")
        self.assertEqual(result.metadata["plan"], "monthly")

    def test_provider_statuses_normalize_to_application_states(self):
        self.assertEqual(normalize_provider_status("active"), "active")
        self.assertEqual(normalize_provider_status("trialing"), "trialing")
        self.assertEqual(normalize_provider_status("past_due"), "past_due")
        self.assertEqual(normalize_provider_status("cancelled"), "canceled")
        self.assertEqual(normalize_provider_status("unknown-status"), "unknown")


if __name__ == "__main__":
    unittest.main()
