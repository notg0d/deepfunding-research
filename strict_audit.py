"""Run offline integrity and arithmetic checks. Write only new audit artifacts."""
import base64
from collections import Counter, defaultdict
import csv
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import statistics
import tarfile

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "strict_audit"
D = Decimal
ALIASES = ("hyperledger-web3j/web3j", "LFDT-web3j/web3j")

# These links confirm roles or selected technical facts, not originality scores.
ECOSYSTEM = {
    "a16z/helios": ("ethereum_clients.md", "Helios"),
    "chainsafe/lodestar": ("ethereum_clients.md", "Lodestar"),
    "consensys/teku": ("ethereum_clients.md", "Teku"),
    "erigontech/erigon": ("ethereum_clients.md", "Turbo‐Geth"),
    "ethereum/go-ethereum": ("ethereum_clients.md", "Go Ethereum"),
    "grandinetech/grandine": ("ethereum_clients.md", "Grandine"),
    "hyperledger/besu": ("ethereum_clients.md", "Besu"),
    "nethermindeth/nethermind": ("ethereum_clients.md", "Nethermind"),
    "OffchainLabs/prysm": ("ethereum_clients.md", "Prysm"),
    "paradigmxyz/reth": ("ethereum_clients.md", "Reth"),
    "sigp/lighthouse": ("ethereum_clients.md", "Lighthouse"),
    "status-im/nimbus-eth2": ("ethereum_clients.md", "Nimbus"),
    "argotorg/solidity": ("ethereum_languages.md", "Solidity"),
    "vyperlang/vyper": ("ethereum_languages.md", "Vyper"),
    "remix-project-org/remix-project": ("ethereum_languages.md", "Remix IDE"),
    "foundry-rs/foundry": ("ethereum_frameworks.md", "Foundry"),
    "nomicfoundation/hardhat": ("ethereum_frameworks.md", "Hardhat"),
    "hyperledger-web3j/web3j": ("ethereum_frameworks.md", "web3j"),
    "LFDT-web3j/web3j": ("ethereum_frameworks.md", "web3j"),
    "scaffold-eth/scaffold-eth-2": ("ethereum_frameworks.md", "Scaffold-ETH 2"),
    "openzeppelin/openzeppelin-contracts": ("ethereum_libraries.md", "OpenZeppelin Contracts"),
}
REGISTRY = {
    "ethereum/js-ethereum-cryptography": ["npm/ethereum-cryptography.json"],
    "ChainSafe/bls": ["npm/@chainsafe__bls.json", "npm/@chainsafe__blst.json"],
    "paulmillr/noble-curves": ["npm/@noble__curves.json"],
    "ethers-io/ethers.js": ["npm/ethers.json"],
    "wevm/viem": ["npm/viem.json"],
    "nomicfoundation/hardhat": ["npm/hardhat.json", "npm/@nomicfoundation__edr.json"],
    "wighawag/hardhat-deploy": ["npm/hardhat-deploy.json"],
    "evmts/tevm-monorepo": ["npm/@tevm__vm.json", "npm/@tevm__node.json", "npm/@tevm__memory-client.json"],
    "shazow/whatsabi": ["npm/@shazow__whatsabi.json"],
    "openzeppelin/openzeppelin-contracts": ["npm/@openzeppelin__contracts.json"],
    "safe-global/safe-smart-account": ["npm/@safe-global__safe-smart-account.json"],
    "vyperlang/titanoboa": ["pypi/titanoboa.json"],
    "vyperlang/vyper": ["pypi/vyper.json"],
    "ethereum/web3.py": ["pypi/web3.json"],
    "apeworx/ape": ["pypi/eth-ape.json"],
    "ethereum/py_ecc": ["pypi/py-ecc.json"],
    "supranational/blst": ["crates/blst.json"],
    "alloy-rs/alloy": ["crates/alloy.json"],
    "succinctlabs/sp1": ["crates/sp1-sdk.json"],
}
PACKAGE_REPOS = {
    "ethereum-cryptography": "ethereum/js-ethereum-cryptography", "@chainsafe/bls": "ChainSafe/bls",
    "@tevm/vm": "evmts/tevm-monorepo", "@tevm/node": "evmts/tevm-monorepo",
    "hardhat-deploy": "wighawag/hardhat-deploy", "@shazow/whatsabi": "shazow/whatsabi",
    "@safe-global/safe-smart-account": "safe-global/safe-smart-account",
}
SCOPE_NOTES = {
    "dappnode/DAppNode": "Correction: this repository contains ISO/install assets. The management application is in separate DNP_DAPPMANAGER code. Do not attribute that application automatically to this row.",
    "evmts/tevm-monorepo": "HEAD describes a breaking native migration. Published next.148 JavaScript packages still use EthereumJS. Both delegate execution; the evaluation version is unknown.",
    "libp2p/libp2p": "Umbrella/community repository. Implementations AND formal specifications live in separate repositories. R1 notes explicitly evaluated implementations beyond this repository.",
    "TrueBlocks/trueblocks-core": "Current .gitmodules places chifra, sdk and khedra in separate repositories. Same-project submodules are not automatically external dependencies; credit boundaries remain unresolved.",
    "wighawag/hardhat-deploy": "The current published package lives in wighawag/rocketh and requires Rocketh peers. The official row retains the older repository name.",
    "powdr-labs/powdr": "Current and powdr-legacy scopes differ. Repository cutoff is unknown.",
    "risc0/risc0-ethereum": "Steel moved to a separate repository. Do not attribute all zkVM or Steel implementation to this integration repository.",
    "Cyfrin/aderyn": "Retirement is not an originality deduction; evaluation version is unknown.",
    "lambdaclass/lambda_ethereum_consensus": "Archived client and successor are different scopes. Archival alone is not an originality deduction.",
    "aestus-relay/mev-boost-relay": "Fork confirmed; original additions confirmed. R1 score 0.89 conflicts with the low subjective prior. Diff/commit counts cannot determine a value share.",
    "ethstaker/ethstaker-deposit-cli": "Fork ancestry confirmed. Truncated/renamed diff paths prevent complete contribution measurement.",
}
TECHNICAL_NOTES = {
    "argotorg/fe": "Cargo workspace confirms compiler components. Optimization entries naming revm do not alone establish a production dependency.",
    "argotorg/solidity": "CMake confirms compiler build scope; Ethereum language documentation corroborates the role, not a score.",
    "argotorg/sourcify": "Server manifest names Sourcify compiler libraries, ethers and WhatsABI; indispensable compilation must receive separate credit.",
    "arkworks-rs/algebra": "Arithmetic workspace confirmed. Established mathematics and generic crates do not imply re-exported arithmetic.",
    "blockscout/blockscout": "Elixir application manifest corroborates application scope; dependencies do not measure indexing originality.",
    "Certora/CertoraProver": "Public build source and solver requirements support the distinction between prover machinery and external SMT solving.",
    "ethereum/consensus-specs": "Executable spec package has cryptographic dependencies, including py_arkworks_bls12381. Specification design is distinct from primitive implementation.",
    "ethereum/eips": "Gemfile covers rendering. EIP-1 covers proposal process; renderer dependencies do not measure standards originality.",
    "ethereum/execution-apis": "Package manifest covers document generation/validation; JSON-RPC specifications remain the assessed contribution.",
    "ethdebug/format": "Root package corroborates the specification workspace, not the share of original format design.",
    "ethereum-lists/chains": "Package manifest and live registry cross-check support maintained-data scope; they do not measure originality.",
    "ethpandaops/ethereum-helm-charts": "Lighthouse chart supplies deployment templates for an external client, not Lighthouse implementation.",
    "ethstaker/eth-docker": "ethd script corroborates client orchestration; script code is not execution/consensus implementation.",
    "herumi/mcl": "CMake builds native C/C++/assembly and offers GMP support. Build metadata does not certify novel mathematics.",
    "holiman/goevmlab": "Go module corroborates Go tooling and external Ethereum components; from-scratch authorship remains a publisher claim.",
    "ipsilon/evmone": "CMake and submodules corroborate native EVM engine scope and EVMC/infrastructure dependencies.",
    "l2beat/l2beat": "Backend manifest confirms an analytics application; ETHBEAT rebrand does not validate the research originality percentage.",
    "lambdaclass/lambda_ethereum_consensus": "Elixir manifest corroborates client and dependency scope; archival is not a numerical penalty.",
    "nethereum/nethereum": "Web3 csproj mostly references internal Nethereum modules. Internal project references are not external packages.",
    "nethermindeth/nethermind": "Correct root Directory.Packages.props exposes .NET packages; generic dependencies do not imply a thin client wrapper.",
    "status-im/nimbus-eth2": "Correct beacon_chain.nimble exposes networking, BLS and serialization dependencies. Nim is not a newly invented language.",
    "taikoxyz/taiko-mono": "Correct root Go module exposes external Ethereum/rollup components; one language manifest does not cover the whole monorepo.",
    "openzeppelin/openzeppelin-contracts": "ERC20 source corroborates contract implementation; standards conformance and originality are different questions.",
    "Vectorized/solady": "ERC20 source corroborates custom Solidity/assembly implementation; prior design attribution still needs judgment.",
    "remix-project-org/remix-project": "Root/lib manifests corroborate IDE integration with Ethereum execution/compiler packages.",
    "protofire/solhint": "Package manifest corroborates parser/tooling dependencies, not the authorship or novelty of every lint rule.",
    "ethereum/js-ethereum-cryptography": "Published 3.2.0 keccak/secp256k1 files directly delegate to noble. This confirms dependency direction, not a 0.293 jury score.",
    "ChainSafe/bls": "Published 8.2.0 source calls @chainsafe/blst and bls-eth-wasm. API guards/initialization remain original integration work.",
    "safe-global/safe-smart-account": "Published 1.5.0 Safe.sol contains authorization/transaction logic and relative imports, including vendored external SafeMath.",
    "shazow/whatsabi": "Published 0.30.0 contains bytecode iteration/disassembly; ABI selector helpers also call ox. It is not merely an ABI database wrapper.",
    "paulmillr/noble-curves": "Independent 2023/2024 security reports inspect implementations. They do not certify current 2.4.0 or any originality score.",
    "supranational/blst": "Galois proof documentation confirms bounded verification work and explicit limitations; the old NCC URL is not a usable report.",
    "paradigmxyz/reth": "Pinned Cargo change adds only an internal version-build module. Alloy/evm2 dependency conclusions are unchanged.",
    "scaffold-eth/scaffold-eth-2": "Manifest and Ethereum framework documentation corroborate NextJS/Wagmi/Viem/RainbowKit integration and custom components.",
}


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def by_repo(rows, names):
    result = {r["repo"]: r for r in rows}
    require(len(result) == len(rows) == len(names), "Missing/duplicate repository rows")
    require(set(result) == set(names), "Repository universe differs")
    return result


