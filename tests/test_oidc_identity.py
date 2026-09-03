import unittest

from src.security.oidc import (
    OIDCConfig,
    build_authorization_url,
    new_oidc_transaction,
    validate_oidc_claims,
)


class OIDCIdentityTests(unittest.TestCase):
    def test_transaction_contains_pkce_state_nonce_and_verifier(self):
        transaction = new_oidc_transaction()

        self.assertEqual(len(transaction["state_hash"]), 64)
        self.assertTrue(transaction["state"])
        self.assertTrue(transaction["nonce"])
        self.assertTrue(transaction["code_verifier"])
        self.assertTrue(transaction["code_challenge"])

    def test_authorization_url_contains_state_nonce_and_pkce(self):
        config = OIDCConfig(
            issuer="https://issuer.example",
            client_id="client-1",
            authorization_endpoint="https://issuer.example/authorize",
            token_endpoint="https://issuer.example/token",
            redirect_uri="https://gfcri.example/api/auth/oidc/acme/callback",
        )
        transaction = new_oidc_transaction()
        url = build_authorization_url(
            config,
            state=transaction["state"],
            nonce=transaction["nonce"],
            code_challenge=transaction["code_challenge"],
        )

        self.assertIn("response_type=code", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn(transaction["state"], url)

    def test_claims_require_issuer_audience_nonce_verified_email_and_domain(self):
        claims = validate_oidc_claims(
            {
                "iss": "https://issuer.example/",
                "aud": ["client-1"],
                "nonce": "nonce-1",
                "sub": "subject-1",
                "email": "analyst@acme.example",
                "email_verified": True,
                "name": "Analyst",
            },
            issuer="https://issuer.example",
            client_id="client-1",
            nonce="nonce-1",
            allowed_domains=("acme.example",),
        )

        self.assertEqual(claims["subject"], "subject-1")
        self.assertEqual(claims["email"], "analyst@acme.example")

    def test_claims_reject_unverified_or_wrong_domain(self):
        base = {
            "iss": "https://issuer.example",
            "aud": "client-1",
            "nonce": "nonce-1",
            "sub": "subject-1",
            "email": "analyst@other.example",
            "email_verified": False,
        }
        with self.assertRaises(ValueError):
            validate_oidc_claims(
                base,
                issuer="https://issuer.example",
                client_id="client-1",
                nonce="nonce-1",
                allowed_domains=("acme.example",),
            )


if __name__ == "__main__":
    unittest.main()
