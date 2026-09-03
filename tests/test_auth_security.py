import unittest
from datetime import datetime, timedelta, timezone

from src.security.passwords import hash_password, verify_password
from src.security.sessions import (
    SESSION_TTL_SECONDS,
    hash_session_token,
    new_session_token,
    session_expiry,
)


class PasswordSecurityTests(unittest.TestCase):
    def test_password_hash_is_salted_and_verifiable(self):
        first = hash_password("A-long-password-2026!")
        second = hash_password("A-long-password-2026!")

        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("A-long-password-2026!", first))
        self.assertFalse(verify_password("wrong-password", first))

    def test_password_hash_rejects_short_passwords(self):
        with self.assertRaises(ValueError):
            hash_password("short")


class SessionSecurityTests(unittest.TestCase):
    def test_session_token_is_random_and_only_hash_is_stored(self):
        first = new_session_token()
        second = new_session_token()

        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("gfcri_sess_"))
        self.assertNotEqual(first, hash_session_token(first))
        self.assertEqual(hash_session_token(first), hash_session_token(first))

    def test_session_expiry_uses_fixed_ttl(self):
        created = datetime(2026, 9, 3, tzinfo=timezone.utc)

        self.assertEqual(
            session_expiry(created),
            created + timedelta(seconds=SESSION_TTL_SECONDS),
        )


if __name__ == "__main__":
    unittest.main()
