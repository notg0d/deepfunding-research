"""Collect selected dependency manifests, project code, and public provenance metadata."""
import concurrent.futures
import json
from collect_sources import download, RAW

FILES = {
    "0xMiden/miden-vm": ["Cargo.toml"],
    "a16z/halmos": ["pyproject.toml"],
    "a16z/helios": ["Cargo.toml"],
    "aestus-relay/mev-boost-relay": ["go.mod"],
    "alloy-rs/alloy": ["Cargo.toml"],
    "apeworx/ape": ["pyproject.toml"],
    "argotorg/hevm": ["hevm.cabal"],
    "argotorg/act": ["act.cabal"],
    "axiom-crypto/snark-verifier": ["Cargo.toml", "snark-verifier/Cargo.toml", "snark-verifier-sdk/Cargo.toml"],
    "ChainSafe/bls": ["package.json"],
    "chainsafe/lodestar": ["packages/beacon-node/package.json"],
    "Commit-Boost/commit-boost-client": ["Cargo.toml"],
    "Consensys/gnark-crypto": ["go.mod"],
    "Cyfrin/aderyn": ["Cargo.toml", "aderyn_core/Cargo.toml"],
    "DefiLlama/chainlist": ["package.json", "constants/chainList.js"],
    "DefiLlama/DefiLlama-Adapters": ["package.json"],
    "dl-solarity/solidity-lib": ["package.json"],
    "edb-rs/edb": ["Cargo.toml"],
    "erigontech/erigon": ["go.mod"],
    "erigontech/silkworm": [".gitmodules"],
    "EspressoSystems/jellyfish": ["Cargo.toml"],
    "eth-infinitism/account-abstraction": ["package.json"],
    "ethereum/js-ethereum-cryptography": ["package.json", "src/keccak.ts", "src/secp256k1.ts"],
    "ethereum/py_ecc": ["pyproject.toml"],
    "ethereum/web3.py": ["pyproject.toml"],
    "ethers-io/ethers.js": ["package.json"],
    "ethpandaops/checkpointz": ["go.mod"],
    "ethpandaops/ethereum-package": ["kurtosis.yml", "main.star"],
    "ethstaker/ethstaker-deposit-cli": ["pyproject.toml", "setup.py"],
    "evmts/tevm-monorepo": ["package.json"],
    "flashbots/mev-boost": ["go.mod"],
    "flashbots/mev-boost-relay": ["go.mod"],
    "flashbots/rbuilder": ["Cargo.toml"],
    "foundry-rs/foundry": ["Cargo.toml"],
    "grandinetech/grandine": ["Cargo.toml"],
    "herumi/mcl": [".gitmodules"],
    "lambdaclass/ethrex": ["Cargo.toml"],
    "lambdaclass/lambdaworks": ["Cargo.toml", "math/Cargo.toml"],
    "NethermindEth/juno": ["go.mod"],
    "nomicfoundation/hardhat": ["v-next/hardhat/package.json", "v-next/hardhat-edr/Cargo.toml"],
    "OffchainLabs/stylus-sdk-rs": ["Cargo.toml", "stylus-sdk/Cargo.toml"],
    "otterscan/otterscan": ["package.json"],
    "paradigmxyz/reth": ["Cargo.toml"],
    "paulmillr/noble-curves": ["package.json"],
    "Plonky3/Plonky3": ["Cargo.toml"],
    "powdr-labs/powdr": ["Cargo.toml"],
    "risc0/risc0-ethereum": ["Cargo.toml", "contracts/src/groth16/RiscZeroGroth16Verifier.sol"],
    "safe-global/safe-smart-account": ["contracts/Safe.sol", "package.json"],
    "scaffold-eth/scaffold-eth-2": ["packages/nextjs/package.json"],
    "shazow/whatsabi": ["package.json"],
    "skalenetwork/libBLS": ["CMakeLists.txt"],
    "smartcontracts/simple-optimism-node": ["docker-compose.yml"],
    "succinctlabs/op-succinct": ["Cargo.toml"],
    "succinctlabs/rsp": ["Cargo.toml"],
    "succinctlabs/sp1": ["Cargo.toml"],
    "supranational/blst": ["build.sh"],
    "swiss-knife-xyz/swiss-knife": ["package.json"],
    "vyperlang/titanoboa": ["pyproject.toml", "setup.py"],
    "vyperlang/vyper": ["pyproject.toml"],
    "wevm/viem": ["src/README.md", "src/package.json", "package.json"],
    "wealdtech/ethdo": ["go.mod"],
    "wighawag/hardhat-deploy": ["package.json"],
}
METADATA = ["aestus-relay/mev-boost-relay", "hyperledger-web3j/web3j", "LFDT-web3j/web3j",
            "ethstaker/ethstaker-deposit-cli", "argotorg/hevm", "erigontech/erigon",
            "Cyfrin/aderyn", "wighawag/hardhat-deploy", "ethereum/web3.py", "powdr-labs/powdr"]


def collect():
    tasks = [(f"https://raw.githubusercontent.com/{repo}/HEAD/{filename}",
              RAW / "repositories" / repo.replace("/", "__") / filename)
             for repo, files in FILES.items() for filename in files]
    tasks.extend(("https://api.github.com/repos/" + repo,
                  RAW / "repositories" / repo.replace("/", "__") / "github_metadata.json") for repo in METADATA)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda task: download(*task), tasks))
    (RAW / "extra_sources_index.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"success": sum(r.get("status") == 200 for r in results),
                      "failures": [r for r in results if r.get("status") != 200]}, indent=2))


if __name__ == "__main__":
    collect()
