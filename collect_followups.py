"""Resolve key provenance and dependency-source gaps with public GitHub data."""
import concurrent.futures
import json
from collect_sources import download, RAW

FILES = {
    "alloy-rs/alloy": ["Cargo.toml"],
    "DefiLlama/chainlist": ["pages/index.js", "scripts/generateChainData.js"],
    "nomicfoundation/hardhat": ["v-next/hardhat/package.json", "packages/hardhat/package.json"],
    "lambdaclass/lambdaworks": ["crates/math/Cargo.toml"],
    "skalenetwork/libBLS": ["deps/CMakeLists.txt", "bls/bls.cpp"],
    "paulmillr/noble-curves": ["README.md"],
}
APIS = {
    "aestus-relay/mev-boost-relay": ("https://api.github.com/repos/flashbots/mev-boost-relay/compare/main...aestus-relay:main", "fork_comparison.json"),
    "ethstaker/ethstaker-deposit-cli": ("https://api.github.com/repos/ethereum/staking-deposit-cli/compare/master...ethstaker:main", "fork_comparison.json"),
    "DefiLlama/chainlist": ("https://api.github.com/repos/DefiLlama/chainlist/contents", "root_contents.json"),
    "nomicfoundation/hardhat": ("https://api.github.com/repos/nomicfoundation/hardhat/contents", "root_contents.json"),
    "wighawag/hardhat-deploy": ("https://api.github.com/repos/wighawag/hardhat-deploy/contents", "root_contents.json"),
}

tasks = [(f"https://raw.githubusercontent.com/{repo}/HEAD/{filename}",
          RAW / "repositories" / repo.replace("/", "__") / filename)
         for repo, files in FILES.items() for filename in files if not (RAW / "repositories" / repo.replace("/", "__") / filename).exists()]
tasks.extend((url, RAW / "repositories" / repo.replace("/", "__") / filename) for repo,(url,filename) in APIS.items())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(lambda task: download(*task), tasks))
(RAW / "followup_sources_index.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
