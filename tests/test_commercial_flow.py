import unittest

from api.commercial_policy import (
    is_institutional_account,
    public_billing_catalog,
    validate_institutional_lead,
)


class CommercialFlowTests(unittest.TestCase):
    def test_institutional_lead_requires_company_work_email_and_use_case(self):
        request = validate_institutional_lead(
            {
                "company_name": "Northstar Capital",
                "work_email": "risk@northstar.example",
                "full_name": "Ava Chen",
                "role": "Portfolio Risk",
                "team_size": "3-10",
                "use_case": "Weekly investment committee macro-risk review",
                "deployment": "Hosted",
                "language": "en",
            }
        )
        self.assertEqual(request["company_name"], "Northstar Capital")

        with self.assertRaises(ValueError):
            validate_institutional_lead(
                {
                    "company_name": "",
                    "work_email": "not-an-email",
                    "use_case": "",
                }
            )

    def test_institutional_guard_requires_institutional_account(self):
        self.assertFalse(is_institutional_account({"account_type": "personal"}))
        self.assertTrue(is_institutional_account({"account_type": "institutional"}))
        self.assertFalse(is_institutional_account(None))

    def test_billing_catalog_has_public_plan_metadata_without_secret_values(self):
        catalog = public_billing_catalog(personal_checkout_configured=False)
        self.assertIn("personal", catalog)
        self.assertIn("institutional", catalog)
        self.assertIn("monthly", catalog["personal"])
        self.assertIn("pilot", catalog["institutional"])
        self.assertNotIn("stripe_secret_key", str(catalog).lower())


if __name__ == "__main__":
    unittest.main()