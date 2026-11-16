"""Pin high-impact repository evidence and fetch selected published artifacts."""
import base64
import concurrent.futures
import hashlib
import json

from collect_audit_sources import AUDIT, SOURCES
from collect_sources import ROOT, download

PIN_REPOS = [
    "ethereum/js-ethereum-cryptography", "ChainSafe/bls", "aestus-relay/mev-boost-relay",
    "smartcontracts/simple-optimism-node", "scaffold-eth/scaffold-eth-2", "succinctlabs/sp1",
    "succinctlabs/rsp", "succinctlabs/op-succinct", "risc0/risc0-ethereum", "alloy-rs/alloy",
    "foundry-rs/foundry", "paradigmxyz/reth", "lambdaclass/ethrex", "Certora/CertoraProver",
    "safe-global/safe-smart-account", "paulmillr/noble-curves", "supranational/blst",
    "skalenetwork/libBLS", "nomicfoundation/hardhat", "evmts/tevm-monorepo",
    "DefiLlama/chainlist", "ethstaker/ethstaker-deposit-cli", "l2beat/l2beat", "libp2p/libp2p",
]
ROOT_REPOS = ["dappnode/DAppNode", "ethereum/eips", "nethermindeth/nethermind",
              "status-im/nimbus-eth2", "taikoxyz/taiko-mono", "TrueBlocks/trueblocks-core"]
PACKAGES = ["ethereum-cryptography", "@chainsafe/bls", "@tevm/vm", "@tevm/node",
            "hardhat-deploy", "@shazow/whatsabi", "@safe-global/safe-smart-account"]


def collect(tasks):
    def fetch(task):
        record = download(task["url"], task["path"])
        return {**{k: v for k, v in task.items() if k != "path"},
                "local_path": task["path"].relative_to(ROOT).as_posix(), **record}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(fetch, tasks))


def main():
    tasks = [dict(id=repo + ":head", repo=repo, kind="repository_commit_metadata",
                  url="https://api.github.com/repos/" + repo + "/commits?per_page=1",
                  path=SOURCES / "heads" / (repo.replace("/", "__") + ".json")) for repo in PIN_REPOS]
    tasks.extend(dict(id=repo + ":root", repo=repo, kind="repository_directory_metadata",
                      url="https://api.github.com/repos/" + repo + "/contents",
                      path=SOURCES / "roots" / (repo.replace("/", "__") + ".json")) for repo in ROOT_REPOS)
    records = collect(tasks)
    readmes = {r["repo"]: r for r in json.loads((ROOT / "sources/repository_index.json").read_text(encoding="utf-8"))}
    assessments = {r["repo"]: r for r in __import__("build_forecast").csv_rows(ROOT / "evidence_assessments.csv")}
    pinned_tasks = []
    for record in records:
        if record["kind"] != "repository_commit_metadata" or record.get("status") != 200:
            continue
        repo = record["repo"]
        data = json.loads((ROOT / record["local_path"]).read_text(encoding="utf-8"))
        sha = data[0]["sha"]
        old_paths = [__import__("pathlib").Path(readmes[repo]["path"])]
        folder = ROOT / "sources/repositories" / repo.replace("/", "__")
        old_paths.extend((folder / p).resolve() for p in assessments[repo]["supporting_files"].split(";") if p)
        for old in old_paths:
            provenance = json.loads(old.with_suffix(old.suffix + ".source.json").read_text(encoding="utf-8"))
            prefix = "https://raw.githubusercontent.com/" + repo + "/HEAD/"
            if not provenance["url"].startswith(prefix):
                continue
            relative = provenance["url"][len(prefix):]
            pinned_tasks.append(dict(id=repo + ":pinned:" + relative, repo=repo, commit=sha,
                                     kind="commit_pinned_repository_source",
                                     url="https://raw.githubusercontent.com/" + repo + "/" + sha + "/" + relative,
                                     baseline_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
                                     path=SOURCES / "pinned" / repo.replace("/", "__") / relative))
    records.extend(collect(pinned_tasks))
    artifacts = []
    for package in PACKAGES:
        metadata = json.loads((SOURCES / "npm" / (package.replace("/", "__") + ".json")).read_text(encoding="utf-8"))
        artifacts.append(dict(id="artifact:" + package, package=package, version=metadata["version"],
                              kind="published_registry_artifact", url=metadata["dist"]["tarball"],
                              integrity=metadata["dist"].get("integrity"), shasum=metadata["dist"].get("shasum"),
                              path=SOURCES / "artifacts" / (package.replace("/", "__") + ".tgz")))
    artifact_records = collect(artifacts)
    for record in artifact_records:
        if record.get("status") != 200:
            continue
        body = (ROOT / record["local_path"]).read_bytes()
        integrity = record.get("integrity")
        record["sha1_matches_registry"] = hashlib.sha1(body).hexdigest() == record["shasum"]
        if integrity:
            algorithm, encoded = integrity.split("-", 1)
            record["integrity_matches_registry"] = base64.b64encode(hashlib.new(algorithm, body).digest()).decode() == encoded
    records.extend(artifact_records)
    (AUDIT / "followup_index.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"attempted": len(records), "successful": sum(r.get("status") == 200 for r in records),
                      "pinned_same_as_original": sum(r.get("sha256") == r.get("baseline_sha256") for r in records if r["kind"] == "commit_pinned_repository_source"),
                      "pinned_total": sum(r["kind"] == "commit_pinned_repository_source" for r in records),
                      "artifact_integrity": [{"package": r["package"], "sha1": r.get("sha1_matches_registry"), "sri": r.get("integrity_matches_registry")} for r in artifact_records],
                      "failures": [{"id": r["id"], "status": r.get("status")} for r in records if r.get("status") != 200]}, indent=2))


if __name__ == "__main__":
    main()
