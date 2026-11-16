# Deep Funding Round 3 originality forecast

**Research date: November 16, 2026. Market snapshot: 11:10:32 UTC.**

This forecast estimates the new jury averages for all 98 required repository rows.
It combines repository evidence, current market prices, and limited historical ratings.
It does not guarantee exact results or a competition rank.

## Forecast files

- [submission.csv](submission.csv): the complete forecast in the official `repo,originality` format.
- [repository_forecasts.md](repository_forecasts.md): all 98 forecasts, scenario ranges, rationales, and source links.
- [forecast_details.csv](forecast_details.csv): component values, weights, market differences, and sensitivity results.
- [forecast_sources.json](forecast_sources.json): repository source URLs, collection times, and verified SHA-256 hashes.
- [forecast_diagnostics.json](forecast_diagnostics.json): aggregate statistics and retrospective scores.
- [market_diagnostics.csv](market_diagnostics.csv): chart movements and collateral-denominated market statistics.

The forecast mean is **0.731**. Its median is **0.759**, and its range is **0.293–0.909**.
The mean raw UP quote is **0.733**.
The main differences concern individual projects, not a broad downward adjustment across Ethereum.

## 1. What the forecast measures

Originality concerns a repository's own contribution relative to its dependencies.
It does not measure popularity, token returns, adoption, security, or usefulness.
A useful integration can have lower originality than a foundational library.
An implementation of established mathematics can still contain substantial original software work.

Each target is the repository's average jury rating, divided by 100.
Repository values are independent. They **do not sum to one**.

The official metric is the **sum of absolute errors**, or SAE:

```text
SAE = sum(abs(prediction[repo] - mean_jury_rating[repo] / 100))
```

Lower SAE is better. A 0.10 error contributes 0.10, regardless of the repository's size or adoption.
Under absolute loss, the optimal point estimate is a median of the uncertainty distribution for the future jury average.
The blend below is a heuristic estimate, not a fitted distribution or a formally optimal median.

