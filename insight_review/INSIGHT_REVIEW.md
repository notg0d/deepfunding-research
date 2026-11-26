# Review of the proposed originality-forecast changes

**Research date: November 16, 2026.**
**Scenario prices: the original 11:10:32 UTC snapshot.**

The proposal identifies a useful normalization sensitivity. It does not establish a reliable forecast correction.
Its explanation of price deficits omits Invalid, and two supplied midpoint forecasts have rounding errors.
The four repository comments contain useful scope questions, but they do not validate replacement percentages.

The original November 16 submission and generated inputs are preserved in [`strict_audit/baseline/`](../strict_audit/baseline/). The alternatives below use that archived market snapshot; they are research scenarios, not revised submissions.

## 1. Price deficits: a real observation, an incomplete explanation

### What the official sources say

The [official dataset README](https://huggingface.co/datasets/DeepFunding/originality-r3-data/blob/main/README.md) states:

> UP and DOWN trade in separate pools, and part of the value sits in the market's Invalid outcome, so UP + DOWN is not exactly 1

This contradicts the claim that a deficit is *purely* an AMM spread.
The saved [README](../sources/dataset/README.md), line 33, preserves this statement.

Seer's [RealityProxy documentation](https://docs.seer.pm/developers/contracts/core/realityproxy.md) describes three scalar outcomes.
The reviewed [contract source](sources/seer/code/contracts/src/RealityProxy.sol), lines 128–149, confirms the payout logic:

| Resolution | DOWN payout | UP payout | Invalid payout |
|---|---:|---:|---:|
| Valid normalized score `x`, between 0 and 1 | `1 - x` | `x` | 0 |
| Invalid answer | 0 | 0 | 1 |

The contract reports payout numerators.
The reviewed [Conditional Tokens source](sources/seer/ConditionalTokens.sol), lines 86–95 and 242, sums the numerators and divides payouts accordingly.
This source inspection is not verification of the deployed bytecode.

Read-only market lookups confirm the actual Alloy and Arkworks markets have `DOWN`, `UP`, and `Invalid` outcomes.
Both use scalar template 1, a zero lower bound, and an upper bound of `100 × 10^18`.
See [Alloy metadata](sources/seer/market_metadata/alloy-rs__alloy.json) and [Arkworks metadata](sources/seer/market_metadata/arkworks-rs__algebra.json).
The [API reference](https://docs.seer.pm/developers/api.md) documents these read-only lookups.

### What normalization can mean

For illustration, assume coherent prices in the local repo-token unit, with no additional discount or pool distortion.
Let `q` be the pricing-weighted probability of a valid child-market resolution, conditional on its parent branch.
Let `mu` be the pricing-weighted mean score in that valid branch.

```text
UP = q × mu
DOWN = q × (1 - mu)
UP + DOWN = q
UP / (UP + DOWN) = mu
```

Under those assumptions, normalization removes the Invalid allowance. It estimates a score conditional on valid resolution.
That can be relevant to forecasting jury scores rather than cash payouts.
It is not evidence that traders actually supplied coherent prices or real-world probabilities.

The markets are conditional and have repo-specific collateral tokens.
Seer's [conditional-market guide](https://docs.seer.pm/developers/guides/conditional-markets.md) explains the parent-token backing.
Its [split/merge guide](https://docs.seer.pm/developers/guides/split-merge-and-redeem.md) requires a full set of outcomes to recover collateral.
For these scalar markets, UP and DOWN alone omit Invalid from that full set.

The observed deficit can therefore reflect Invalid valuation, separate-pool dislocation, or more complex collateral/pricing effects.
These data do not identify each cause's share.
For Alloy and Arkworks, the lookup reports no Invalid pool. There is no reliable Invalid quote here to reconcile the three prices.
Do not interpret its missing pool as proof that Invalid has zero value.
The same lookup returns zero USD liquidity despite visible pool balances; those fields do not establish absent local liquidity.

The audited prices are marginal tick-based pool prices. They are not bid/ask spreads or size-specific executable quotes.
A sum below 0.98 is not a liquidity measurement.
Seer's [trading guide](https://docs.seer.pm/developers/guides/trading.md) separates trade quotes, amounts, routing, and slippage.

**Finding:** Normalization is a plausible conditional-score scenario. Calling it a proven mechanical correction is not justified.

## 2. The claimed independent agreement is not independent

All 13 markets below 0.98 appear in [deficit_markets.csv](deficit_markets.csv).
Normalized UP is closer to the subjective evidence prior in **nine**, and farther away in **four**.
The four counterexamples are Aderyn, DefiLlama-Adapters, js-ethereum-cryptography, and TEVM.

Aderyn directly contradicts the highlighted agreement claim:

```text
Evidence prior: 0.660000
Raw UP:        0.673693
Normalized UP: 0.730675
```

Normalization moves Aderyn farther from its prior, not closer.
Moreover, normalized UP is computed from the same two pool prices. It is not another market observation.
The evidence priors were researched with market prices and historical labels visible. They are not blind estimates.

When the sum is below one, normalization always raises a positive UP price.
Agreement with an upward prior can arise from that algebra, selection of examples, or a genuine conditional-score signal.
These observations cannot distinguish those explanations.

## 3. Exact scenario results

The calculation retains the original evidence weights and derives historical weights from the actual juror counts:

```text
wH = 0.30 × n / (n + 2)
wM = 1 - wE - wH
prediction = wE × E + wH × H + wM × market_anchor
```

The proposed scenario uses `(raw_UP + normalized_UP) / 2` where `UP + DOWN < 0.98`.
It changes **13 of 98 forecasts**.

| Repository | Original | Correct midpoint forecast | Change |
|---|---:|---:|---:|
| alloy-rs/alloy | 0.800 | **0.835** | +0.035 |
| argotorg/fe | 0.766 | **0.794** | +0.028 |
| arkworks-rs/algebra | 0.829 | **0.854** | +0.025 |
| Cyfrin/aderyn | 0.668 | **0.683** | +0.015 |
| l2beat/l2beat | 0.741 | **0.758** | +0.017 |
| safe-global/safe-smart-account | 0.827 | **0.838** | +0.011 |

The supplied Fe value, 0.795, and Aderyn value, 0.684, do not reproduce the full-precision calculation.

### Public historical diagnostics

Lower sum of absolute errors, or SAE, is better.

| Scenario | Branch-active rows | Public SAE | SAE without direct history |
|---|---:|---:|---:|
| Original raw-UP blend | 0 | **2.277000** | **2.533666** |
| Midpoint where sum < 0.90 | 3 | 2.277000 | 2.533666 |
| Midpoint where sum < 0.95 | 7 | 2.277000 | 2.533666 |
| Proposed midpoint where sum < 0.98 | 13 | **2.282000** | **2.539666** |
| Full normalization where sum < 0.98 | 13 | 2.288000 | 2.545666 |
| Midpoint on every market | 98 | 2.289000 | 2.549666 |
| Full normalization on every market | 98 | 2.302000 | 2.567666 |

The proposed midpoint worsens public SAE by **0.005000**.
Blockscout is the only affected row with a public label. Its forecast rises from 0.696 to 0.701 against a 0.600 target.
All six highlighted markets lack public labels.
The unchanged SAE at lower thresholds therefore supplies no evidence of success on those markets.

**These are retrospective diagnostics, not held-out validation.**
The history-enabled forecasts directly use the public targets.
The history-free forecasts still use priors researched with those targets visible.
The small public deterioration does not prove that the patch will fail on Round 3.
It also does not support a claim that the patch improves accuracy.

The 0.98 threshold and 50% midpoint fraction remain uncalibrated choices.
Changing either choice changes the forecast policy. The threshold also introduces an abrupt branch change.

### Alias defect in the proposed patch

The original forecast gives both Web3j aliases the same anchor.
The proposed patch branches on each alias's own `price_sum`, even while using shared alias prices.
If only one sum crosses 0.98, the aliases can receive different predictions.

Current sums are 1.0000454698375847 and 0.9887970445723311. Neither currently crosses the threshold.
The defect is a future/counterfactual risk, not a current discrepancy.

A regression example uses sums 0.80 and 1.00:

| Policy | First alias anchor | Second alias anchor |
|---|---:|---:|
| Proposed per-row branch | 0.760 | 0.720 |
| Shared branch in the scenario implementation | 0.760 | 0.760 |

The implementation applies one threshold decision using the aliases' mean sum.
That preserves the alias invariant. It is a declared scenario convention, not an economically optimal policy.

## 4. The four repository claims

### ethereum-lists/chains: useful audit target, insufficient reason for the proposed cut

The repository primarily contains chain metadata. It is not only a set of JSON files.
Its reviewed [Kotlin processor](sources/registry/code/processor/src/main/kotlin/org/ethereum/lists/chains/Main.kt) validates entries and builds registry outputs.
Its [test suite](sources/registry/code/processor/src/test/kotlin/org/ethereum/lists/chains/TheChainChecker.kt) covers constraints and invalid entries.
The code uses dependencies including Klaxon, OkHttp, and kethereum. It does not constitute an executable blockchain protocol.

[EIP-155](https://eips.ethereum.org/EIPS/eip-155) links the registry.
The [EIP155 namespace document](https://namespaces.chainagnostic.org/eip155/caip2) describes operator-submitted chain identifiers and RPC information.
These sources corroborate the registry's role. They do not measure its originality.

The comparison with Chainlist overlooks an important dependency direction.
Chainlist's [reviewed fetch code](../sources/repositories/DefiLlama__chainlist/utils/fetch.js), lines 175–189, consumes `chainid.network/chains.json`.
It combines that upstream registry with RPC additions, overrides, and DefiLlama data.
An upstream registry and a downstream integration need not have equal originality.
Curated data also needs attribution analysis; its file format alone does not establish dependency reliance.

The claim that Chainlist was pulled up *only* by its single R1 rating is misleading.
Its history-free forecast is **0.660**, compared with **0.667** with history.
The R1 value adds about 0.007 to the final forecast, not the entire difference from its 0.59 prior.

The original 0.80 registry prior remains subjective and deserves closer attribution review.
This does not establish that 0.55–0.65 is the correct replacement.

| Alternative registry prior | Resulting forecast, unchanged market weight |
|---|---:|
| 0.55 | 0.681 |
| 0.60 | 0.698 |
| 0.65 | 0.716 |

**Assessment:** Investigate data provenance and evaluation scope. Do not lower the prior merely because the repository is data-heavy.

### Aestus: fork evidence supports caution, not an exact 0.35 prior

The saved [GitHub comparison](../sources/repositories/aestus-relay__mev-boost-relay/fork_comparison.json) confirms Flashbots ancestry.
It reports 147 commits ahead, 18 behind, and 26 changed files.
The listed changes contain 2,027 additions and 532 deletions, including tests, manifests, and configuration.
Those counts do not measure the fraction of original functionality.

The reviewed additions include:

- [Latency estimation](sources/aestus/code/services/api/latency.go), including timing headers, RTT estimates, and fallback logic.
- [MEV-commit integration](sources/aestus/code/mevcommitclient/mev_commit_client.go), including validator opt-in checks and builder-event handling.
- [Redis top-bid logic](sources/aestus/code/datastore/topbid.lua).

The code preserves the Flashbots relay and uses other dependencies, including Primev contract clients.
The comparison supports a fork-sensitive interpretation. It neither proves that all additions originated with Aestus nor validates E = 0.35.

The single R1 score is **0.89**, without an explanatory note. The original raw market anchor is **0.721096**.
The 0.515 forecast gives the 0.35 subjective prior a **0.60 weight**, despite the large historical conflict.
Keeping that prior but changing its weight to 0.50 produces 0.552; a 0.40 weight produces 0.590.
These are uncertainty illustrations, not alternative validated recommendations.

**Assessment:** Keep 0.515 as a clearly fork-sensitive scenario. Do not describe it as strongly validated or predict a competitive advantage.

### SP1: custom implementation is real; numerical uplift remains a judgment

The reviewed workspace is SP1 **6.10.0** at commit `749b0c63f226063c471a6238a94101f930c14a13`.
Current [SP1 documentation](https://docs.succinct.xyz/docs/sp1/introduction) describes V6 Hypercube, a multilinear proof system.
Its [proof-system guide](https://docs.succinct.xyz/docs/sp1/hypercube/) describes shard proofs, memory consistency, and recursion.
Its [precompile guide](https://docs.succinct.xyz/docs/sp1/optimizing-programs/precompiles) describes optimized circuits and patched cryptography crates.

The [SHA-256 AIR implementation](sources/sp1/code/crates/core/machine/src/syscall/precompiles/sha256/compress/air.rs) contains substantial constraint and memory logic.
The [prover manifest](sources/sp1/code/crates/prover/Cargo.toml) links internal execution, recursion, Hypercube, and SLOP components.
This is substantive implementation work, not merely an external prover wrapper.

However, SP1's [SLOP README](sources/sp1/code/slop/README.md) explicitly distinguishes:

- Thin re-exports of Plonky3 primitives, including AIR, FRI, matrix, symmetric, and Keccak AIR components.
- SP1-specific extensions to Plonky3 field, challenger, and commitment components.
- Its own implementations of polynomial protocols and data structures.

The [algebra manifest](sources/sp1/code/slop/crates/algebra/Cargo.toml) directly depends on `p3-field`.
The workspace pins `p3-*` dependencies to `=0.4.3-succinct`.
The documentation also credits established protocols. Original implementation does not mean invention of the underlying mathematics.

The original prior, **0.710**, and market, **0.711071**, are close. Their rounded agreement does not validate either value.
Miden and Plonky3 are not a numerical calibration set. Shared category membership does not require similar originality scores.

| Alternative SP1 prior | Resulting forecast |
|---|---:|
| 0.76 | 0.736 |
| 0.77 | 0.741 |
| 0.78 | 0.746 |

**Assessment:** A higher prior is a defensible subjective scenario if custom prover implementation receives more credit.
The reviewed evidence does not establish the proposed 0.76–0.78 interval as more accurate than 0.71.

### libp2p: the historical scope claim is supported

Both R1 records give **0.90**. Their [saved notes](../sources/dataset/r1_juror_ratings.csv), lines 39–40, explicitly discuss separate implementations.
One mentions Rust dependencies. The other discusses the networking protocol's contribution.
The [umbrella README](../sources/repositories/libp2p__libp2p/README.md) links implementation and specification repositories elsewhere.

This confirms that historical jurors assessed more than the literal umbrella repository.
It supports the broad scope behind the original **0.828** forecast.
It does not guarantee that Round 3 jurors will use that scope or repeat the 0.90 scores.

**Assessment:** Retain the broad-scope interpretation as a historically supported scenario. Keep the literal-repository scope caveat explicit.

## 5. Decision and reproducibility

No numerical revision is justified solely by this proposal.
Normalization remains a useful alternative, especially if Invalid allowance rather than pool dislocation explains a deficit.
The strongest repository follow-up is attribution and scope, not matching neighboring percentages.

The forecast has no measured Round 3 accuracy. Neither the original forecast nor these scenarios are certified originality assessments.

Files:

- [scenario_summary.csv](scenario_summary.csv): 20 scenarios, including history-free variants and threshold sensitivities.
- [scenario_forecasts.csv](scenario_forecasts.csv): all 98 rows for every scenario, with the actual anchor used.
- [deficit_markets.csv](deficit_markets.csv): all 13 markets below 0.98.
- [prior_scenarios.csv](prior_scenarios.csv): the six proposed prior alternatives and their forecast effects.
- [scenario_results.json](scenario_results.json): independent arithmetic checks, alias regression, and preserved-source hashes.
- [source_index.json](source_index.json), [tree_index.json](tree_index.json), [selected_source_index.json](selected_source_index.json), and [metadata_source_index.json](metadata_source_index.json): source provenance and failures.
- [payout_source_index.json](payout_source_index.json): provenance for the upstream Conditional Tokens payout implementation.

The scenario calculation independently verifies **1,966 rounded values** with Decimal arithmetic.
Every scenario has 98 canonical rows and passes the official parser.
Official SAE and independently calculated SAE agree for all 20 scenarios.
All **11 original artifact hashes** and **37 newly saved source hashes** match.
The combined offline test suite passes **35 tests**, including all 16 strict-audit checks.

Run the offline calculation from the project directory:

```powershell
python review_insight_scenarios.py
python -m unittest test_forecast test_strict_audit test_insight_review -v
```

These commands do not trade, submit, connect a wallet, or replace the original forecast.
The calculation writes only the separate scenario output files.

Web search was unavailable with HTTP 402. Direct official HTTP sources and pinned repository files supplied the research evidence.
One additional libp2p documentation request failed TLS hostname verification; it is recorded and excluded.
Repository and version cutoff uncertainty remains unresolved.
