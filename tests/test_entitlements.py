import unittest

from src.security.entitlements import build_entitlements, has_entitlement


class EntitlementTests(unittest.TestCase):
    def test_anonymous_user_gets_base_data_only(self):
        result = build_entitlements(None)

        self.assertEqual(result["access_level"], "anonymous")
        self.assertEqual(result["entitlements"], ["basic_data", "basic_history"])
        self.assertFalse(has_entitlement(None, "deep_analysis"))

    def test_free_personal_user_gets_base_data_only(self):
        result = build_entitlements({"plan": "free", "account_type": "personal"})

        self.assertEqual(result["access_level"], "free")
        self.assertEqual(result["entitlements"], ["basic_data", "basic_history"])

    def test_personal_pro_gets_deep_analysis(self):
        user = {"plan": "pro", "account_type": "personal"}

        self.assertEqual(build_entitlements(user)["access_level"], "personal")
        self.assertTrue(has_entitlement(user, "deep_analysis"))
        self.assertFalse(has_entitlement(user, "institutional_data"))

    def test_institutional_membership_gets_institutional_capabilities(self):
        user = {
            "plan": "free",
            "account_type": "personal",
            "has_institutional_membership": True,
        }

        result = build_entitlements(user)

        self.assertEqual(result["access_level"], "institutional")
        self.assertTrue(has_entitlement(user, "institutional_data"))
        self.assertTrue(has_entitlement(user, "workspace"))

    def test_inactive_institutional_subscription_falls_back_to_base_data(self):
        user = {
            "account_type": "personal",
            "institutional_memberships": [
                {"subscription_status": "canceled"},
            ],
        }

        result = build_entitlements(user)

        self.assertEqual(result["access_level"], "free")
        self.assertFalse(has_entitlement(user, "institutional_data"))


if __name__ == "__main__":
    unittest.main()
