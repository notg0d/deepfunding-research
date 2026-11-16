"""Local validation tests. These tests do not measure future forecast accuracy."""
import csv
import hashlib
import io
import json
import math
import unittest

from build_forecast import ROOT, RAW, WEB3J_ALIASES, blend, csv_rows, history_weight, load_metric


class ForecastValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metric = load_metric()
        cls.universe = cls.metric.load_repos((RAW / "dataset" / "repos.csv").read_bytes())
        cls.predictions = cls.metric.parse_submission((ROOT / "submission.csv").read_bytes(), cls.universe)
        cls.details = csv_rows(ROOT / "forecast_details.csv")

    def test_exact_canonical_universe_and_header(self):
        rows = list(csv.reader(io.StringIO((ROOT / "submission.csv").read_text(encoding="utf-8"))))
        self.assertEqual(rows[0], ["repo", "originality"])
        self.assertEqual(len(rows) - 1, 98)
        self.assertEqual([r[0] for r in rows[1:]], list(self.universe.values()))

    def test_unit_interval_and_scenario_ranges(self):
        for r in self.details:
            value = float(r["originality"])
            self.assertTrue(math.isfinite(value) and 0 <= value <= 1)
            self.assertLessEqual(float(r["scenario_low_uncalibrated"]), value)
            self.assertGreaterEqual(float(r["scenario_high_uncalibrated"]), value)

    def test_aliases_identical(self):
        self.assertEqual(self.predictions[WEB3J_ALIASES[0]], self.predictions[WEB3J_ALIASES[1]])

    def test_weights_and_reproducible_formula(self):
        for r in self.details:
            n = int(r["historical_n_jurors"])
            h = float(r["historical_target"]) if n else None
            value, m_weight, h_weight = blend(float(r["market_anchor_used"]),
                                             float(r["evidence_prior_subjective"]),
                                             float(r["evidence_weight"]), h, n)
            self.assertEqual(round(value, 3), float(r["originality"]))
            self.assertAlmostEqual(m_weight + h_weight + float(r["evidence_weight"]), 1)

    def test_history_weights_and_no_history(self):
        self.assertEqual(history_weight(0), 0)
        self.assertAlmostEqual(history_weight(1), 0.1)
        self.assertAlmostEqual(history_weight(6), 0.225)
        self.assertEqual(blend(0.8, 0.6, 0.5), (0.7, 0.5, 0.0))

    def test_official_parser_rejects_invalid_values_and_missing_rows(self):
        body = (ROOT / "submission.csv").read_text(encoding="utf-8")
        for bad in ("nan", "inf", "1.1", "-0.1"):
            with self.assertRaises(self.metric.SubmissionError):
                self.metric.parse_submission(body.replace(",0.764", "," + bad, 1), self.universe)
        with self.assertRaises(self.metric.SubmissionError):
            self.metric.parse_submission("\n".join(body.splitlines()[:-1]), self.universe)

    def test_historical_targets_match_ratings(self):
        ratings = {}
        for r in csv_rows(RAW / "dataset" / "r1_juror_ratings.csv"):
            ratings.setdefault(r["repo"], []).append(float(r["originality"]) / 100)
        for r in csv_rows(RAW / "dataset" / "public_leaderboard_targets.csv"):
            values = ratings[r["repo"]]
            self.assertEqual(len(values), int(r["n_jurors"]))
            self.assertAlmostEqual(sum(values) / len(values), float(r["originality"]), delta=0.00000051)

    def test_all_cited_source_hashes(self):
        source_rows = json.loads((ROOT / "forecast_sources.json").read_text(encoding="utf-8"))
        self.assertEqual(len(source_rows), 98)
        for r in source_rows:
            self.assertTrue(r["sources"])
            for s in r["sources"]:
                self.assertEqual(hashlib.sha256((ROOT / s["local_path"]).read_bytes()).hexdigest(), s["sha256"])
                self.assertTrue(s["url"].startswith("https://"))

    def test_only_leaf_markets_and_matching_units(self):
        rows = csv_rows(ROOT / "market_diagnostics.csv")
        self.assertEqual(len(rows), 98)
        self.assertEqual({r["repo"] for r in rows}, set(self.universe.values()))
        for r in rows:
            self.assertTrue(r["collateral_symbol"].endswith("_R3C"))


if __name__ == "__main__":
    unittest.main()