The [current competition information](https://deepfunding-predictivefundingchallengeforopensou-78c7e9f.hf.space/competition_info) explains the target and leaderboards.
An [archived copy](sources/competition/competition_info.json) preserves the information used here.

## 2. Dataset findings

The [official dataset](https://huggingface.co/datasets/DeepFunding/originality-r3-data) contains:

| Data | Finding |
|---|---|
| Required repository rows | 98 |
| Historical individual ratings | 51 |
| Repositories with historical averages | 33 |
| Historical repositories with only one juror | 23 of 33 |
| Historical target mean | 0.775050 |
| Historical target median | 0.800 |
| Published market snapshot | October 16, 2026, 10:55 UTC |

Historical ratings are sparse and uneven. They are not a representative calibration sample for all 98 rows.
The 65 rows without historical labels require other evidence.

Juror disagreement also matters:

- `axiom-crypto/snark-verifier` received **0.90 and 0.48**.
- Remix received **0.60, 0.95, and 0.80**.
- Solidity received ratings from **0.80 to 1.00**.

Some notes contain factual problems. One Solidity note refers to BLS cryptography.
A Nimbus note describes Nim as new. A Foundry note implies no dependencies.
These notes do not override current source evidence.

The public leaderboard uses the 33 published historical averages.
The private leaderboard remains a public-score placeholder until new Round 3 targets become available.
Therefore, a low public error is not evidence of future accuracy.

### Required names and aliases

Both `hyperledger-web3j/web3j` and `LFDT-web3j/web3j` resolve to the same current repository.
Both remain required submission rows. Both receive **0.765**.
Their market prices differ, so their shared forecast uses the average of the two raw UP quotes.

The submission preserves every official spelling and row order.
The [dataset audit](dataset_analysis.json) records label statistics and market-address checks.

## 3. Market research

### Correct market set

The market source is the [current Round 3 quote endpoint](https://deep.seer.pm/.netlify/functions/get-originality-r3-v3-markets-data).
The [saved response](sources/market/live_markets.json) was fetched at **2026-11-16 11:10:32 UTC**.
All 98 repository market addresses match `repos.csv`.

The current public client identifies this parent market:

```text
0x37ab5cbeee3a32289430e5d38b914ec7f580fd87
```

The site distinguishes older Round 3 markets as incorrect and disables their trading controls.
Using those older markets would mix different instruments into the forecast.
The [saved public client](sources/market/index-BCzRvg8P.js) records this distinction.

### Raw UP versus normalized UP

The dataset explains that UP pays proportionally to the final originality score.
Prices use each market's repository collateral token.
UP and DOWN trade in separate pools, and the market also has an Invalid outcome.

In the current snapshot:

- UP + DOWN ranges from **0.854817 to 1.000056**.
- **13** pairs sum to less than **0.98**.
- **7** pairs sum to less than **0.95**.

The primary forecast uses raw UP. It does not assume that UP and DOWN must sum to one.
This follows the dataset's description of UP as the market estimate of the proportional payout.
Raw UP still contains liquidity, collateral, and invalid-resolution effects.
It is not a pure or guaranteed unbiased estimate of jury opinion.

The sensitivity calculation instead uses:

```text
normalized_UP = UP / (UP + DOWN)
```

Normalization is not automatically a correction. It discards the pair's discount and can materially change the estimate.
For Alloy, raw UP is **0.751**, while normalized UP is **0.879**.
The resulting forecast changes from **0.800 to 0.870**.
This 0.070 difference is methodological uncertainty, not evidence that either value is correct.

Six forecasts change by more than 0.020 under normalization:
Alloy, Fe, Arkworks algebra, Aderyn, L2BEAT, and Safe.
Both versions appear in `forecast_details.csv`.

### Price changes and market activity

The chart endpoint returned 104 records. The analysis retains only the 98 required leaf markets.
The recorded chart window ends at **November 16, 2026, 07:00 UTC**.
Seven-day changes use the last recorded price at or before the seven-day boundary.
They are not exact trade-to-trade returns.

| Repository | Recorded seven-day UP change |
|---|---:|
| Eth Docker | −0.099146 |
| MCL | −0.077819 |
| WhatsABI | +0.067501 |
| noble-curves | −0.062052 |
| Safe | −0.059114 |

Across all 98 charts, 43 prices rose and 55 fell. The median change was **−0.0042415**.

The latest recorded UP transition occurs at **01:30 UTC on November 16** for 97 of 98 charts.
Its maximum absolute size is only **0.000110**.
These synchronized tails resemble snapshot or rounding updates. They do not establish 97 independent trades.
The chart timestamps are not confirmed trade timestamps.

Reported volume and liquidity use different repository collateral tokens, **not USD**.
Gross liquidity is not executable depth. Cumulative volume is not seven-day volume.
Neither statistic identifies independent traders or guarantees an accurate market price.
For these reasons, momentum and volume do not determine the forecast weights.

## 4. Ethereum repository evidence

Documentation was collected for all 98 rows.
The review used READMEs, bounded excerpts, selected dependency manifests, selected code, and GitHub provenance.
It was not an exhaustive code audit or a line-by-line originality measurement.

The central question was: **Which project implements the essential functionality, and which project supplies it through a dependency?**
Internal workspace modules are not automatically external dependencies.
Development-only packages do not necessarily supply runtime functionality.
Dependency counts, lines of code, commits, stars, and forks are not direct originality percentages.

### Evidence behind the largest downward differences

| Repository | Forecast | Raw UP | Main evidence |
|---|---:|---:|---|
| `ethereum/js-ethereum-cryptography` | **0.293** | 0.508 | Documentation describes noble/scure re-exports; selected source files confirm delegation. |
| `smartcontracts/simple-optimism-node` | **0.442** | 0.625 | Docker Compose deploys OP Stack images rather than implementing their execution protocol. |
| `ChainSafe/bls` | **0.457** | 0.617 | Native blst bindings and a herumi WASM backend supply the cryptographic core. |
| `aestus-relay/mev-boost-relay` | **0.515** | 0.721 | Flashbots fork ancestry, with substantive relay additions but extensive inherited functionality. |
| `scaffold-eth/scaffold-eth-2` | **0.542** | 0.724 | Wagmi, Viem, RainbowKit, and NextJS provide central application functionality. |
| `succinctlabs/rsp` | **0.565** | 0.669 | Reth supplies execution and SP1 supplies proving; witness integration remains original work. |
| `risc0/risc0-ethereum` | **0.633** | 0.735 | Ethereum integration depends on the separate RISC Zero zkVM. |

These are forecast disagreements, **not proven market mispricing**.
They depend on how the new jurors allocate credit between integration and upstream implementation.
The linked [repository rationales](repository_forecasts.md) provide the supporting sources.

### Forks require a scope assessment

Aestus is **147 commits ahead and 18 behind** the compared Flashbots branch.
The returned comparison lists 26 changed files, including latency and MEV-commit functionality.
Fork ancestry does not imply zero original work.

However, Aestus's historical rating was **0.89**, far above this forecast.
Its **0.20–0.93** scenario range reflects unusually large uncertainty about the jury's scope.
The 0.515 point estimate is a substantial, risky departure from that historical judgment.

Ethstaker's deposit CLI is **678 commits ahead and 28 behind** the compared staking-deposit-cli branch.
Its comparison returns 300 files. Renames and API limits prevent a complete diff-based originality measurement.
Key and validator-exit workflows support credit for subsequent work. Its forecast is **0.610**.

### Foundational implementations versus their applications

The forecast distinguishes these dependency relationships:

- blst implements BLS primitives; ChainSafe BLS exposes bindings and integration.
- MCL implements pairing arithmetic; SKALE libBLS adds threshold-signature and key-generation functionality.
- Arkworks algebra supplies arithmetic foundations used by higher-level cryptographic systems.
- SP1 credits Plonky3; RSP and OP Succinct then depend on SP1 and execution stacks.
- Titanoboa adds debugging and development features over Vyper and py-evm.
- WhatsABI implements bytecode analysis; Swiss Knife integrates WhatsABI alongside other tools.

These distinctions support higher estimates for foundational implementations than for some downstream integrations.
They do not imply that downstream projects are less useful.

### Current repository scope

Current sources also prevent several stale interpretations:

- Hardhat 3 delegates Ethereum runtime functionality to EDR.
- Viem's published-package manifest is more informative than its root manifest.
- hardhat-deploy code now lives in Rocketh and depends on that framework.
- TEVM documents a native migration with ZEVM, Voltaire, and Guillotine Mini.
- powdr separates its current scope from powdr-legacy.
- Reth and Foundry currently reference evm2; a revm-only description is incomplete.
- Aderyn is retired, and Lambda Ethereum Consensus is archived.

Retirement or archival status alone does not reduce originality.
The competition does not specify a sufficiently clear repository cutoff to eliminate these scope uncertainties.

## 5. Selected high forecasts

| Repository | Forecast | Raw UP | Main contribution |
|---|---:|---:|---|
| `supranational/blst` | **0.909** | 0.839 | Foundational C and assembly BLS implementation. |
| `ethereum/consensus-specs` | **0.902** | 0.855 | Protocol specifications and executable consensus descriptions. |
| `ethereum/eips` | **0.891** | 0.791 | Proposal research and protocol standardization. |
| `Consensys/gnark-crypto` | **0.863** | 0.825 | Field arithmetic and pairing implementations. |
| `ethers-io/ethers.js` | **0.863** | 0.843 | Substantial Ethereum SDK implementation. |
| `argotorg/solidity` | **0.862** | 0.825 | Language design and compiler implementation. |
| `status-im/nimbus-eth2` | **0.855** | 0.821 | Independent, resource-efficient consensus-client engineering. |
| `shazow/whatsabi` | **0.835** | 0.830 | Bytecode analysis and proxy-resolution algorithms. |

The manually assigned category summaries show the same distinction:

| Category | Rows | Mean forecast | Mean raw UP |
|---|---:|---:|---:|
| Specifications | 4 | 0.852 | 0.801 |
| Cryptographic primitives | 8 | 0.830 | 0.776 |
| Clients | 16 | 0.780 | 0.762 |
| Zero-knowledge systems | 9 | 0.661 | 0.688 |
| Deployment tools | 5 | 0.536 | 0.599 |
| Wrappers | 4 | 0.467 | 0.630 |

These summaries describe this forecast. They are not validated category-level facts about jury behavior.

## 6. Forecast method and uncertainty

For each repository:

```text
prediction = wE * E + wH * H + wM * M
wH = 0.30 * n / (n + 2), when historical ratings exist
wH = 0, otherwise
wM = 1 - wE - wH
```

- `E`: the subjective evidence prior in `evidence_assessments.csv`.
- `H`: the published historical average, when available.
- `n`: the number of historical jurors.
- `M`: the raw UP quote, except for the shared Web3j alias average.
- `wE`: a manually selected evidence weight from **0.35 to 0.60**.

Direct evidence of core delegation generally receives a stronger evidence weight.
Broad descriptions and unresolved scope generally receive a weaker weight.
Neither these weights nor the evidence priors were learned from a training process.
They have no demonstrated calibration or claim of Bayesian optimality.

One historical juror gives `wH = 0.10`. Two give `0.15`, and six give `0.225`.
These are cautious heuristic weights, not measured reliability estimates.
Market prices may already reflect public ratings, so the components are not necessarily independent.

For JS Ethereum Cryptography, the calculation is:

```text
0.60 * 0.15 + 0.40 * 0.5080039 = 0.2932016
submission value = 0.293
```

The submission rounds each value to three decimals.
This is file precision, not a claim of three-decimal predictive accuracy.

### Sensitivity and scenarios

`forecast_details.csv` includes three alternative calculations:

1. Use normalized UP instead of raw UP.
2. Remove direct historical-label use and return its weight to the market.
3. Increase or decrease the evidence weight by 0.10.

The largest rounded change under the evidence-weight adjustment is **0.037**.
The largest normalization change is **0.070**.
These calculations test selected modeling choices, not every possible source of error.

Scenario ranges reflect plausible disagreements about dependency credit and repository scope.
They are **not calibrated confidence or prediction intervals**.
No coverage probability, such as 80% or 95%, is assigned to them.

## 7. Retrospective diagnostics, not future validation

The official scorer produces these errors against the 33 **known R1 averages**:

| Method | Public SAE |
|---|---:|
| Constant 0.800 | 3.670000 |
| October raw UP | 2.734761 |
| November raw UP | 2.465020 |
| November normalized UP | 2.503960 |
| Subjective evidence priors alone | 2.880000 |
| Recommended blend, with direct history | **2.277000** |
| Blend without direct history | 2.533666 |

**These are not held-out results.** The recommendation directly includes the published historical targets.
Those targets were also visible during the research.
Even the history-free calculation is not a blind experiment.

The history-free blend does **not** beat raw market prices on these old labels.
The research therefore has not demonstrated a predictive advantage over the market.
The recommended values express evidence-based judgments about new Round 3 ratings, not proven superior accuracy.

Exact final accuracy, expected rank, and winning probability cannot be established from the available data.
The new jury targets do not yet exist.

## 8. Reproduce and validate

The local build and validation use Python's standard library.
Use Python 3.10 or later and the complete research folder, including `sources`.
Run these commands from this report's directory:

```powershell
python build_forecast.py
python -m unittest test_forecast.py -v
python sources/dataset/metric.py submission.csv --solution sources/dataset/public_leaderboard_targets.csv
```

The build overwrites its generated forecast files. It does not submit a file or execute a trade.
It uses saved inputs rather than fresh network requests.
`sources/repository_index.json` currently records absolute collection paths, so retain the folder's original location for this build.

Validation on November 16, 2026 confirmed:

- All 98 required rows are present, with finite values in `[0,1]`.
- Both Web3j aliases have identical forecasts.
- Every forecast reproduces from its declared components.
- Historical averages agree with the individual ratings, within published rounding.
- All cited repository source hashes match their saved files.
- Only the 98 required leaf markets enter the chart analysis.
- All **nine local tests pass**.
- The official scorer reports **public error: 2.2770**.

The submission SHA-256 is:

```text
d2cdc04285f48dd7fe29a3992faca81201eda2dbc5430bf6aa22fcb679daf8ae
```

Online `HEAD` links can change. Use the saved files and provenance sidecars to inspect the evidence from this research date.
Collection failures appear in the source-index files rather than as invented evidence.

## 9. Competition conditions and remaining gaps

The [current rules](https://deepfunding-predictivefundingchallengeforopensou-78c7e9f.hf.space/rules) state:

- Submissions close **December 10, 2026, 23:59 UTC**.
- Only the latest successfully scored submission counts.
- Prizes are **$1,000, $650, and $350** for the three eligible places.
- Prize eligibility requires a qualifying **$10 sUSDS trade** on the Round 3 markets.
- Organizers manually verify the top three submissions' trades.

The [archived rules](sources/competition/rules.json) preserve the source used here.
This forecast does not establish anyone's eligibility or authorize a transaction.

Remaining gaps include the precise repository evaluation cutoff, final private evaluation set, and market execution costs.
Wallet-to-team verification, additional eligibility restrictions, and detailed payout arrangements also require organizer confirmation.

The strongest defensible conclusion is a relative one:
foundational implementations and protocol specifications deserve more originality credit than several heavily delegated integrations.
The exact credit allocation remains a prediction about human jurors.
