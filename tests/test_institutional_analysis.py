import unittest

from src.engines.institutional_analysis import analyze_target_observations


class InstitutionalAnalysisTests(unittest.TestCase):
    def test_target_analysis_blends_core_score_with_direct_pressure_overlay(self):
        result = analyze_target_observations(
            target={"entity_type": "economy", "entity_id": "US"},
            core_score=40,
            observations=[
                {
                    "metric_id": "risk.pressure_score",
                    "value": 80,
                    "quality_status": "verified",
                    "source_id": "internal-risk",
                    "as_of": "2026-08-31",
                }
            ],
            data_quality={"status": "verified", "coverage": 1.0},
        )
        self.assertEqual(result["target"]["entity_id"], "US")
        self.assertEqual(result["model_version"], "gfcri-institutional-v1")
        self.assertEqual(result["risk_score"], 52.0)
        self.assertEqual(result["dimensions"]["target_overlay"], 80.0)
        self.assertEqual(result["data_quality"]["status"], "verified")

    def test_target_analysis_marks_missing_overlay_as_degraded(self):
        result = analyze_target_observations(
            target={"entity_type": "country", "entity_id": "US"},
            core_score=40,
            observations=[],
            data_quality={"status": "empty", "coverage": 0},
        )
        self.assertEqual(result["risk_score"], 40.0)
        self.assertEqual(result["data_quality"]["status"], "degraded")
        self.assertEqual(result["dimensions"]["target_overlay"], None)


if __name__ == "__main__":
    unittest.main()
