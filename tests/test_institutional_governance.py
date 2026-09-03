import unittest
from datetime import datetime, timezone

from src.security.api_keys import (
    DEFAULT_API_KEY_SCOPES,
    hash_api_key,
    has_api_key_scope,
    new_api_key,
)
from src.security.audit import build_audit_event
from src.security.invitations import (
    hash_invitation_token,
    invitation_expiry,
    new_invitation_token,
)


class InstitutionalGovernanceTests(unittest.TestCase):
    def test_invitation_token_is_hashed_and_has_expiry(self):
        created = datetime(2026, 9, 3, tzinfo=timezone.utc)
        token = new_invitation_token()

        self.assertTrue(token.startswith("gfcri_inv_"))
        self.assertNotEqual(token, hash_invitation_token(token))
        self.assertGreater(invitation_expiry(created), created)

    def test_api_keys_have_explicit_scopes(self):
        token = new_api_key()

        self.assertTrue(token.startswith("gfcri_"))
        self.assertEqual(len(hash_api_key(token)), 64)
        self.assertTrue(has_api_key_scope(DEFAULT_API_KEY_SCOPES, "analysis:read"))
        self.assertFalse(has_api_key_scope(DEFAULT_API_KEY_SCOPES, "raw-data:export"))

    def test_audit_event_contains_actor_action_target_and_outcome(self):
        event = build_audit_event(
            organization_id=11,
            actor_user_id=7,
            actor_type="native",
            action="member.invite",
            target_type="membership",
            target_id="risk@example.com",
            outcome="accepted",
            request_id="req-1",
            metadata={"role": "analyst"},
        )

        self.assertEqual(event["organization_id"], 11)
        self.assertEqual(event["action"], "member.invite")
        self.assertEqual(event["outcome"], "accepted")
        self.assertEqual(event["metadata"]["role"], "analyst")
        self.assertIn("occurred_at", event)


if __name__ == "__main__":
    unittest.main()
