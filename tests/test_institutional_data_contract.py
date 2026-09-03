import unittest

from src.data.institutional.contracts import (
    MODEL_VERSION,
    model_manifest,
    normalize_observation,
    summarize_quality,
)


class InstitutionalDataContractTests(unittest.TestCase):
    def test_manifest_exposes_version_entity_types_and_source_tiers(self):
        manifest = model_manifest()
        self.assertEqual(manifest["model_version"], MODEL_VERSION)
        self.assertIn("country", manifest["entity_types"])
        self.assertIn("economy", manifest["entity_types"])
        self.assertIn("internal_verified", manifest["source_tiers"])

    def test_normalize_observation_rejects_unknown_entity_and_missing_fields(self):
        observation = normalize_observation(
            {
                "tenant_id": "org-qa",
                "entity_type": "country",
                "entity_id": "US",
                "metric_id": "credit.hy_spread",
                "value": 3.4,
                "unit": "percent",
                "as_of": "2026-08-31",
                "frequency": "daily",
                "source_id": "fred",
                "quality_status": "verified",
            }
        )
        self.assertEqual(observation["entity_id"], "US")
        self.assertEqual(observation["source_tier"], "official")

        with self.assertRaises(ValueError):
            normalize_observation(
                {
                    "tenant_id": "org-qa",
                    "entity_type": "unsupported",
                    "entity_id": "x",
                    "metric_id": "risk",
                    "value": 1,
                    "unit": "score",
                    "as_of": "2026-08-31",
                    "frequency": "daily",
                    "source_id": "internal",
                    "source_tier": "internal_verified",
                }
            )

    def test_quality_summary_marks_stale_and_degraded_inputs(self):
        summary = summarize_quality(
            [
                {
                    "quality_status": "verified",
                    "as_of": "2026-08-31",
                },
                {
                    "quality_status": "degraded",
                    "as_of": "2026-08-01",
                },
            ],
            as_of="2026-09-02",
            stale_after_days=7,
        )
        self.assertEqual(summary["observation_count"], 2)
        self.assertEqual(summary["degraded_count"], 1)
        self.assertEqual(summary["stale_count"], 1)
        self.assertEqual(summary["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
