import unittest

from src.notifications.email_policy import (
    build_idempotency_key,
    normalize_preferences,
    render_subscription_email,
)


class EmailPolicyTests(unittest.TestCase):
    def test_preferences_default_to_explicit_product_choices(self):
        prefs = normalize_preferences({})
        self.assertFalse(prefs["daily_brief"])
        self.assertFalse(prefs["risk_alerts"])
        self.assertFalse(prefs["weekly_digest"])
        self.assertFalse(prefs["product_updates"])
        self.assertEqual(prefs["frequency"], "daily")
        self.assertEqual(prefs["language"], "en")

    def test_preferences_reject_unknown_frequency_and_normalize_language(self):
        prefs = normalize_preferences(
            {
                "daily_brief": True,
                "risk_alerts": True,
                "frequency": "hourly",
                "language": "zh-CN",
            }
        )
        self.assertTrue(prefs["daily_brief"])
        self.assertTrue(prefs["risk_alerts"])
        self.assertEqual(prefs["frequency"], "daily")
        self.assertEqual(prefs["language"], "zh")

    def test_idempotency_key_is_stable_per_subscription_kind_and_date(self):
        first = build_idempotency_key(12, "daily_brief", "2026-09-03")
        second = build_idempotency_key(12, "daily_brief", "2026-09-03")
        different = build_idempotency_key(12, "weekly_digest", "2026-09-03")
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)

    def test_email_render_contains_non_advisory_disclaimer_and_unsubscribe_url(self):
        subject, text, html = render_subscription_email(
            kind="daily_brief",
            language="en",
            gfcri_value=42.5,
            alert_level="yellow",
            unsubscribe_url="https://gfcrilabs.com/unsubscribe?t=token",
        )
        self.assertIn("42.5", subject)
        self.assertIn("not investment advice", text.lower())
        self.assertIn("unsubscribe", html.lower())


if __name__ == "__main__":
    unittest.main()
