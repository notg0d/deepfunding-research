"""Save read-only evidence for the separate AI-insight review."""

from concurrent.futures import ThreadPoolExecutor
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

from collect_sources import download

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "insight_review"
SOURCES = OUT / "sources"


def save_batch(items, index_name):
    def fetch(item):
        name, url = item
        target = SOURCES / name
        record = download(url, target)
        return {"local_path": target.relative_to(ROOT).as_posix(), **record}

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, items))
    OUT.mkdir(exist_ok=True)
    (OUT / index_name).write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"index": index_name, "saved": sum(r.get("status") == 200 for r in records),
                      "failed": [r for r in records if r.get("status") != 200]}, indent=2))
    return records


def main():
    docs = [
        ("seer/llms.txt", "https://docs.seer.pm/llms.txt"),
        ("seer/resolve.md", "https://docs.seer.pm/developers/guides/resolve-a-market.md"),
        ("seer/split_merge_redeem.md", "https://docs.seer.pm/developers/guides/split-merge-and-redeem.md"),
        ("seer/conditional_markets.md", "https://docs.seer.pm/developers/guides/conditional-markets.md"),
        ("seer/trading.md", "https://docs.seer.pm/developers/guides/trading.md"),
        ("seer/realityproxy.md", "https://docs.seer.pm/developers/contracts/core/realityproxy.md"),
        ("seer/ConditionalTokens.sol", "https://raw.githubusercontent.com/gnosis/conditional-tokens-contracts/master/contracts/ConditionalTokens.sol"),
        ("seer/api.md", "https://docs.seer.pm/developers/api.md"),
        ("registry/eip155.html", "https://eips.ethereum.org/EIPS/eip-155"),
        ("registry/caip2_eip155.html", "https://namespaces.chainagnostic.org/eip155/caip2"),
        ("sp1/introduction.html", "https://docs.succinct.xyz/docs/sp1/introduction"),
        ("sp1/hypercube.html", "https://docs.succinct.xyz/docs/sp1/hypercube/"),
        ("sp1/precompiles.html", "https://docs.succinct.xyz/docs/sp1/optimizing-programs/precompiles"),
        ("seer/head.json", "https://api.github.com/repos/seer-pm/demo/commits/main"),
        ("registry/head.json", "https://api.github.com/repos/ethereum-lists/chains/commits/master"),
        ("libp2p/concepts.html", "https://docs.libp2p.io/concepts/introduction/overview/"),
    ]
    save_batch(docs, "source_index.json")
    collect_trees()
    collect_selected()
    collect_market_metadata()


def collect_trees():
    sp1_head = json.loads((ROOT / "strict_audit/sources/heads/succinctlabs__sp1.json").read_text(encoding="utf-8"))[0]["sha"]
    items = [("sp1/tree.json", f"https://api.github.com/repos/succinctlabs/sp1/git/trees/{sp1_head}?recursive=1")]
    for folder, repo in [("seer", "seer-pm/demo"), ("registry", "ethereum-lists/chains")]:
        head = json.loads((SOURCES / folder / "head.json").read_text(encoding="utf-8"))["sha"]
        items.append((f"{folder}/tree.json", f"https://api.github.com/repos/{repo}/git/trees/{head}?recursive=1"))
    save_batch(items, "tree_index.json")


def collect_selected():
    items = []
    for folder, repo, paths in [
        ("seer", "seer-pm/demo", ["contracts/src/RealityProxy.sol", "contracts/src/MarketFactory.sol",
                                  "web/src/lib/deepfundMarkets.generated.ts"]),
        ("registry", "ethereum-lists/chains", ["processor/src/main/kotlin/org/ethereum/lists/chains/Main.kt",
                                                "processor/src/test/kotlin/org/ethereum/lists/chains/TheChainChecker.kt",
                                                "model/src/main/kotlin/org/ethereum/lists/chains/model/Chain.kt"]),
        ("sp1", "succinctlabs/sp1", ["crates/core/machine/Cargo.toml", "crates/prover/Cargo.toml",
                                     "crates/core/machine/src/syscall/precompiles/README.md",
                                     "crates/core/machine/src/syscall/precompiles/sha256/compress/air.rs",
                                     "crates/hypercube/src/lib.rs", "slop/README.md", "slop/crates/algebra/Cargo.toml"]),
        ("aestus", "aestus-relay/mev-boost-relay", ["mevcommitclient/mev_commit_client.go",
                                                   "services/api/latency.go", "datastore/topbid.lua"]),
    ]:
        if folder == "sp1":
            sha = json.loads((ROOT / "strict_audit/sources/heads/succinctlabs__sp1.json").read_text(encoding="utf-8"))[0]["sha"]
        elif folder == "aestus":
            sha = json.loads((ROOT / "sources/repositories/aestus-relay__mev-boost-relay/fork_comparison.json").read_text(encoding="utf-8"))["commits"][-1]["sha"]
        else:
            sha = json.loads((SOURCES / folder / "head.json").read_text(encoding="utf-8"))["sha"]
        items.extend((f"{folder}/code/{path}", f"https://raw.githubusercontent.com/{repo}/{sha}/{path}") for path in paths)
    save_batch(items, "selected_source_index.json")


def collect_market_metadata():
    """POST to a documented read-only lookup; no wallet or transaction calls."""
    repos = list(csv.DictReader((ROOT / "sources/dataset/repos.csv").open(encoding="utf-8-sig")))
    selected = [(r["repo"].replace("/", "__"), r["seer_market"])
                for r in repos if r["repo"] in ("alloy-rs/alloy", "arkworks-rs/algebra")]
    selected.append(("parent", "0x37ab5cbeee3a32289430e5d38b914ec7f580fd87"))

    def fetch(item):
        name, market_id = item
        url = "https://app.seer.pm/.netlify/functions/get-market"
        body = json.dumps({"chainId": 10, "id": market_id}).encode()
        record = {"url": url, "method": "POST", "request": json.loads(body),
                  "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        target = SOURCES / "seer/market_metadata" / (name + ".json")
        try:
            request = urllib.request.Request(url, data=body,
                                             headers={"Content-Type": "application/json", "User-Agent": "Public-originality-research/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read()
                record.update(status=response.status, final_url=response.url,
                              sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.with_suffix(".json.source.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        except (urllib.error.URLError, TimeoutError) as error:
            record.update(status=getattr(error, "code", None), error=str(error))
        return {"local_path": target.relative_to(ROOT).as_posix(), **record}

    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(fetch, selected))
    (OUT / "metadata_source_index.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"saved": sum(r.get("status") == 200 for r in records),
                      "failed": [r for r in records if r.get("status") != 200]}, indent=2))


if __name__ == "__main__":
    main()
