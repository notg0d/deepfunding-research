"""Offline regression tests for the separate scenario review."""

from collections import defaultdict
from decimal import Decimal
import json
import unittest

from review_insight_scenarios import ROOT, OUT, ALIASES, alias_counterexample, baseline_hashes, rows, shared_anchor


class InsightReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = json.loads((OUT / "scenario_results.json").read_text(encoding="utf-8"))
        cls.by_scenario = defaultdict(dict)
        for row in rows(OUT / "scenario_forecasts.csv"):
            cls.by_scenario[row["scenario"]][row["repo"]] = row

    def test_original_artifacts_unchanged(self):
        self.assertEqual(baseline_hashes(), self.results["unchanged_original_artifact_hashes"])

    def test_every_scenario_has_98_canonical_rows(self):
        names = [r["repo"] for r in rows(ROOT / "sources/dataset/repos.csv")]
        for scenario in self.by_scenario.values():
            self.assertEqual(list(scenario), names)
            self.assertTrue(all(Decimal(0) <= Decimal(r["originality"]) <= Decimal(1) for r in scenario.values()))

    def test_reproduces_original_submission(self):
        actual = self.by_scenario["original_raw"]
        for row in rows(ROOT / "strict_audit/baseline/submission.csv"):
            self.assertEqual(actual[row["repo"]]["originality"], row["originality"])

    def test_corrects_two_supplied_midpoint_numbers(self):
        actual = self.by_scenario["midpoint_below_098"]
        expected = {"alloy-rs/alloy": "0.835", "argotorg/fe": "0.794", "arkworks-rs/algebra": "0.854",
                    "Cyfrin/aderyn": "0.683", "l2beat/l2beat": "0.758", "safe-global/safe-smart-account": "0.838"}
        for name, value in expected.items():
            self.assertEqual(actual[name]["originality"], value)

    def test_only_blockscout_has_label_among_deficits(self):
        deficits = rows(OUT / "deficit_markets.csv")
        self.assertEqual(len(deficits), 13)
        self.assertEqual([r["repo"] for r in deficits if r["public_target"]], ["blockscout/blockscout"])
        self.assertEqual(sum(r["normalized_closer_to_prior"] == "True" for r in deficits), 9)
        self.assertEqual(next(r for r in deficits if r["repo"] == "Cyfrin/aderyn")["normalized_closer_to_prior"], "False")

    def test_public_sae_is_independent_and_worsens_by_0005(self):
        summaries = {r["scenario"]: r for r in self.results["scenarios"]}
        self.assertEqual(Decimal(summaries["original_raw"]["public_sae_decimal"]), Decimal("2.277000"))
        self.assertEqual(Decimal(summaries["midpoint_below_098"]["public_sae_decimal"]), Decimal("2.282000"))
        self.assertEqual(Decimal(summaries["midpoint_below_098"]["public_sae_change_vs_original"]), Decimal("0.005000"))
        for summary in summaries.values():
            self.assertAlmostEqual(float(summary["public_sae_decimal"]), summary["public_sae_official"], places=12)

    def test_aliases_remain_identical(self):
        for scenario in self.by_scenario.values():
            self.assertEqual(scenario[ALIASES[0]]["originality"], scenario[ALIASES[1]]["originality"])

    def test_proposed_alias_branch_fails_synthetic_case(self):
        result = alias_counterexample()
        self.assertNotEqual(*result["proposed_per_row_anchors"])
        self.assertEqual(*result["shared_branch_anchors"])

    def test_threshold_is_strict(self):
        markets = {"example/repo": {"up_price": "0.7", "up_share": "0.7142857142857143", "price_sum": "0.98"}}
        anchor, active = shared_anchor("example/repo", markets, 0.5, 0.98)
        self.assertEqual(anchor, 0.7)
        self.assertFalse(active)

    def test_actual_market_metadata_has_invalid_and_scalar_bounds(self):
        canonical = {r["repo"]: r["seer_market"].lower() for r in rows(ROOT / "sources/dataset/repos.csv")}
        for name in ["alloy-rs/alloy", "arkworks-rs/algebra"]:
            market = json.loads((OUT / "sources/seer/market_metadata" / (name.replace("/", "__") + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(market["id"].lower(), canonical[name])
            self.assertEqual(market["outcomes"], ["DOWN", "UP", "Invalid"])
            self.assertEqual(market["templateId"], "1")
            self.assertEqual(market["lowerBound"], "0")
            self.assertEqual(market["upperBound"], "100000000000000000000")
            self.assertEqual(len(market["wrappedTokens"]), 3)
            self.assertEqual(market["poolBalance"][2], None)


if __name__ == "__main__":
    unittest.main()
