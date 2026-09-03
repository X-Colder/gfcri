import unittest

from src.security.data_visibility import visible_risk_index


SAMPLE = {
    "index_date": "2026-09-03",
    "gfcri_value": 40.01,
    "alert_level": "yellow",
    "si_rates": 20.51,
    "si_fx": 20.15,
    "si_equity": 0.0,
    "si_credit": 6.79,
    "si_sentiment": 12.83,
    "sub_index_details": {
        "SI_FX": {
            "name": "Global FX",
            "score": 20.15,
            "top_driver": "cny_usd",
            "node_scores": {"cny_usd": 0.476},
        }
    },
    "active_chains": [{"id": "fed_cascade"}],
    "chain_details": [{"id": "fed_cascade", "path": ["fed_funds", "ust_10y"]}],
    "coherence_multiplier": 1.2,
    "node_contributions": {"cny_usd": {"zscore": -1.9}},
    "divergence": {"status": "significant"},
    "undercurrent_boost": 25.0,
    "trade_spillover": {
        "score": 19.3,
        "top_links": [{"source": "CN", "target": "KR"}],
    },
    "trade_spillover_boost": 1.08,
}


class DataVisibilityTests(unittest.TestCase):
    def test_anonymous_response_keeps_base_values_and_removes_deep_details(self):
        result = visible_risk_index(SAMPLE, None)

        self.assertEqual(result["gfcri_value"], 40.01)
        self.assertEqual(result["sub_index_details"]["SI_FX"]["score"], 20.15)
        self.assertIsNone(result["node_contributions"])
        self.assertEqual(result["active_chains"], [])
        self.assertIsNone(result["divergence"])
        self.assertEqual(result["trade_spillover"], {"score": 19.3, "top_links": []})

    def test_personal_pro_response_keeps_deep_details(self):
        result = visible_risk_index(
            SAMPLE,
            {"account_type": "personal", "plan": "pro"},
        )

        self.assertEqual(result["node_contributions"], SAMPLE["node_contributions"])
        self.assertEqual(result["chain_details"], SAMPLE["chain_details"])
        self.assertEqual(result["trade_spillover"], SAMPLE["trade_spillover"])


if __name__ == "__main__":
    unittest.main()
