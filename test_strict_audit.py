"""Test offline audit results and rejection of malformed market evidence."""
import copy
import unittest

from strict_audit import AUDIT, ROOT, audit, csv_rows, load_json, validate_market_snapshot


class StrictAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results, cls.matrix = audit()
        cls.checks = {r["id"]: r for r in cls.results["checks"]}
        cls.universe = csv_rows(ROOT / "sources/dataset/repos.csv")
        cls.payload = load_json(ROOT / "sources/market/live_markets.json")

    def detail(self, name):
        return self.checks[name]["detail"]

    def test_all_technical_checks_pass(self):
        self.assertEqual(len(self.checks), 16)
        self.assertTrue(all(r["status"] == "PASS" for r in self.checks.values()), self.checks)

    def test_original_artifacts_are_preserved(self):
        self.assertEqual(self.detail("original_artifacts_preserved")["preserved_artifacts"], 11)
        self.assertEqual(self.results["numerical_revisions"], 0)

    def test_upstream_records_and_official_rounding(self):
        result = self.detail("upstream_historical_labels")
        self.assertEqual((result["ratings"], result["repositories"], result["single_rating_repositories"]), (51, 33, 23))
        self.assertTrue(result["ratings_and_notes_match_upstream"])
        self.assertEqual(result["target_file_precision_decimals"], 6)
        self.assertLess(result["max_mean_rounding_difference"], 0.0000005)

    def test_independent_blend_and_sensitivity_coverage(self):
        self.assertEqual(self.detail("independent_blend_and_sensitivities")["rounded_values_checked"], 490)

    def test_independent_and_official_sae_match(self):
        result = self.detail("independent_sae")
        self.assertAlmostEqual(result["official_submission_sae"], 2.277, places=12)
        self.assertAlmostEqual(result["independent_sae"]["recommended_forecast_uses_public_history"], 2.277, places=12)

    def test_forecast_is_not_certified_or_held_out(self):
        self.assertFalse(self.results["forecast_certified_as_accurate"])
        self.assertFalse(self.detail("independent_sae")["held_out"])
        self.assertFalse(self.detail("independent_sae")["future_accuracy_validated"])

    def test_matrix_has_exact_official_order(self):
        self.assertEqual([r["repo"] for r in self.matrix], [r["repo"] for r in self.universe])
        self.assertEqual(len({r["repo"] for r in self.matrix}), 98)

    def test_corroboration_is_not_numerical_validation(self):
        self.assertEqual(self.results["coverage"]["rows_with_limited_independent_corroboration"], 23)
        self.assertTrue(all(r["exact_originality_percentage_validated"] == "no" for r in self.matrix))
        self.assertTrue(all(r["future_predictive_accuracy_validated"] == "no" for r in self.matrix))

    def test_both_market_snapshots_have_all_quotes(self):
        for name in ["original_market_token_orientation", "fresh_market_token_orientation"]:
            self.assertEqual(self.detail(name)["quotes_checked"], 196)
            self.assertLess(self.detail(name)["max_absolute_tick_price_error"], 0.0000000002)

    def test_wrong_market_address_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        first = self.universe[0]["repo"]
        payload["marketsData"][first]["id"] = "0x0000000000000000000000000000000000000000"
        with self.assertRaisesRegex(ValueError, "Market address mismatch"):
            validate_market_snapshot(payload, self.universe)

    def test_wrong_outcome_token_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        first = self.universe[0]["repo"]
        payload["marketsData"][first]["upPool"]["token0"] = "0x0000000000000000000000000000000000000000"
        with self.assertRaisesRegex(ValueError, "Wrong pool token pair"):
            validate_market_snapshot(payload, self.universe)

    def test_price_tampering_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        first = self.universe[0]["repo"]
        quote = payload["marketsData"][first]
        quote["upPrice"] += 0.01
        quote["upPool"]["price"] = quote["upPrice"]
        with self.assertRaisesRegex(ValueError, "Tick-derived quote mismatch"):
            validate_market_snapshot(payload, self.universe)

    def test_published_artifacts_are_checked_without_execution(self):
        result = self.detail("published_artifact_integrity")
        self.assertEqual(result["tarballs"], 7)
        self.assertEqual(result["selected_files_checked"], 20)
        self.assertTrue(result["sha1_and_sri_match"])
        self.assertFalse(result["package_code_executed"])

    def test_http_200_html_is_not_counted_as_reviewed_pdf(self):
        result = self.detail("source_content_exceptions_identified")
        self.assertEqual(result["valid_pdf_reports"], 2)
        self.assertIn("HTML", result["excluded"])
        self.assertFalse((AUDIT / "sources/blst_ncc.pdf").read_bytes().startswith(b"%PDF-"))

    def test_high_priority_scope_conflicts_are_explicit(self):
        matrix = {r["repo"]: r for r in self.matrix}
        for name in ["dappnode/DAppNode", "evmts/tevm-monorepo", "libp2p/libp2p", "TrueBlocks/trueblocks-core", "wighawag/hardhat-deploy", "aestus-relay/mev-boost-relay"]:
            self.assertEqual(matrix[name]["scope_or_conflict_flag"], "yes")
            self.assertIn("scope_review_required", matrix[name]["audit_action"])

    def test_history_free_blend_does_not_claim_improvement(self):
        scores = self.detail("independent_sae")["independent_sae"]
        self.assertGreater(scores["forecast_without_direct_history_but_not_blind"], scores["live_raw_up"])


if __name__ == "__main__":
    unittest.main()
