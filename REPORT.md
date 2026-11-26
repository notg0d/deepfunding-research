# Deep Funding Round 3 originality forecast

**Research refreshed: November 26, 2026. Market snapshot: 09:00:23 UTC.**

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
- [MARKET_REVIEW.md](MARKET_REVIEW.md): comparison of the November 26 snapshot with the original forecast and a record of which rows changed.

The refreshed forecast mean is **0.743**. Its median is **0.765**, and its range is **0.378–0.925**.
The current mean raw UP quote is **0.757**.
The forecast still includes uncalibrated, repository-specific evidence adjustments.

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
Both remain required submission rows. Both receive **0.778** in the refreshed file.
Their market prices differ, so their shared forecast uses the average of the two raw UP quotes.

The submission preserves every official spelling and row order.
The [dataset audit](dataset_analysis.json) records label statistics and market-address checks.

## 3. Market research

### Correct market set

The market source is the [current Round 3 quote endpoint](https://deep.seer.pm/.netlify/functions/get-originality-r3-v3-markets-data).
The [saved response](sources/market/live_markets.json) was fetched at **2026-11-26 09:00:23 UTC**.
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

- UP + DOWN ranges from **0.985060 to 1.059781**.
- No pair sums to less than **0.98** in this snapshot.

The primary forecast uses raw UP. It does not assume that UP and DOWN must sum to one.
This follows the dataset's description of UP as the market estimate of the proportional payout.
Raw UP still contains liquidity, collateral, and invalid-resolution effects.
It is not a pure or guaranteed unbiased estimate of jury opinion.

The sensitivity calculation instead uses:

```text
normalized_UP = UP / (UP + DOWN)
```

Normalization is not automatically a correction. It discards the pair's discount and can change the estimate.
The largest resulting forecast change is **0.023**, for DAppNode.
This is methodological sensitivity, not evidence that either value is correct.

Only one forecast changes by more than 0.020 under normalization: DAppNode.
Both versions appear in `forecast_details.csv`.

### Price changes and market activity

The chart endpoint returned 104 records. The analysis retains only the 98 required leaf markets.
The recorded chart window ends at **November 26, 2026, 08:30 UTC**.
Seven-day changes use the last recorded price at or before the seven-day boundary.
They are not exact trade-to-trade returns.

| Repository | Recorded seven-day UP change |
|---|---:|
| Ethereum JS Cryptography | +0.212367 |
| WhatsABI | −0.129830 |
| EIPs | +0.098377 |
| Act | +0.096682 |
| ChainSafe BLS | +0.095843 |

Across all 98 charts, 72 prices rose and 26 fell. The median change was **+0.021996**.

The latest recorded UP transitions occur at **01:00, 05:00, and 07:00 UTC on November 26**.
The largest final transition is only **0.000118**.
These synchronized tails resemble snapshot or rounding updates. They do not establish independent trades.
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
| `ethereum/js-ethereum-cryptography` | **0.378** | 0.721 | Documentation describes noble/scure re-exports; selected source files confirm delegation. |
| `smartcontracts/simple-optimism-node` | **0.453** | 0.653 | Docker Compose deploys OP Stack images rather than implementing their execution protocol. |
| `ChainSafe/bls` | **0.495** | 0.713 | Native blst bindings and a herumi WASM backend supply the cryptographic core. |
| `aestus-relay/mev-boost-relay` | **0.532** | 0.777 | Flashbots fork ancestry, with substantive relay additions but extensive inherited functionality. |
| `scaffold-eth/scaffold-eth-2` | **0.526** | 0.686 | Wagmi, Viem, RainbowKit, and NextJS provide central application functionality. |
| `succinctlabs/rsp` | **0.567** | 0.672 | Reth supplies execution and SP1 supplies proving; witness integration remains original work. |
| `risc0/risc0-ethereum` | **0.611** | 0.685 | Ethereum integration depends on the separate RISC Zero zkVM. |

These are forecast disagreements, **not proven market mispricing**.
They depend on how the new jurors allocate credit between integration and upstream implementation.
The linked [repository rationales](repository_forecasts.md) provide the supporting sources.

### Forks require a scope assessment

Aestus is **147 commits ahead and 18 behind** the compared Flashbots branch.
The returned comparison lists 26 changed files, including latency and MEV-commit functionality.
Fork ancestry does not imply zero original work.

However, Aestus's historical rating was **0.89**, far above this forecast.
Its **0.20–0.93** scenario range reflects unusually large uncertainty about the jury's scope.
The refreshed 0.532 point estimate remains a substantial, risky departure from that historical judgment.

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
| `ethereum/eips` | **0.925** | 0.890 | Proposal research and protocol standardization. |
| `ethereum/consensus-specs` | **0.910** | 0.875 | Protocol specifications and executable consensus descriptions. |
| `supranational/blst` | **0.910** | 0.839 | Foundational C and assembly BLS implementation. |
| `status-im/nimbus-eth2` | **0.877** | 0.866 | Independent, resource-efficient consensus-client engineering. |
| `ethers-io/ethers.js` | **0.874** | 0.872 | Substantial Ethereum SDK implementation. |
| `Consensys/gnark-crypto` | **0.869** | 0.838 | Field arithmetic and pairing implementations. |
| `argotorg/solidity` | **0.868** | 0.845 | Language design and compiler implementation. |
| `paulmillr/noble-curves` | **0.868** | 0.846 | Cryptographic curve implementation with independent security reviews. |

The manually assigned category summaries show the same distinction:

| Category | Rows | Mean forecast | Mean raw UP |
|---|---:|---:|---:|
| Specifications | 4 | 0.858 | 0.823 |
| Cryptographic primitives | 8 | 0.846 | 0.805 |
| Clients | 16 | 0.793 | 0.784 |
| Zero-knowledge systems | 9 | 0.659 | 0.682 |
| Deployment tools | 5 | 0.563 | 0.653 |
| Wrappers | 4 | 0.502 | 0.715 |

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
0.60 * 0.15 + 0.40 * 0.7207351 = 0.3782940
submission value = 0.378
```

The submission rounds each value to three decimals.
This is file precision, not a claim of three-decimal predictive accuracy.

### Sensitivity and scenarios

`forecast_details.csv` includes three alternative calculations:

1. Use normalized UP instead of raw UP.
2. Remove direct historical-label use and return its weight to the market.
3. Increase or decrease the evidence weight by 0.10.

The largest rounded change under the evidence-weight adjustment is **0.057**.
The largest normalization change is **0.023**.
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
| November 16 raw UP | 2.465020 |
| November 26 raw UP | 1.741816 |
| November 26 normalized UP | 1.736882 |
| Subjective evidence priors alone | 2.880000 |
| Refreshed blend, with direct history | **2.009000** |
| Refreshed blend without direct history | 2.191000 |

**These are not held-out results.** The recommendation directly includes the published historical targets.
Those targets were also visible during the research.
Even the history-free calculation is not a blind experiment.

The refreshed market and blend errors are retrospective comparisons on the same published labels, which the research already used.
They are not held-out evidence of Round 3 accuracy or of an advantage over the market.
The refreshed values express evidence-based judgments about new Round 3 ratings, not proven superior accuracy.

Exact final accuracy, expected rank, and winning probability cannot be established from the available data.
The new jury targets do not yet exist.

## 8. Reproduce and validate

The local build and validation use Python's standard library.
Use Python 3.10 or later and the complete research folder, including `sources`.
Run these commands from this report's directory:

```powershell
python build_forecast.py
python -m unittest test_forecast.py -v
python -m unittest test_strict_audit.py test_insight_review.py -v
python sources/dataset/metric.py submission.csv --solution sources/dataset/public_leaderboard_targets.csv
```

The build overwrites its generated forecast files. It does not submit a file or execute a trade.
It uses saved inputs rather than fresh network requests.
The original November 16 generated artifacts remain preserved in [strict_audit/baseline](strict_audit/baseline). Current forecast files use the refreshed market input.

Validation on November 26, 2026 confirmed:

- All 98 required rows are present, with finite values in `[0,1]`.
- Both Web3j aliases have identical forecasts.
- Every forecast reproduces from its declared components.
- Historical averages agree with the individual ratings, within published rounding.
- All cited repository source hashes match their saved files.
- Only the 98 required leaf markets enter the chart analysis.
- All **36 local tests pass**.
- The official scorer reports **public error: 2.0090**. This remains an in-sample diagnostic, not validation against Round 3 jury scores.

The submission SHA-256 is:

```text
33504dc379f7d92db25e0bb0574f284a33191630ecdb56ba3dbda9ecfb009f52
```

The forecast now uses a November 26 market snapshot. A fresh market update changes **93 of 98** rounded predictions from the original November 16 submission. See the [market refresh review](MARKET_REVIEW.md) for the comparison and major movers.
Online `HEAD` links can change. Use the saved files and provenance sidecars to inspect the evidence from each research date.
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
