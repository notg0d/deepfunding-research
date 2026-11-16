"""Build an auditable jury-score forecast, without submitting or trading."""
import csv
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "sources"
WEB3J_ALIASES = ("hyperledger-web3j/web3j", "LFDT-web3j/web3j")


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def history_weight(n_jurors):
    """A declared heuristic, not a learned or Bayesian weight."""
    return 0.30 * n_jurors / (n_jurors + 2) if n_jurors else 0.0


def blend(market, evidence, evidence_weight, history=None, n_jurors=0):
    h_weight = history_weight(n_jurors) if history is not None else 0.0
    m_weight = 1.0 - evidence_weight - h_weight
    if min(evidence_weight, h_weight, m_weight) < 0:
        raise ValueError("Negative forecast weight")
    value = m_weight * market + evidence_weight * evidence
    if history is not None:
        value += h_weight * history
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid forecast")
    return value, m_weight, h_weight


def load_metric():
    spec = importlib.util.spec_from_file_location("official_metric", RAW / "dataset" / "metric.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def amount(value):
    numeric, unit = value.split(maxsplit=1)
    numeric = float(numeric)
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError("Invalid chart amount")
    return numeric, unit


def analyze_charts(repos):
    payload = {}
    for path in (RAW / "market").glob("charts_*.json"):
        payload.update(json.loads(path.read_text(encoding="utf-8")))
    details = []
    for repo in repos:
        chart = payload[repo["seer_market"].lower()]
        up_series = next(s for s in chart["series"] if s["outcomeName"].upper() == "UP")
        points = sorted(up_series["points"])
        last_time, last_price = points[-1]
        cutoff = last_time - 7 * 24 * 60 * 60
        anchors = [p for p in points if p[0] <= cutoff]
        anchor = anchors[-1] if anchors else None
        changes = [(b[0], b[1]) for a, b in zip(points, points[1:]) if b[1] != a[1]]
        volume, unit = amount(chart["totalVolumeMarket"])
        liquidity, other_unit = amount(chart["totalLiquidityMarket"])
        if other_unit != unit:
            raise ValueError("Chart units do not match")
        timestamp = lambda x: dt.datetime.fromtimestamp(x, dt.timezone.utc).isoformat()
        details.append({
            "repo": repo["repo"], "chart_end_utc": timestamp(last_time),
            "chart_up_last": last_price,
            "chart_up_7d_change": last_price - anchor[1] if anchor else "",
            "recorded_up_changes_7d": sum(c[0] > cutoff for c in changes),
            "last_recorded_up_price_change_utc": timestamp(changes[-1][0]) if changes else "",
            "last_recorded_up_price_change_size": changes[-1][1] - next(p[1] for p in reversed(points) if p[0] < changes[-1][0]) if changes else "",
            "cumulative_volume_in_repo_collateral": volume,
            "reported_liquidity_in_repo_collateral": liquidity,
            "collateral_symbol": unit,
            "cumulative_volume_to_reported_liquidity": volume / liquidity if liquidity else "",
        })
    return details, len(payload)


def source_record(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    sidecar = path.with_suffix(path.suffix + ".source.json")
    provenance = json.loads(sidecar.read_text(encoding="utf-8"))
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if provenance["sha256"] != observed:
        raise ValueError("Source hash mismatch: " + str(path))
    return {"url": provenance["url"], "fetched_at": provenance["fetched_at"],
            "sha256": observed, "local_path": path.relative_to(ROOT).as_posix()}


def main():
    repos = csv_rows(RAW / "dataset" / "repos.csv")
    names = [r["repo"] for r in repos]
    inputs = csv_rows(ROOT / "evidence_assessments.csv")
    assessments = {r["repo"]: r for r in inputs}
    if len(assessments) != len(inputs) or set(assessments) != set(names):
        raise ValueError("Evidence rows do not exactly match canonical repositories")
    historical = {r["repo"]: r for r in csv_rows(RAW / "dataset" / "public_leaderboard_targets.csv")}
    market_rows = csv_rows(ROOT / "market_analysis.csv")
    markets = {r["repo"]: r for r in market_rows}
    if set(markets) != set(names) or len(markets) != len(market_rows):
        raise ValueError("Market universe mismatch")
    readmes = {r["repo"]: r for r in json.loads((RAW / "repository_index.json").read_text(encoding="utf-8"))}
    alias_market = st.mean(float(markets[n]["up_price"]) for n in WEB3J_ALIASES)
    alias_normalized = st.mean(float(markets[n]["up_share"]) for n in WEB3J_ALIASES)
    if assessments[WEB3J_ALIASES[0]]["evidence_prior"] != assessments[WEB3J_ALIASES[1]]["evidence_prior"]:
        raise ValueError("Web3j aliases have different evidence priors")
    details, records, source_details = [], [], []
    for repo in repos:
        name = repo["repo"]
        e, m = assessments[name], markets[name]
        if repo["seer_market"].lower() != m["market_id"].lower():
            raise ValueError("Wrong market: " + name)
        prior, e_weight = float(e["evidence_prior"]), float(e["evidence_weight"])
        h = historical.get(name)
        history = float(h["originality"]) if h else None
        n_jurors = int(h["n_jurors"]) if h else 0
        raw_market = float(m["up_price"])
        market = alias_market if name in WEB3J_ALIASES else raw_market
        normalized = alias_normalized if name in WEB3J_ALIASES else float(m["up_share"])
        prediction, m_weight, h_weight = blend(market, prior, e_weight, history, n_jurors)
        prediction = round(prediction, 3)
        low, high = float(e["scenario_low"]), float(e["scenario_high"])
        if not 0 <= low <= prediction <= high <= 1:
            raise ValueError("Invalid subjective scenario range: " + name)
        if not e["rationale"].strip():
            raise ValueError("Missing rationale")
        normalized_prediction = blend(normalized, prior, e_weight, history, n_jurors)[0]
        no_history = blend(market, prior, e_weight)[0]
        less_evidence = blend(market, prior, e_weight - 0.10, history, n_jurors)[0]
        more_evidence = blend(market, prior, e_weight + 0.10, history, n_jurors)[0]
        row = {
            "repo": name, "originality": f"{prediction:.3f}",
            "scenario_low_uncalibrated": f"{low:.2f}", "scenario_high_uncalibrated": f"{high:.2f}",
            "category": e["category"], "evidence_prior_subjective": prior, "evidence_weight": e_weight,
            "historical_target": history if history is not None else "", "historical_n_jurors": n_jurors,
            "historical_weight": round(h_weight, 6), "market_up_raw": raw_market,
            "market_anchor_used": market, "market_weight": round(m_weight, 6),
            "market_up_normalized": float(m["up_share"]), "up_plus_down": float(m["price_sum"]),
            "prediction_minus_market_up": round(prediction - raw_market, 6),
            "prediction_if_normalized_market": round(normalized_prediction, 3),
            "prediction_without_history": round(no_history, 3),
            "prediction_with_evidence_weight_minus_010": round(less_evidence, 3),
            "prediction_with_evidence_weight_plus_010": round(more_evidence, 3),
            "rationale": e["rationale"],
        }
        folder = RAW / "repositories" / name.replace("/", "__")
        source_paths = [Path(readmes[name]["path"])]
        source_paths.extend((folder / p).resolve() for p in e["supporting_files"].split(";") if p)
        sources = [source_record(p) for p in dict.fromkeys(source_paths)]
        row["source_urls"] = "; ".join(s["url"] for s in sources)
        details.append(row)
        records.append({"repo": name, "originality": f"{prediction:.3f}"})
        source_details.append({"repo": name, "sources": sources})
    write_csv(ROOT / "submission.csv", records)
    write_csv(ROOT / "forecast_details.csv", details)
    (ROOT / "forecast_sources.json").write_text(json.dumps(source_details, indent=2), encoding="utf-8")
    metric = load_metric()
    universe = metric.load_repos((RAW / "dataset" / "repos.csv").read_bytes())
    predictions = metric.parse_submission((ROOT / "submission.csv").read_bytes(), universe)
    truth = metric.load_solution((RAW / "dataset" / "public_leaderboard_targets.csv").read_bytes(), universe)
    old_prices = {r["repo"]: r for r in csv_rows(RAW / "dataset" / "market_prices.csv")}
    public_targets = truth["public"]
    errors = lambda p: metric.score_split(p, public_targets)
    baselines = {
        "constant_050": errors(dict.fromkeys(names, 0.5)),
        "constant_080": errors(dict.fromkeys(names, 0.8)),
        "october_raw_up": errors({n: float(old_prices[n]["up_price"]) for n in names}),
        "october_normalized_up": errors({n: float(old_prices[n]["up_share"]) for n in names}),
        "live_raw_up": errors({n: float(markets[n]["up_price"]) for n in names}),
        "live_normalized_up": errors({n: float(markets[n]["up_share"]) for n in names}),
        "subjective_evidence_prior": errors({n: float(assessments[n]["evidence_prior"]) for n in names}),
        "recommended_forecast_uses_public_history": errors(predictions),
        "forecast_without_direct_history_but_not_blind": errors({r["repo"]: r["prediction_without_history"] for r in details}),
        "forecast_with_normalized_market_uses_history": errors({r["repo"]: r["prediction_if_normalized_market"] for r in details}),
    }
    chart_details, returned_chart_count = analyze_charts(repos)
    write_csv(ROOT / "market_diagnostics.csv", chart_details)
    errors_per_repo = [{"repo": n, "r1_target": public_targets[n], "forecast": predictions[n],
                        "forecast_abs_error": abs(predictions[n] - public_targets[n]),
                        "raw_market_abs_error": abs(float(markets[n]["up_price"]) - public_targets[n])}
                       for n in public_targets]
    quote_source = source_record(RAW / "market" / "live_markets.json")
    category_stats = {}
    for category in sorted(set(r["category"] for r in details)):
        subset = [r for r in details if r["category"] == category]
        category_stats[category] = {"n": len(subset), "mean_forecast": st.mean(float(r["originality"]) for r in subset),
                                    "mean_market_up": st.mean(r["market_up_raw"] for r in subset)}
    diagnostics = {
        "quote_source": quote_source,
        "submission_rows": len(predictions), "canonical_names_preserved": list(predictions) == names,
        "submission_sha256": hashlib.sha256((ROOT / "submission.csv").read_bytes()).hexdigest(),
        "all_values_finite_and_in_unit_interval": all(math.isfinite(v) and 0 <= v <= 1 for v in predictions.values()),
        "web3j_aliases_identical": predictions[WEB3J_ALIASES[0]] == predictions[WEB3J_ALIASES[1]],
        "mean_prediction": st.mean(predictions.values()), "median_prediction": st.median(predictions.values()),
        "min_prediction": min(predictions.values()), "max_prediction": max(predictions.values()),
        "mean_market_up": st.mean(float(r["up_price"]) for r in market_rows),
        "historical_public_diagnostics_NOT_heldout_validation": baselines,
        "public_repo_absolute_errors": errors_per_repo,
        "category_summary": category_stats,
        "largest_disagreements_with_raw_up": sorted(details, key=lambda r: abs(r["prediction_minus_market_up"]), reverse=True)[:15],
        "normalization_max_forecast_change": max(abs(float(r["originality"]) - r["prediction_if_normalized_market"]) for r in details),
        "evidence_weight_010_max_forecast_change": max(max(abs(float(r["originality"]) - r[k]) for k in ("prediction_with_evidence_weight_minus_010", "prediction_with_evidence_weight_plus_010")) for r in details),
        "normalization_change_over_002": [r["repo"] for r in details if abs(float(r["originality"]) - r["prediction_if_normalized_market"]) > 0.02],
        "leaf_markets_analyzed": len(chart_details), "chart_endpoint_total_records": returned_chart_count,
        "price_sum_below_098": sum(float(r["price_sum"]) < 0.98 for r in market_rows),
        "price_sum_below_095": sum(float(r["price_sum"]) < 0.95 for r in market_rows),
        "largest_chart_7d_moves": sorted(chart_details, key=lambda r: abs(r["chart_up_7d_change"] or 0), reverse=True)[:10],
        "latest_recorded_up_change_timestamp_counts": dict(Counter(r["last_recorded_up_price_change_utc"] for r in chart_details)),
        "max_abs_up_change_at_2026_11_16_0130_utc": max(abs(r["last_recorded_up_price_change_size"]) for r in chart_details if r["last_recorded_up_price_change_utc"] == "2026-11-16T01:30:00+00:00"),
        "chart_7d_up_count": sum(r["chart_up_7d_change"] > 0 for r in chart_details),
        "chart_7d_down_count": sum(r["chart_up_7d_change"] < 0 for r in chart_details),
        "chart_7d_median_change": st.median(r["chart_up_7d_change"] for r in chart_details),
        "limitations": [
            "No Round 3 jury targets exist. Final predictive accuracy is unmeasured.",
            "Public diagnostic scores use published R1 targets. The forecast directly uses some of those targets.",
            "Evidence priors and blending weights are subjective heuristics, not learned or calibrated estimates.",
            "Scenario intervals have no assigned statistical coverage probability.",
            "README claims and selected code/manifests were reviewed; this is not an exhaustive code audit.",
            "Repository collateral-token amounts are not USD. Chart timestamps are not confirmed trade timestamps.",
            "Quotes are marginal pool prices, not guaranteed executable prices or independent crowd estimates.",
        ],
    }
    (ROOT / "forecast_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    lines = [
        "# Repository originality forecasts", "",
        "The forecasts estimate new Round 3 jury averages. Values are independent and do not sum to one.", "",
        "Market quotes were fetched on " + quote_source["fetched_at"] + ".", "",
        "Ranges are subjective scenarios, not calibrated confidence intervals.",
        "Evidence priors and weights are heuristics. See [REPORT.md](REPORT.md) for the method and limitations.", "",
        "## All 98 forecasts", "",
        "| Repository | Forecast | Scenario range | Raw UP quote |", "|---|---:|---:|---:|",
    ]
    lines.extend(f"| {r['repo']} | {r['originality']} | {r['scenario_low_uncalibrated']}–{r['scenario_high_uncalibrated']} | {r['market_up_raw']:.3f} |" for r in details)
    lines.extend(["", "## Evidence and rationale", ""])
    for r, source in zip(details, source_details):
        lines.extend([
            "### " + r["repo"], "",
            f"**Forecast: {r['originality']}.** Subjective scenario range: {r['scenario_low_uncalibrated']}–{r['scenario_high_uncalibrated']}.", "",
            r["rationale"], "",
            f"Evidence prior: {r['evidence_prior_subjective']:.2f}; evidence weight: {r['evidence_weight']:.2f}. "
            f"Market weight: {r['market_weight']:.4f}; historical weight: {r['historical_weight']:.4f}.", "",
            "Sources: " + "; ".join(f"[source {i}]({s['url']})" for i, s in enumerate(source["sources"], 1)) + ".", "",
        ])
    (ROOT / "repository_forecasts.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: diagnostics[k] for k in (
        "submission_rows", "web3j_aliases_identical", "mean_prediction", "median_prediction", "min_prediction", "max_prediction",
        "mean_market_up", "historical_public_diagnostics_NOT_heldout_validation", "normalization_max_forecast_change",
        "evidence_weight_010_max_forecast_change", "price_sum_below_098", "price_sum_below_095")}, indent=2))


if __name__ == "__main__":
    main()
