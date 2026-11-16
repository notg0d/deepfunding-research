"""Inspect market metadata and bounded chart summaries."""
import json
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = Path(__file__).resolve().parent / "sources" / "market"
live = json.loads((root / "live_markets.json").read_text(encoding="utf-8"))
for key, value in live.items():
    if key == "marketsData":
        continue
    print("KEY", key, "TYPE", type(value).__name__)
    print(json.dumps(value, ensure_ascii=False)[:10000])
charts = {}
for path in root.glob("charts_*.json"):
    charts.update(json.loads(path.read_text(encoding="utf-8")))
print("CHART METADATA")
for name in ("ethereum/js-ethereum-cryptography", "aestus-relay/mev-boost-relay", "supranational/blst", "ChainSafe/bls", "wevm/viem"):
    market = next(v for k,v in live["marketsData"].items() if k.lower() == name.lower())
    data = charts.get(market["id"].lower(), {})
    compact = {k:v for k,v in data.items() if k != "series"}
    compact["series"] = [{k:v for k,v in s.items() if k != "points"} | {"points_count": len(s.get("points", [])), "first": s.get("points", [])[:1], "last": s.get("points", [])[-1:]} for s in data.get("series", [])]
    print(name, json.dumps(compact, ensure_ascii=False))
text = next(root.glob("index-*.js")).read_text(encoding="utf-8")
print("DATA FUNCTIONS", sorted(set(re.findall(r'Dc\("([^\"]+)"', text))))
for term in ("parentMarketId:Ame", "Ame=", "Sme=", "collateralUnitPrice", "jury", "juror", "resolve", "average originality", "incorrect", "upPrice"):
    matches = list(re.finditer(re.escape(term), text, re.I))
    print("TERM", term, "COUNT", len(matches))
    for m in matches[-3:]:
        print(text[max(0,m.start()-160):m.end()+500])
