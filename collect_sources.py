"""Collect public competition data and repository documentation. No trading or authentication."""

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "sources"
RAW.mkdir(exist_ok=True)
BASE = "https://huggingface.co/datasets/DeepFunding/originality-r3-data/raw/main/"


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "Public-originality-research/1.0"})
    record = {"url": url, "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read()
            record.update(status=response.status, final_url=response.url,
                          sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        target.with_suffix(target.suffix + ".source.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record
    except (urllib.error.URLError, TimeoutError) as error:
        record.update(status=getattr(error, "code", None), error=str(error))
        return record


def collect_dataset():
    names = ["README.md", "repos.csv", "sample_submission.csv", "r1_juror_ratings.csv",
             "public_leaderboard_targets.csv", "market_prices.csv", "metric.py", "LICENSE"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda name: download(BASE + name, RAW / "dataset" / name), names))
    site = download("https://deep.seer.pm", RAW / "market" / "index.html")
    if site.get("status") == 200:
        html = (RAW / "market" / "index.html").read_text(encoding="utf-8")
        for asset in re.findall(r'src="([^\"]+\.js)"', html):
            results.append(download("https://deep.seer.pm" + asset, RAW / "market" / Path(asset).name))
    print(json.dumps(results, indent=2))


def collect_readme(repo):
    name = repo["repo"]
    folder = RAW / "repositories" / name.replace("/", "__")
    attempts = []
    for filename in ("README.md", "README.rst", "README", "readme.md", "Readme.md"):
        result = download(f"https://raw.githubusercontent.com/{name}/HEAD/{filename}", folder / filename)
        attempts.append(result)
        if result.get("status") == 200:
            return {"repo": name, "source": result, "path": str(folder / filename)}
        if result.get("status") in (403, 429):
            break
    return {"repo": name, "attempts": attempts, "missing": True}


def collect_readmes():
    with (RAW / "dataset" / "repos.csv").open(encoding="utf-8-sig", newline="") as handle:
        repos = list(csv.DictReader(handle))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(collect_readme, repos))
    (RAW / "repository_index.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"collected": sum(not r.get("missing") for r in results),
                      "missing": [r["repo"] for r in results if r.get("missing")]}, indent=2))


def collect_markets():
    prefix = "https://deep.seer.pm/.netlify/functions/"
    result = download(prefix + "get-originality-r3-v3-markets-data", RAW / "market" / "live_markets.json")
    print(json.dumps(result, indent=2))
    with (RAW / "dataset" / "repos.csv").open(encoding="utf-8-sig", newline="") as handle:
        repos = list(csv.DictReader(handle))
    batches = [repos[i:i+40] for i in range(0, len(repos), 40)]
    def charts(batch):
        ids = ",".join(r["seer_market"] for r in batch)
        return download(prefix + "get-market-charts?ids=" + ids,
                        RAW / "market" / ("charts_" + batch[0]["bundle"] + "_" + batch[0]["repo"].replace("/", "__") + ".json"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(charts, batches)), indent=2))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dataset"
    if mode == "dataset":
        collect_dataset()
    elif mode == "readmes":
        collect_readmes()
    elif mode == "markets":
        collect_markets()
    else:
        raise SystemExit("Use dataset, readmes, or markets")