def validate_market_snapshot(payload, universe):
    data = payload["marketsData"]
    metadata = {m["id"].lower(): m for m in payload["markets"]}
    require(set(data) == {r["repo"] for r in universe}, "Wrong quote universe")
    require(len(metadata) == len(payload["markets"]) == 98, "Missing/duplicate market metadata")
    max_error, orientations = D(0), Counter()
    for repo in universe:
        quote = data[repo["repo"]]
        market_id = repo["seer_market"].lower()
        require(quote["id"].lower() == market_id, "Market address mismatch")
        market = metadata[market_id]
        collateral = market["collateralToken"].lower()
        require(len(market["wrappedTokens"]) == 3, "Wrong leaf outcome count")
        require(len(set(t.lower() for t in market["wrappedTokens"])) == 3, "Duplicate outcome tokens")
        for side, index in [("up", 1), ("down", 0)]:
            pool = quote[side + "Pool"]
            token0, token1 = pool["token0"].lower(), pool["token1"].lower()
            outcome = market["wrappedTokens"][index].lower()
            require({token0, token1} == {collateral, outcome}, "Wrong pool token pair")
            require(int(token0, 16) < int(token1, 16), "Unsorted pool tokens")
            require(int(pool["liquidity"]) >= 0, "Negative liquidity")
            ratio = D("1.0001") ** int(pool["tick"])
            expected = ratio if token0 == outcome else D(1) / ratio
            observed = D(str(quote[side + "Price"]))
            require(observed.is_finite() and observed > 0, "Invalid market quote")
            error = abs(expected - observed)
            max_error = max(max_error, error)
            require(error < D("0.0000000002"), "Tick-derived quote mismatch")
            require(D(str(pool["price"])) == observed, "Pool/quote price differs")
            orientations[side + ("_direct" if token0 == outcome else "_inverse")] += 1
    return {"markets": len(data), "quotes_checked": 2 * len(data),
            "max_absolute_tick_price_error": float(max_error), "orientations": dict(orientations)}


