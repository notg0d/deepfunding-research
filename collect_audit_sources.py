"""Collect read-only cross-check sources without replacing the original evidence."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
from urllib.parse import quote

from collect_sources import ROOT, download

AUDIT = ROOT / "strict_audit"
SOURCES = AUDIT / "sources"

DOCUMENTS = [
    ("ethereum_clients", "https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/nodes-and-clients/index.md", "ecosystem_documentation", "ethereum_clients.md"),
    ("ethereum_languages", "https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/smart-contracts/languages/index.md", "ecosystem_documentation", "ethereum_languages.md"),
    ("ethereum_libraries", "https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/smart-contracts/libraries/index.md", "ecosystem_documentation", "ethereum_libraries.md"),
    ("ethereum_frameworks", "https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/frameworks/index.md", "ecosystem_documentation", "ethereum_frameworks.md"),
    ("ethereum_verification", "https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/smart-contracts/formal-verification/index.md", "ecosystem_documentation", "ethereum_verification.md"),
    ("upstream_r1", "https://raw.githubusercontent.com/deepfunding/oss-evals/main/Originality%20R1%20-%20Sheet1.csv", "official_upstream_labels", "upstream_r1.csv"),
    ("noble_trailofbits", "https://raw.githubusercontent.com/trailofbits/publications/master/reviews/2023-01-ryanshea-noblecurveslibrary-securityreview.pdf", "independent_auditor", "noble_trailofbits.pdf"),
    ("noble_cure53", "https://cure53.de/audit-report_noble-crypto-libs.pdf", "independent_auditor", "noble_cure53.pdf"),
    ("blst_ncc", "https://research.nccgroup.com/wp-content/uploads/2021/01/NCC_Group_EthereumFoundation_ETHF002_Report_2021-01-20_v1.0.pdf", "independent_auditor", "blst_ncc.pdf"),
    ("blst_galois", "https://raw.githubusercontent.com/GaloisInc/BLST-Verification/HEAD/README.md", "independent_verification_project", "blst_galois.md"),
    ("aestus_site", "https://aestus.live/", "publisher_documentation", "aestus.html"),
    ("aestus_docs", "https://aestus.live/docs/", "publisher_documentation", "aestus_docs.html"),
    ("scaffold_docs", "https://docs.scaffoldeth.io/", "publisher_documentation", "scaffold.html"),
    ("evm2_upstream", "https://raw.githubusercontent.com/alloy-rs/evm2/HEAD/README.md", "dependency_upstream", "evm2.md"),
    ("ethbeat_site", "https://ethbeat.org/", "publisher_documentation", "ethbeat.html"),
    ("chain_registry", "https://chainid.network/chains.json", "dependency_upstream", "chain_registry.json"),
    ("sp1_docs", "https://docs.succinct.xyz/docs/sp1/introduction", "publisher_documentation", "sp1_docs.html"),
    ("certora_docs", "https://docs.certora.com/en/latest/docs/prover/index.html", "publisher_documentation", "certora.html"),
    ("seer_documentation", "https://docs.seer.pm/", "publisher_documentation", "seer.html"),
    ("github_rate_limit", "https://api.github.com/rate_limit", "hosting_metadata", "github_rate_limit.json"),
]

EXTRA_FILES = {
    "argotorg/fe": ["Cargo.toml"],
    "argotorg/solidity": ["CMakeLists.txt"],
    "argotorg/sourcify": ["package.json", "services/server/package.json"],
    "arkworks-rs/algebra": ["Cargo.toml"],
    "blockscout/blockscout": ["mix.exs"],
    "Certora/CertoraProver": ["build.gradle.kts"],
    "consensys/teku": ["build.gradle"],
    "dappnode/DAppNode": ["package.json"],
    "ethdebug/format": ["package.json"],
    "ethereum-lists/chains": ["package.json"],
    "ethereum/consensus-specs": ["pyproject.toml"],
    "ethereum/eips": ["package.json"],
    "ethereum/execution-apis": ["package.json"],
    "ethereum/go-ethereum": ["go.mod"],
    "ethpandaops/ethereum-helm-charts": ["charts/lighthouse/Chart.yaml"],
    "ethstaker/eth-docker": ["ethd"],
    "herumi/mcl": ["CMakeLists.txt"],
    "holiman/goevmlab": ["go.mod"],
    "hyperledger/besu": ["build.gradle"],
    "intellij-solidity/intellij-solidity": ["build.gradle.kts"],
    "ipsilon/evmone": ["CMakeLists.txt", ".gitmodules"],
    "l2beat/l2beat": ["package.json", "packages/backend/package.json"],
    "lambdaclass/lambda_ethereum_consensus": ["mix.exs"],
    "nethereum/nethereum": ["src/Nethereum.Web3/Nethereum.Web3.csproj"],
    "nethermindeth/nethermind": ["src/Nethermind/Directory.Packages.props"],
    "OffchainLabs/prysm": ["go.mod"],
    "openzeppelin/openzeppelin-contracts": ["package.json", "contracts/token/ERC20/ERC20.sol"],
    "protofire/solhint": ["package.json"],
    "remix-project-org/remix-project": ["package.json", "libs/remix-lib/package.json"],
    "sigp/lighthouse": ["Cargo.toml"],
    "status-im/nimbus-eth2": ["nimbus_beacon_node.nimble"],
    "taikoxyz/taiko-mono": ["packages/taiko-client/go.mod"],
    "TrueBlocks/trueblocks-core": ["src/apps/chifra/go.mod"],
    "Vectorized/solady": ["src/tokens/ERC20.sol"],
}

NPM_PACKAGES = [
    "ethereum-cryptography", "@chainsafe/bls", "@chainsafe/blst", "@noble/curves",
    "@noble/hashes", "ethers", "viem", "hardhat", "hardhat-deploy",
    "@tevm/node", "@tevm/vm", "@tevm/memory-client", "@shazow/whatsabi",
    "@openzeppelin/contracts", "@safe-global/safe-smart-account", "@nomicfoundation/edr",
]
PYPI_PACKAGES = ["titanoboa", "vyper", "web3", "eth-ape", "py-ecc"]
CRATES = ["blst", "alloy", "sp1-sdk", "revm"]


def snapshot():
    baseline = AUDIT / "baseline"
    baseline.mkdir(parents=True, exist_ok=True)
    names = ["submission.csv", "forecast_details.csv", "forecast_diagnostics.json", "forecast_sources.json",
             "evidence_assessments.csv", "market_analysis.csv", "market_diagnostics.csv", "REPORT.md",
             "repository_forecasts.md", "build_forecast.py", "test_forecast.py"]
    for name in names:
        target = baseline / name
        if not target.exists():
            shutil.copyfile(ROOT / name, target)
    manifest = {name: hashlib.sha256((baseline / name).read_bytes()).hexdigest() for name in names}
    (baseline / "sha256.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def tasks():
    result = [dict(id=id_, url=url, kind=kind, path=SOURCES / filename)
              for id_, url, kind, filename in DOCUMENTS]
    base = "https://huggingface.co/datasets/DeepFunding/originality-r3-data/raw/main/"
    for filename in ["README.md", "repos.csv", "r1_juror_ratings.csv", "public_leaderboard_targets.csv", "market_prices.csv", "metric.py"]:
        result.append(dict(id="official_" + filename, url=base + filename,
                           kind="official_dataset_refresh", path=SOURCES / "dataset" / filename))
    for name in ["rules", "competition_info"]:
        result.append(dict(id="official_" + name, url="https://deepfunding-predictivefundingchallengeforopensou-78c7e9f.hf.space/" + name,
                           kind="official_rules_refresh", path=SOURCES / "competition" / (name + ".json")))
    result.append(dict(id="fresh_market", url="https://deep.seer.pm/.netlify/functions/get-originality-r3-v3-markets-data",
                       kind="official_market_refresh", path=SOURCES / "fresh_markets.json"))
    for repo, files in EXTRA_FILES.items():
        for filename in files:
            result.append(dict(id=repo + ":" + filename,
                               url="https://raw.githubusercontent.com/" + repo + "/HEAD/" + filename,
                               kind="additional_repository_source", repo=repo,
                               path=SOURCES / "repositories" / repo.replace("/", "__") / filename))
    for package in NPM_PACKAGES:
        result.append(dict(id="npm:" + package, url="https://registry.npmjs.org/" + quote(package, safe="") + "/latest",
                           kind="registry_publisher_metadata", package=package,
                           path=SOURCES / "npm" / (package.replace("/", "__") + ".json")))
    for package in PYPI_PACKAGES:
        result.append(dict(id="pypi:" + package, url="https://pypi.org/pypi/" + package + "/json",
                           kind="registry_publisher_metadata", package=package,
                           path=SOURCES / "pypi" / (package + ".json")))
    for package in CRATES:
        result.append(dict(id="crates:" + package, url="https://crates.io/api/v1/crates/" + package,
                           kind="registry_publisher_metadata", package=package,
                           path=SOURCES / "crates" / (package + ".json")))
    return result


def main():
    snapshot()
    planned = tasks()
    def fetch(task):
        provenance = download(task["url"], task["path"])
        return {**{key: value for key, value in task.items() if key != "path"},
                "local_path": task["path"].relative_to(ROOT).as_posix(), **provenance}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(fetch, planned))
    (AUDIT / "source_index.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"attempted": len(records), "successful": sum(r.get("status") == 200 for r in records),
                      "failures": [{"id": r["id"], "status": r.get("status"), "error": r.get("error")} for r in records if r.get("status") != 200]}, indent=2))


if __name__ == "__main__":
    main()
