"""Compare alternatives without changing the original forecast or audit."""

import csv
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "insight_review"
ALIASES = ("hyperledger-web3j/web3j", "LFDT-web3j/web3j")
D = Decimal


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def baseline_hashes():
    baseline = ROOT / "strict_audit/baseline"
    expected = json.loads((baseline / "sha256.json").read_text())
    observed = {name: hashlib.sha256((baseline / name).read_bytes()).hexdigest() for name in expected}
    if observed != expected:
        raise ValueError("An original artifact changed")
    return observed


def shared_anchor(name, markets, fraction=0.0, threshold=None):
    members = ALIASES if name in ALIASES else (name,)
    raw = statistics.mean(float(markets[n]["up_price"]) for n in members)
    normalized = statistics.mean(float(markets[n]["up_share"]) for n in members)
    price_sum = statistics.mean(float(markets[n]["price_sum"]) for n in members)
    active = fraction != 0 and (threshold is None or price_sum < threshold)
    return (raw * (1 - fraction) + normalized * fraction if active else raw), active


def decimal_prediction(name, markets, evidence, targets, fraction, threshold, use_history=True):
    """Independent arithmetic: rebuild normalized prices and derive exact weights."""
    with localcontext() as context:
        context.prec = 60
        members = ALIASES if name in ALIASES else (name,)
        raw = sum(D(markets[n]["up_price"]) for n in members) / len(members)
        normalized = sum(D(markets[n]["up_price"]) /
                         (D(markets[n]["up_price"]) + D(markets[n]["down_price"]))
                         for n in members) / len(members)
        price_sum = sum(D(markets[n]["up_price"]) + D(markets[n]["down_price"])
                        for n in members) / len(members)
        part = D(str(fraction)) if threshold is None or price_sum < D(str(threshold)) else D(0)
        anchor = raw + part * (normalized - raw)
        e = evidence[name]
        ew = D(e["evidence_weight"])
        history = targets.get(name) if use_history else None
        hw = D("0.30") * D(history["n_jurors"]) / (D(history["n_jurors"]) + 2) if history else D(0)
        result = ew * D(e["evidence_prior"]) + (1 - ew - hw) * anchor
        if history:
            result += hw * D(history["originality"])
        return result.quantize(D("0.001"), rounding=ROUND_HALF_EVEN)


def float_prediction(anchor, evidence, target=None, use_history=True):
    ew = float(evidence["evidence_weight"])
    n = int(target["n_jurors"]) if target and use_history else 0
    hw = 0.30 * n / (n + 2) if n else 0.0
    mw = 1 - ew - hw
    if min(ew, hw, mw) < 0:
        raise ValueError("Negative weight")
    value = mw * anchor + ew * float(evidence["evidence_prior"])
    if hw:
        value += hw * float(target["originality"])
    return f"{round(value, 3):.3f}"


