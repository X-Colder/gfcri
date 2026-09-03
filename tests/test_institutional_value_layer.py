import unittest

from src.data.institutional.value_tiers import (
    VALUE_LAYER_VERSION,
    apply_visibility_policy,
    value_layer_manifest,
)
from src.engines.institutional_analysis import analyze_target_observations


class InstitutionalValueLayerTests(unittest.TestCase):
    def _evidence(self, tier: str):
        return analyze_target_observations(
            target={"entity_type": "economy", "entity_id": "US"},
            core_score=40,
            observations=[
                {
                    "metric_id": "risk.pressure_score",
                    "value": 80,
                    "quality_status": "verified",
                    "source_id": "internal-risk",
                    "source_tier": "internal_verified",
                    "as_of": "2026-08-31",
                }
            ],
            data_quality={"status": "verified", "coverage": 1.0},
            product_tier=tier,
            core_risk={
                "gfcri_value": 40,
                "alert_level": "yellow",
                "sub_index_details": {
                    "SI_CREDIT": {
                        "name": "Credit",
                        "score": 35,
                        "mean_stress": 0.3,
                        "mean_abs_stress": 0.2,
                        "transmission": 0.1,
                        "top_driver": "fred_hy_spread",
                        "node_scores": {"fred_hy_spread": 0.4},
                    }
                },
                "node_contributions": {
                    "fred_hy_spread": {
                        "display_name": "US High Yield OAS",
                        "zscore": 1.8,
                        "anomaly_score": 0.45,
                        "abs_score": 0.3,
                        "stress_direction": "higher_is_worse",
                    }
                },
                "chain_details": [
                    {
                        "id": "credit_contagion",
                        "name": "Credit Contagion",
                        "stress": 52,
                        "active": True,
                        "path_strength": 0.42,
                        "path": ["lqd", "hyg", "kospi"],
                        "node_scores": {"lqd": 0.3, "hyg": 0.5},
                    }
                ],
                "divergence": {
                    "status": "significant",
                    "gap": 0.22,
                    "details": [
                        {
                            "type": "surface_calm_deep_stress",
                            "title": "Surface calm / deep stress",
                        }
                    ],
                },
                "undercurrent_boost": 6,
                "active_chain_count": 2,
            },
        )

    def test_research_tier_exposes_derived_evidence_but_redacts_detail(self):
        result = self._evidence("research")

        self.assertEqual(result["risk_score"], 52.0)
        self.assertEqual(result["value_layer_version"], VALUE_LAYER_VERSION)
        self.assertFalse(result["delivery"]["raw_observations_exposed"])
        self.assertNotIn("formula_receipt", result)
        self.assertNotIn("source_tier", result["contributors"][0])
        self.assertNotIn("path", result["transmission_paths"][0])
        self.assertNotIn("value", result["drivers"][0])
        self.assertEqual(result["hidden_risk"]["status"], "significant")

    def test_private_tier_includes_governed_algorithm_evidence(self):
        result = self._evidence("private")

        self.assertIn("formula_receipt", result)
        self.assertEqual(result["contributors"][0]["source_tier"], "A")
        self.assertEqual(
            result["transmission_paths"][0]["path"],
            ["lqd", "hyg", "kospi"],
        )
        self.assertIn("details", result["hidden_risk"])
        self.assertFalse(result["delivery"]["raw_observations_exposed"])

    def test_team_tier_keeps_workflow_depth_without_raw_values(self):
        result = self._evidence("team")

        self.assertIn("watch_next", result)
        self.assertIn("risk_domains", result["dimensions"])
        self.assertIn("source_tier_mix", result["data_quality"])
        self.assertNotIn("value", result["drivers"][0])

    def test_unknown_product_tier_is_rejected(self):
        with self.assertRaises(ValueError):
            self._evidence("raw-data")

    def test_manifest_describes_derived_value_principle(self):
        manifest = value_layer_manifest()

        self.assertEqual(manifest["version"], VALUE_LAYER_VERSION)
        self.assertEqual([tier["id"] for tier in manifest["tiers"]], [
            "research",
            "team",
            "private",
        ])
        self.assertTrue(all(
            tier["raw_observations_exposed"] is False
            for tier in manifest["tiers"]
        ))


if __name__ == "__main__":
    unittest.main()
