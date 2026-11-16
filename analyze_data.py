"""Audit labels, compare market snapshots, and summarize public chart data."""
import csv
import datetime as dt
import json
from pathlib import Path
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "sources"


def rows(name):
    with (RAW / "dataset" / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


repos = rows("repos.csv")
historical = {r["repo"].lower(): r for r in rows("public_leaderboard_targets.csv")}
old = {r["repo"].lower(): r for r in rows("market_prices.csv")}
live_payload = json.loads((RAW / "market" / "live_markets.json").read_text(encoding="utf-8"))
print("LIVE TOP LEVEL", list(live_payload))
live = {k.lower(): v for k, v in live_payload["marketsData"].items()}
charts = {}
for path in (RAW / "market").glob("charts_*.json"):
    charts.update(json.loads(path.read_text(encoding="utf-8")))
print("CHARTS COUNT", len(charts))
first = next(iter(charts.values()))
print("CHART EXAMPLE", json.dumps(first, ensure_ascii=False)[:2800])
missing = [r["repo"] for r in repos if r["repo"].lower() not in live]
mismatch = [r["repo"] for r in repos if live.get(r["repo"].lower(), {}).get("id", "").lower() != r["seer_market"].lower()]
records = []
for r in repos:
    name = r["repo"].lower()
    market = live[name]
    up, down = market["upPrice"], market["downPrice"]
    chart = charts.get(r["seer_market"].lower(), {})
    series = chart.get("series", [])
    last = max((p[0] for s in series for p in s.get("points", [])), default=None)
    record = dict(repo=r["repo"], market_id=r["seer_market"], up_price=up, down_price=down,
                  up_share=up/(up+down), price_sum=up+down,
                  up_change=up-float(old[name]["up_price"]),
                  normalized_change=up/(up+down)-float(old[name]["up_share"]),
                  historical_target=historical.get(name, {}).get("originality", ""),
                  n_jurors=historical.get(name, {}).get("n_jurors", ""),
                  volume_market=chart.get("totalVolumeMarket", ""),
                  liquidity_market=chart.get("totalLiquidityMarket", ""),
                  last_chart_time=dt.datetime.fromtimestamp(last, dt.timezone.utc).isoformat() if last else "",
                  chart_points=sum(len(s.get("points", [])) for s in series))
    records.append(record)
with (ROOT / "market_analysis.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
targets = [float(r["originality"]) for r in historical.values()]
sae = lambda key: sum(abs(record[key]-float(record["historical_target"])) for record in records if record["historical_target"] != "")
ratings_by_repo = {}
for r in rows("r1_juror_ratings.csv"):
    ratings_by_repo.setdefault(r["repo"], []).append(float(r["originality"])/100)
stats = {"repos": len(repos), "market_repos": len(live), "missing": missing, "id_mismatches": mismatch,
         "historical_repos": len(historical), "single_juror": sum(int(r["n_jurors"]) == 1 for r in historical.values()),
         "target_mean": st.mean(targets), "target_median": st.median(targets),
         "live_raw_public_sae": sae("up_price"), "live_normalized_public_sae": sae("up_share"),
         "price_sum_min": min(r["price_sum"] for r in records), "price_sum_max": max(r["price_sum"] for r in records),
         "largest_movements": sorted(records, key=lambda r: abs(r["up_change"]), reverse=True)[:12],
         "juror_disagreement": sorted([{"repo": k, "ratings": v, "range": max(v)-min(v)} for k,v in ratings_by_repo.items() if len(v)>1], key=lambda r:r["range"], reverse=True)}
(ROOT / "dataset_analysis.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
print(json.dumps(stats, indent=2, ensure_ascii=False))