def load_metric():
    spec = importlib.util.spec_from_file_location("insight_official_metric", ROOT / "sources/dataset/metric.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_records(records, targets, metric, universe):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=["repo", "originality"])
    writer.writeheader()
    writer.writerows({"repo": r["repo"], "originality": r["originality"]} for r in records)
    parsed = metric.parse_submission(handle.getvalue(), universe)
    exact = sum(abs(D(r["originality"]) - D(targets[r["repo"]]["originality"]))
                for r in records if r["repo"] in targets)
    official = metric.score_split(parsed, {n: float(t["originality"]) for n, t in targets.items()})
    if abs(official - float(exact)) > 1e-12:
        raise ValueError("Independent SAE differs from official metric")
    return exact, official


def alias_counterexample():
    """The proposed per-row branch can break the original alias invariant."""
    markets = {
        ALIASES[0]: {"up_price": "0.64", "down_price": "0.16", "up_share": "0.8", "price_sum": "0.8"},
        ALIASES[1]: {"up_price": "0.8", "down_price": "0.2", "up_share": "0.8", "price_sum": "1.0"},
    }
    raw, _ = shared_anchor(ALIASES[0], markets)
    normalized, _ = shared_anchor(ALIASES[0], markets, 1.0)
    proposed = [0.5 * (raw + normalized) if float(markets[n]["price_sum"]) < 0.98 else raw for n in ALIASES]
    corrected = [shared_anchor(n, markets, 0.5, 0.98)[0] for n in ALIASES]
    if proposed[0] == proposed[1] or corrected[0] != corrected[1]:
        raise ValueError("Alias regression counterexample failed")
    return {"synthetic_not_current_quotes": True, "price_sums": [0.8, 1.0],
            "proposed_per_row_anchors": proposed, "shared_branch_anchors": corrected,
            "shared_threshold_policy": "Use the mean price_sum for both aliases; heuristic, not uniquely optimal."}


def main():
    before = baseline_hashes()
    names = [r["repo"] for r in rows(ROOT / "sources/dataset/repos.csv")]
    original = {r["repo"]: r["originality"] for r in rows(ROOT / "strict_audit/baseline/submission.csv")}
    old_details = {r["repo"]: r for r in rows(ROOT / "strict_audit/baseline/forecast_details.csv")}
    markets = {r["repo"]: r for r in rows(ROOT / "strict_audit/baseline/market_analysis.csv")}
    evidence = {r["repo"]: r for r in rows(ROOT / "strict_audit/baseline/evidence_assessments.csv")}
    targets = {r["repo"]: r for r in rows(ROOT / "sources/dataset/public_leaderboard_targets.csv")}
    if len(names) != 98 or set(names) != set(markets) or set(names) != set(evidence):
        raise ValueError("Universe mismatch")
    for m in markets.values():
        up, down = float(m["up_price"]), float(m["down_price"])
        if abs(up + down - float(m["price_sum"])) > 2e-15 or abs(up / (up + down) - float(m["up_share"])) > 2e-15:
            raise ValueError("Market arithmetic mismatch")
    metric = load_metric()
    universe = metric.load_repos((ROOT / "sources/dataset/repos.csv").read_bytes())
    plans = [("original_raw", 0.0, None), ("normalized_all", 1.0, None), ("midpoint_all", 0.5, None)]
    plans += [(f"midpoint_below_{str(t).replace('.', '')}", 0.5, t) for t in [0.85, 0.90, 0.95, 0.98, 1.0, 1.02]]
    plans.append(("normalized_below_098", 1.0, 0.98))
    detailed, summaries, scores = [], [], {}
    for scenario, fraction, threshold in plans:
        for use_history in [True, False]:
            label = scenario + ("" if use_history else "_without_history")
            records = []
            for name in names:
                anchor, active = shared_anchor(name, markets, fraction, threshold)
                prediction = float_prediction(anchor, evidence[name], targets.get(name), use_history)
                independent = decimal_prediction(name, markets, evidence, targets, fraction, threshold, use_history)
                if D(prediction) != independent:
                    raise ValueError(f"Decimal mismatch: {label} {name}")
                if scenario == "original_raw":
                    expected = original[name] if use_history else old_details[name]["prediction_without_history"]
                    if D(prediction) != D(expected):
                        raise ValueError("Original reproduction failed: " + name)
                row = {"scenario": label, "repo": name, "originality": prediction,
                       "original_forecast": original[name], "change_from_original": str(D(prediction) - D(original[name])),
                       "market_anchor_used": repr(anchor), "normalization_branch_active": active,
                       "normalization_fraction": fraction, "price_sum_threshold": threshold if threshold is not None else "",
                       "uses_public_history": use_history, "has_public_label": name in targets}
                records.append(row)
            if records[names.index(ALIASES[0])]["originality"] != records[names.index(ALIASES[1])]["originality"]:
                raise ValueError("Alias forecasts differ")
            exact, official = score_records(records, targets, metric, universe)
            summary = {"scenario": label, "rows": len(records), "active_branch_rows": sum(r["normalization_branch_active"] for r in records),
                       "changed_rows_vs_original": sum(D(r["originality"]) != D(r["original_forecast"]) for r in records),
                       "public_sae_decimal": str(exact), "public_sae_official": official,
                       "maximum_abs_change_vs_original": str(max(abs(D(r["change_from_original"])) for r in records))}
            summaries.append(summary)
            scores[label] = records
            detailed.extend(records)
    baseline_sae = D(summaries[0]["public_sae_decimal"])
    for summary in summaries:
        summary["public_sae_change_vs_original"] = str(D(summary["public_sae_decimal"]) - baseline_sae)
    deficits = []
    for name in names:
        m, e = markets[name], evidence[name]
        if float(m["price_sum"]) >= 0.98:
            continue
        raw, _ = shared_anchor(name, markets)
        norm, _ = shared_anchor(name, markets, 1.0)
        candidate = scores["midpoint_below_098"][names.index(name)]
        deficits.append({"repo": name, "price_sum": m["price_sum"], "evidence_prior": e["evidence_prior"],
                         "raw_up": m["up_price"], "normalized_up": repr(norm),
                         "normalized_closer_to_prior": abs(norm - float(e["evidence_prior"])) < abs(raw - float(e["evidence_prior"])),
                         "original": original[name], "midpoint": candidate["originality"],
                         "change": candidate["change_from_original"], "public_target": targets.get(name, {}).get("originality", "")})
    prior_rows = []
    for name, proposed in [("ethereum-lists/chains", ["0.55", "0.60", "0.65"]),
                           ("succinctlabs/sp1", ["0.76", "0.77", "0.78"])]:
        for prior in proposed:
            revised = {n: dict(e) for n, e in evidence.items()}
            revised[name]["evidence_prior"] = prior
            anchor, _ = shared_anchor(name, markets)
            predicted = float_prediction(anchor, revised[name], targets.get(name))
            independent = decimal_prediction(name, markets, revised, targets, 0.0, None)
            if D(predicted) != independent:
                raise ValueError("Prior-sweep arithmetic mismatch")
            prior_rows.append({"repo": name, "original_prior": evidence[name]["evidence_prior"], "scenario_prior_not_adopted": prior,
                               "original_forecast": original[name], "scenario_forecast": predicted,
                               "change": str(D(predicted) - D(original[name])), "public_label_exists": name in targets})
    citation_hashes = {}
    for sidecar in (OUT / "sources").rglob("*.source.json"):
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        source = Path(str(sidecar).removesuffix(".source.json"))
        observed = hashlib.sha256(source.read_bytes()).hexdigest()
        if observed != metadata["sha256"]:
            raise ValueError("New source hash mismatch: " + str(source))
        citation_hashes[source.relative_to(ROOT).as_posix()] = observed
    after = baseline_hashes()
    if before != after:
        raise ValueError("Original artifacts changed during review")
    results = {"snapshot": "Original quotes, 2026-11-16 11:10:32 UTC; no quote replacement.",
               "not_held_out_validation": True, "scenario_count_including_history_free": len(summaries),
               "decimal_forecast_checks": len(detailed) + len(prior_rows), "scenarios": summaries,
               "deficit_count_below_098": len(deficits),
               "deficit_normalized_closer_to_subjective_prior": sum(r["normalized_closer_to_prior"] for r in deficits),
               "publicly_labelled_deficits": [r["repo"] for r in deficits if r["public_target"]],
               "alias_counterexample": alias_counterexample(), "unchanged_original_artifact_hashes": after,
               "new_source_hashes": citation_hashes,
               "limitations": ["No Round 3 labels exist.", "Public history enters the original blend and all scenarios marked uses_public_history.",
                               "Priors and all thresholds/fractions are subjective and uncalibrated.",
                               "Normalized prices use the same pools; they are not independent evidence.",
                               "The history-free scenarios are not blind forecasts."]}
    OUT.mkdir(exist_ok=True)
    write_csv(OUT / "scenario_forecasts.csv", detailed)
    write_csv(OUT / "scenario_summary.csv", summaries)
    write_csv(OUT / "deficit_markets.csv", deficits)
    write_csv(OUT / "prior_scenarios.csv", prior_rows)
    (OUT / "scenario_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({k: results[k] for k in ["scenario_count_including_history_free", "decimal_forecast_checks", "deficit_count_below_098",
                                             "deficit_normalized_closer_to_subjective_prior", "publicly_labelled_deficits"]}, indent=2))
    for summary in summaries:
        print(summary["scenario"], summary["active_branch_rows"], summary["public_sae_decimal"])


if __name__ == "__main__":
    main()