def collect_indexes():
    return [r for name in ["source_index.json", "followup_index.json", "final_source_index.json"]
            for r in load_json(AUDIT / name)]


def audit():
    universe = csv_rows(ROOT / "sources/dataset/repos.csv")
    names = [r["repo"] for r in universe]
    require(len(set(names)) == len(names) == 98, "Invalid official universe")
    submission_rows = csv_rows(ROOT / "submission.csv")
    predictions = by_repo(submission_rows, names)
    assessments = by_repo(csv_rows(ROOT / "evidence_assessments.csv"), names)
    details = by_repo(csv_rows(ROOT / "forecast_details.csv"), names)
    markets = by_repo(csv_rows(ROOT / "market_analysis.csv"), names)
    originals = load_json(ROOT / "sources/market/live_markets.json")
    refreshed = load_json(AUDIT / "sources/fresh_markets.json")
    indexes = collect_indexes()
    checks = []

    def check(id_, function):
        try:
            value = function()
            checks.append({"id": id_, "status": "PASS", "detail": value})
        except Exception as error:
            checks.append({"id": id_, "status": "FAIL", "detail": str(error)})

    def format_check():
        header = next(csv.reader(io.StringIO((ROOT / "submission.csv").read_text(encoding="utf-8"))))
        require(header == ["repo", "originality"], "Wrong submission header")
        require([r["repo"] for r in submission_rows] == names, "Canonical order changed")
        for name, row in predictions.items():
            value = D(row["originality"])
            require(value.is_finite() and 0 <= value <= 1, "Invalid submission value")
            require(re.fullmatch(r"[01]\.\d{3}", row["originality"]) is not None, "Unexpected precision")
            require(D(assessments[name]["scenario_low"]) <= value <= D(assessments[name]["scenario_high"]), "Scenario does not enclose forecast")
        require(predictions[ALIASES[0]]["originality"] == predictions[ALIASES[1]]["originality"], "Alias values differ")
        return {"rows": 98, "aliases_equal": True, "sha256": sha256(ROOT / "submission.csv")}

    def baseline_check():
        manifest = load_json(AUDIT / "baseline/sha256.json")
        for name, digest in manifest.items():
            require(sha256(AUDIT / "baseline" / name) == digest, "Baseline snapshot changed: " + name)
            require(sha256(ROOT / name) == digest, "Original artifact changed: " + name)
        return {"preserved_artifacts": len(manifest)}

    def saved_hash_check(folder):
        count = 0
        for sidecar in folder.rglob("*.source.json"):
            record = load_json(sidecar)
            if record.get("status") != 200:
                continue
            path = Path(str(sidecar).removesuffix(".source.json"))
            require(path.is_file() and sha256(path) == record["sha256"], "Saved source changed: " + str(path))
            count += 1
        return {"verified_downloads": count}

    def cited_hash_check():
        records = load_json(ROOT / "forecast_sources.json")
        require([r["repo"] for r in records] == names, "Citations do not cover canonical rows")
        sources = [s for row in records for s in row["sources"]]
        for source in sources:
            require(sha256(ROOT / source["local_path"]) == source["sha256"], "Cited source changed")
        return {"repository_rows": len(records), "cited_source_records": len(sources)}

    def official_refresh_check():
        records = [r for r in indexes if r["kind"] in ["official_dataset_refresh", "official_rules_refresh"]]
        for record in records:
            current = ROOT / record["local_path"]
            section = "dataset" if record["kind"] == "official_dataset_refresh" else "competition"
            require(current.read_bytes() == (ROOT / "sources" / section / current.name).read_bytes(), "Official input changed")
        return {"identical_files": len(records)}

    def pinned_check():
        records = [r for r in indexes if r["kind"] == "commit_pinned_repository_source"]
        require(len(records) == 52, "Unexpected pinned-source coverage")
        for r in records:
            require(sha256(ROOT / r["local_path"]) == r["sha256"], "Pinned source changed locally")
            require("/" + r["commit"] + "/" in r["url"], "Commit not pinned in URL")
        changed = [r["id"] for r in records if r["sha256"] != r["baseline_sha256"]]
        require(changed == ["paradigmxyz/reth:pinned:Cargo.toml"], "Unexpected moving-HEAD difference")
        import difflib
        old = (ROOT / "sources/repositories/paradigmxyz__reth/Cargo.toml").read_text(encoding="utf-8").splitlines()
        new = (AUDIT / "sources/pinned/paradigmxyz__reth/Cargo.toml").read_text(encoding="utf-8").splitlines()
        altered = [line for line in difflib.ndiff(old, new) if line.startswith(("+ ", "- "))]
        require(len(altered) == 2 and all("version-build" in line for line in altered), "Reth semantic change needs review")
        return {"files": len(records), "unchanged": 51, "changed": changed,
                "change_scope": "Two additions for an internal version-build module"}

    ratings = csv_rows(ROOT / "sources/dataset/r1_juror_ratings.csv")
    history = defaultdict(list)
    for row in ratings:
        history[row["repo"]].append(D(row["originality"]) / 100)
    targets = {r["repo"]: r for r in csv_rows(ROOT / "sources/dataset/public_leaderboard_targets.csv")}

    def upstream_check():
        upstream = csv_rows(AUDIT / "sources/upstream_r1.csv")
        canonical = {name.casefold(): name for name in names}
        canonical.update({"account-abstraction": "eth-infinitism/account-abstraction", "ethereum/solidity": "argotorg/solidity"})
        normalized = Counter((canonical[r["Repo"].strip().casefold()], r["Repo"], D(r["Originality"]), r["Juror notes"]) for r in upstream)
        published = Counter((r["repo"], r["repo_as_rated"], D(r["originality"]), r["juror_note"]) for r in ratings)
        require(normalized == published, "Upstream labels/notes were changed or lost")
        require(len(ratings) == 51 and len(history) == len(targets) == 33, "Historical coverage differs")
        for name, values in history.items():
            mean = sum(values) / len(values)
            require(mean.quantize(D("0.000001"), rounding=ROUND_HALF_EVEN) == D(targets[name]["originality"]), "Historical mean differs after official six-decimal rounding")
            require(len(values) == int(targets[name]["n_jurors"]), "Historical count differs")
        return {"ratings": len(ratings), "repositories": len(history),
                "single_rating_repositories": sum(len(v) == 1 for v in history.values()),
                "ratings_and_notes_match_upstream": True,
                "target_file_precision_decimals": 6,
                "max_mean_rounding_difference": float(max(abs(sum(v) / len(v) - D(targets[n]["originality"])) for n, v in history.items()))}

    def arithmetic_check():
        for name in names:
            e, row, market = assessments[name], details[name], markets[name]
            raw = D(str(originals["marketsData"][name]["upPrice"]))
            down = D(str(originals["marketsData"][name]["downPrice"]))
            require(abs(raw - D(market["up_price"])) < D("1e-12"), "Market analysis UP differs")
            require(abs(raw / (raw + down) - D(market["up_share"])) < D("1e-12"), "Normalized quote differs")
            normalized = raw / (raw + down)
            anchor = raw
            if name in ALIASES:
                anchor = sum(D(str(originals["marketsData"][n]["upPrice"])) for n in ALIASES) / 2
                normalized = sum(D(markets[n]["up_share"]) for n in ALIASES) / 2
            require(abs(anchor - D(row["market_anchor_used"])) < D("1e-12"), "Wrong anchor")
            prior, w_e = D(e["evidence_prior"]), D(e["evidence_weight"])
            count = len(history[name])
            h = D(targets[name]["originality"]) if count else D(0)
            w_h = D("0.30") * count / (count + 2) if count else D(0)
            w_m = 1 - w_e - w_h
            require(min(w_e, w_h, w_m) >= 0 and w_e + w_h + w_m == 1, "Invalid weights")
            require(w_h.quantize(D("0.000001"), rounding=ROUND_HALF_EVEN) == D(row["historical_weight"]), "Wrong rounded historical weight")
            require(w_m.quantize(D("0.000001"), rounding=ROUND_HALF_EVEN) == D(row["market_weight"]), "Wrong rounded market weight")
            if count:
                require(abs(h - D(row["historical_target"])) < D("1e-12"), "Wrong historical anchor")
            require(count == int(row["historical_n_jurors"]), "Wrong juror count")
            values = {
                "originality": w_e * prior + w_h * h + w_m * anchor,
                "prediction_if_normalized_market": w_e * prior + w_h * h + w_m * normalized,
                "prediction_without_history": w_e * prior + (1 - w_e) * anchor,
                "prediction_with_evidence_weight_minus_010": (w_e - D("0.10")) * prior + w_h * h + (w_m + D("0.10")) * anchor,
                "prediction_with_evidence_weight_plus_010": (w_e + D("0.10")) * prior + w_h * h + (w_m - D("0.10")) * anchor,
            }
            for field, value in values.items():
                rounded = value.quantize(D("0.001"), rounding=ROUND_HALF_EVEN)
                require(rounded == D(row[field]), "Forecast/sensitivity differs: " + name + ":" + field)
            require(D(row["originality"]) == D(predictions[name]["originality"]), "Submission/detail differs")
        return {"rows": len(names), "rounded_values_checked": 5 * len(names), "arithmetic": "Independent Decimal calculation"}

    def score_check():
        spec = importlib.util.spec_from_file_location("audit_official_metric", ROOT / "sources/dataset/metric.py")
        metric = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(metric)
        repo_map = metric.load_repos((ROOT / "sources/dataset/repos.csv").read_bytes())
        parsed = metric.parse_submission((ROOT / "submission.csv").read_bytes(), repo_map)
        solution = metric.load_solution((ROOT / "sources/dataset/public_leaderboard_targets.csv").read_bytes(), repo_map)
        official = metric.score_split(parsed, solution["public"])
        actual_targets = {name: D(row["originality"]) for name, row in targets.items()}
        errors = lambda values: sum(abs(D(str(values[name])) - actual_targets[name]) for name in actual_targets)
        scores = {
            "live_raw_up": errors({n: originals["marketsData"][n]["upPrice"] for n in names}),
            "live_normalized_up": errors({n: markets[n]["up_share"] for n in names}),
            "subjective_evidence_prior": errors({n: assessments[n]["evidence_prior"] for n in names}),
            "recommended_forecast_uses_public_history": errors({n: predictions[n]["originality"] for n in names}),
            "forecast_without_direct_history_but_not_blind": errors({n: details[n]["prediction_without_history"] for n in names}),
        }
        require(abs(D(str(official)) - scores["recommended_forecast_uses_public_history"]) < D("1e-12"), "Official/manual SAE differs")
        declared = load_json(ROOT / "forecast_diagnostics.json")["historical_public_diagnostics_NOT_heldout_validation"]
        for name, value in scores.items():
            require(abs(value - D(str(declared[name]))) < D("1e-12"), "Declared retrospective SAE differs")
        return {"official_submission_sae": official, "independent_sae": {k: float(v) for k, v in scores.items()},
                "held_out": False, "future_accuracy_validated": False}

    def artifact_check():
        records = [r for r in indexes if r["kind"] == "published_registry_artifact"]
        reviews = load_json(AUDIT / "artifact_review_index.json")
        require(len(records) == len(reviews) == 7, "Unexpected package coverage")
        for record in records:
            body = (ROOT / record["local_path"]).read_bytes()
            require(hashlib.sha1(body).hexdigest() == record["shasum"], "Tarball SHA1 differs")
            algorithm, encoded = record["integrity"].split("-", 1)
            require(base64.b64encode(hashlib.new(algorithm, body).digest()).decode() == encoded, "Tarball SRI differs")
            registry = load_json(AUDIT / "sources/npm" / (record["package"].replace("/", "__") + ".json"))
            require(registry["dist"]["integrity"] == record["integrity"], "Tarball/index registry metadata differs")
        for review in reviews:
            require(not review["missing_selected_files"], "Missing selected artifact file")
            require(review["identity_and_dependencies_match_registry"] and review["normalized_repository_matches_registry"], "Artifact identity differs")
            require(sha256(ROOT / review["tarball_path"]) == review["tarball_sha256"], "Tarball review checksum differs")
            with tarfile.open(ROOT / review["tarball_path"], "r:gz") as archive:
                for file in review["reviewed_files"]:
                    body = archive.extractfile(file["member"]).read()
                    require(hashlib.sha256(body).hexdigest() == file["sha256"], "Archive/extracted file differs")
                    require(sha256(ROOT / file["local_path"]) == file["sha256"], "Extracted file changed")
        return {"tarballs": 7, "sha1_and_sri_match": True,
                "selected_files_checked": sum(len(r["reviewed_files"]) for r in reviews), "package_code_executed": False}

    def source_exceptions_check():
        pdfs = load_json(AUDIT / "pdf_extraction.json")
        valid = [r for r in pdfs if r["pdf_signature_valid"]]
        invalid = [r for r in pdfs if not r["pdf_signature_valid"]]
        require(len(valid) == 2 and len(invalid) == 1, "PDF signature results differ")
        require(not (AUDIT / "sources/blst_ncc.pdf").read_bytes().startswith(b"%PDF-"), "Unexpected NCC content change")
        for pdf in valid:
            require(sha256(ROOT / pdf["source"]) == pdf["source_sha256"], "Extracted PDF hash differs")
            require((ROOT / pdf["text_file"]).is_file(), "Missing PDF text")
        return {"valid_pdf_reports": 2, "excluded": "NCC URL returns generic HTML despite HTTP 200"}

    for id_, function in [
        ("submission_format", format_check), ("original_artifacts_preserved", baseline_check),
        ("original_download_hashes", lambda: saved_hash_check(ROOT / "sources")),
        ("original_citation_hashes", cited_hash_check),
        ("audit_download_hashes", lambda: saved_hash_check(AUDIT / "sources")),
        ("official_refresh_matches", official_refresh_check), ("commit_pinned_sources", pinned_check),
        ("upstream_historical_labels", upstream_check),
        ("original_market_token_orientation", lambda: validate_market_snapshot(originals, universe)),
        ("fresh_market_token_orientation", lambda: validate_market_snapshot(refreshed, universe)),
        ("independent_blend_and_sensitivities", arithmetic_check), ("independent_sae", score_check),
        ("published_artifact_integrity", artifact_check), ("source_content_exceptions_identified", source_exceptions_check),
    ]:
        check(id_, function)

    def quote_refresh_check():
        changes = sorted(((name, D(str(refreshed["marketsData"][name]["upPrice"])) - D(str(originals["marketsData"][name]["upPrice"]))) for name in names), key=lambda r: abs(r[1]), reverse=True)
        blended_changes = []
        for name, _ in changes:
            anchor_names = ALIASES if name in ALIASES else (name,)
            delta = sum(D(str(refreshed["marketsData"][n]["upPrice"])) - D(str(originals["marketsData"][n]["upPrice"])) for n in anchor_names) / len(anchor_names)
            count = len(history[name])
            w_h = D("0.30") * count / (count + 2) if count else D(0)
            w_m = 1 - D(assessments[name]["evidence_weight"]) - w_h
            blended_changes.append((name, delta * w_m))
        return {"largest_raw_up_changes": [{"repo": n, "change": float(v)} for n, v in changes[:8]],
                "maximum_unrounded_blend_change": float(max(abs(v) for _, v in blended_changes)),
                "original_forecast_inputs_replaced": False}
    check("fresh_quote_sensitivity", quote_refresh_check)

    matrix = []
    original_citations = {r["repo"]: r["sources"] for r in load_json(ROOT / "forecast_sources.json")}
    artifacts = load_json(AUDIT / "artifact_review_index.json")
    for name in names:
        original_paths = [s["local_path"] for s in original_citations[name]]
        extra = [r for r in indexes if r.get("repo") == name and r.get("status") == 200]
        technical = [r["local_path"] for r in extra if r["kind"] in ["additional_repository_source", "resolved_repository_source", "commit_pinned_repository_source"] and Path(r["local_path"]).name.lower() not in ["readme.md", "readme.rst", "readme"]]
        technical.extend(p for p in original_paths if Path(p).name.lower() not in ["readme.md", "readme.rst", "readme", "github_metadata.json", "fork_comparison.json"])
        registry_paths = ["strict_audit/sources/" + p for p in REGISTRY.get(name, [])]
        artifact_paths = [f["local_path"] for r in artifacts if PACKAGE_REPOS[r["package"]] == name for f in r["reviewed_files"]]
        independent = []
        if name in ECOSYSTEM:
            filename, term = ECOSYSTEM[name]
            path = "strict_audit/sources/" + filename
            require(term in (ROOT / path).read_text(encoding="utf-8"), "Ecosystem citation does not contain relevant role")
            independent.append(path)
        if name == "paulmillr/noble-curves":
            independent.extend(["strict_audit/sources/noble_trailofbits.txt", "strict_audit/sources/noble_cure53.txt"])
        if name == "supranational/blst":
            independent.append("strict_audit/sources/blst_galois.md")
        all_paths = list(dict.fromkeys(original_paths + [r["local_path"] for r in extra] + registry_paths + artifact_paths + independent))
        require(all((ROOT / p).is_file() for p in all_paths), "Matrix contains missing evidence")
        matrix.append({
            "repo": name, "forecast_original_unchanged": predictions[name]["originality"],
            "arithmetic_verified": "yes" if all(c["status"] == "PASS" for c in checks) else "see_failed_checks",
            "original_readme_only": "yes" if not assessments[name]["supporting_files"] else "no",
            "technical_files_beyond_readme": len(set(technical)),
            "registry_metadata_available": "yes" if registry_paths else "no",
            "published_artifact_selected_files": len(artifact_paths),
            "independent_role_or_implementation_corroboration": "limited" if independent else "none_collected",
            "independent_evidence_limit": "Role/selected implementation only; ecosystem pages can be stale or contributor-authored; commissioned reports have bounded scope" if independent else "Publisher/hosting/market evidence is not an independent review",
            "r1_ratings": len(history[name]),
            "scope_or_conflict_flag": "yes" if name in SCOPE_NOTES else "no_specific_flag; cutoff_unknown",
            "technical_crosscheck": TECHNICAL_NOTES.get(name, "Selected repository source/build/dependency evidence supports only bounded role and dependency checks." if technical else "Repository documentation and metadata only; core code attribution remains unverified."),
            "scope_note": SCOPE_NOTES.get(name, "No specific conflict established. The common evaluation-cutoff and subjective-weight limitations still apply."),
            "exact_originality_percentage_validated": "no",
            "future_predictive_accuracy_validated": "no",
            "audit_action": "retain_original_unvalidated; scope_review_required" if name in SCOPE_NOTES else "retain_original_unvalidated",
            "supporting_paths": ";".join(all_paths),
            "independent_paths": ";".join(independent),
        })
    checks.append({"id": "all_repository_crosscheck_matrix", "status": "PASS", "detail": {
        "canonical_rows": len(matrix), "no_validated_percentages": all(r["exact_originality_percentage_validated"] == "no" for r in matrix)}})
    result = {
        "audit_date_utc": "2026-11-16", "verdict": "TECHNICAL_CHECKS_PASS_WITH_RESEARCH_LIMITATIONS" if all(c["status"] == "PASS" for c in checks) else "TECHNICAL_CHECKS_FAILED",
        "forecast_certified_as_accurate": False, "numerical_revisions": 0,
        "checks": checks,
        "collection": {"attempts_recorded": len(indexes), "successful_downloads": sum(r.get("status") == 200 for r in indexes),
                       "http_failures": [{"id": r["id"], "status": r.get("status"), "url": r["url"]} for r in indexes if r.get("status") != 200]},
        "coverage": {"rows": len(matrix), "original_readme_only": sum(r["original_readme_only"] == "yes" for r in matrix),
                     "rows_with_technical_files_beyond_readme": sum(r["technical_files_beyond_readme"] > 0 for r in matrix),
                     "rows_with_registry_metadata": sum(r["registry_metadata_available"] == "yes" for r in matrix),
                     "rows_with_selected_published_artifacts": sum(r["published_artifact_selected_files"] > 0 for r in matrix),
                     "rows_with_limited_independent_corroboration": sum(r["independent_role_or_implementation_corroboration"] == "limited" for r in matrix),
                     "rows_without_independent_corroboration": sum(r["independent_role_or_implementation_corroboration"] == "none_collected" for r in matrix),
                     "specific_scope_or_conflict_flags": sum(r["scope_or_conflict_flag"] == "yes" for r in matrix),
                     "validated_originality_percentages": 0},
        "research_limitations": [
            "New Round 3 labels do not exist; future accuracy and ranking are not measurable.",
            "Public-label use is allowed, but retrospective SAE is not held-out validation.",
            "The history-free forecast does not outperform raw markets on the visible R1 sample.",
            "Priors, weights and scenario bounds are subjective and uncalibrated.",
            "Market prices can already reflect public labels; components are correlated.",
            "Not all repositories have independent corroboration; code review is bounded, not exhaustive.",
            "Version/cutoff, repository-versus-ecosystem credit and final evaluation coverage remain unclear.",
            "No on-chain RPC, trade-depth, price execution or independent trader verification was performed.",
            "Security audits and formal proofs do not measure originality; current-version coverage cannot be assumed.",
            "Web search returned HTTP 402; direct sources were available.",
        ],
    }
    return result, matrix


def main():
    result, matrix = audit()
    (AUDIT / "audit_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (AUDIT / "repository_crosscheck.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(matrix[0]))
        writer.writeheader()
        writer.writerows(matrix)
    print(json.dumps({"verdict": result["verdict"], "checks": [{"id": r["id"], "status": r["status"], **({"detail": r["detail"]} if r["status"] == "FAIL" else {})} for r in result["checks"]],
                      "coverage": result["coverage"], "collection": result["collection"]}, indent=2))
    if any(r["status"] == "FAIL" for r in result["checks"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
