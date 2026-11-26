# Strict audit of the Round 3 originality forecast

**Audit refreshed: November 26, 2026. Market snapshot: 09:00:23 UTC.**

The refreshed submission passes the technical checks. Its future accuracy remains unvalidated.
The market refresh changes 93 of 98 rounded forecasts; the original November 16 artifacts remain preserved.
The audit confirms several dependency claims, but it also identifies scope problems and gaps in independent evidence.
It does **not** certify any of the 98 originality percentages.

## Results and files

- [repository_crosscheck.csv](repository_crosscheck.csv): checks, evidence paths, limitations, and scope notes for all 98 rows.
- [audit_results.json](audit_results.json): machine-readable results for the 16 audit checks.
- [source_index.json](source_index.json), [followup_index.json](followup_index.json), and [final_source_index.json](final_source_index.json): additional source provenance and failed requests.
- [artifact_review_index.json](artifact_review_index.json): seven published packages and 20 selected manifest/code files.
- [baseline/sha256.json](baseline/sha256.json): hashes of the 11 preserved original artifacts.
- [Current submission](../submission.csv): regenerated with the November 26 market snapshot. The original submission and its generated inputs are retained in `baseline/`.

Read this report's scope corrections before using the [original report](../REPORT.md).

## 1. Technical checks

| Check | Result |
|---|---|
| Required rows, names, order, header, and finite values | All 98 pass |
| Web3j aliases | Both remain required; both equal 0.778 |
| Preserved November 16 artifacts | All 11 match their saved baseline hashes |
| Original downloaded source files | All 205 hashes match |
| Original per-repository citation records | All 184 hashes match across 98 rows |
| Additional downloaded sources | All 189 saved download hashes match |
| Fresh official dataset/rule files | Eight files exactly match the original copies |
| Upstream R1 ratings and notes | All 51 match after documented alias/case mapping |
| Published historical targets | All 33 match the means rounded to six decimals |
| Independent forecast arithmetic | All 490 rounded forecast/sensitivity values match |
| Current and prior market responses | All 392 UP/DOWN quotes pass token-orientation and tick checks |
| Published npm tarballs | All seven match registry SHA-1 and SRI hashes |
| Selected files inside tarballs | All 20 match their saved review copies |
| Official and independently calculated current public SAE | Both equal **2.009000** |

The historical target file rounds means to six decimals.
Solidity and Remix therefore differ slightly from their unrounded means.
The maximum difference is **0.000000333333**. This is expected rounding, not label corruption.

The independent calculation uses `Decimal`, not the forecast's blend function.
It also checks the historical weights, alias averaging, normalized prices, and sensitivity variants.

### Market orientation

The saved public client labels `wrappedTokens[1]` as UP and `wrappedTokens[0]` as DOWN.
Each pool must contain the relevant outcome token and that leaf market's collateral token.

```text
ratio = 1.0001 ** tick
outcome price = ratio       if token0 is the outcome token
outcome price = 1 / ratio   if token1 is the outcome token
```

The current and prior snapshots reproduce their quoted prices within **1.05 × 10⁻¹⁶** absolute error.
Their 98 leaf addresses match the official universe.
The saved client identifies parent market `0x37ab5cbeee3a32289430e5d38b914ec7f580fd87` and the v3 endpoint.

This verifies response consistency and client interpretation. It does not independently verify on-chain state or executable prices.
Token decimals were not retrieved through an independent blockchain RPC.
Volume remains collateral-denominated, not USD. Gross liquidity remains different from executable depth.

## 2. What the additional sources establish

The collection records **196 requests**, **189 successful downloads**, and **seven HTTP 404 responses**.
One HTTP-200 download contains the wrong document type and is excluded from reviewed audit evidence.
The saved provenance records the failures rather than treating them as evidence of absent functionality.

### Published packages

Registry metadata comes from publishers. Integrity checks establish matching bytes, not independent expert judgment.
The package sources were inspected without installation or execution.

| Package | Published version | Confirmed finding |
|---|---|---|
| `ethereum-cryptography` | 3.2.0 | Keccak calls noble-hashes; secp256k1 directly re-exports noble-curves. Noble/scure packages supply the cryptographic implementations. |
| `@chainsafe/bls` | 8.2.0 | Native key/signature code calls `@chainsafe/blst`; the WASM context calls `bls-eth-wasm`. Guards and initialization remain integration work. |
| `@tevm/vm` | 1.0.0-next.148 | The manifest depends on EthereumJS. Selected source adds event handling and VM actions. |
| `@tevm/node` | 1.0.0-next.148 | Node code composes TEVM components, state, transaction pools, receipts, and VM actions. |
| `hardhat-deploy` | 2.3.0 | Repository metadata points to Rocketh. The package requires Hardhat, Rocketh, and `@rocketh/node` peers. |
| `@shazow/whatsabi` | 0.30.0 | Source contains its own bytecode iteration/disassembly. ABI selector helpers also call `ox`. |
| `@safe-global/safe-smart-account` | 1.5.0 | Safe.sol contains substantial account authorization and transaction logic. Imports are relative, including vendored external SafeMath. |

These findings strengthen the dependency distinctions behind JS cryptography **0.378** and ChainSafe BLS **0.495**.
They do not establish that either percentage matches future jury opinion.
Safe and WhatsABI also illustrate why counting packages or imports is not an originality measurement.

### Outside technical and ecosystem sources

- [Ethereum client documentation](https://ethereum.org/en/developers/docs/nodes-and-clients/) corroborates client roles and Erigon's geth ancestry.
- [Ethereum framework documentation](https://ethereum.org/en/developers/docs/frameworks/) corroborates Foundry, Hardhat, Web3j, and Scaffold-ETH's integrated stack.
- [Ethereum language documentation](https://ethereum.org/en/developers/docs/smart-contracts/languages/) distinguishes compiler languages from Remix's IDE role.
- [Ethereum library documentation](https://ethereum.org/en/developers/docs/smart-contracts/libraries/) distinguishes ERC designs from contract implementations.
- [Trail of Bits report](sources/noble_trailofbits.pdf) and [Cure53 report](sources/noble_cure53.pdf) inspect bounded noble cryptographic implementations.
- [Galois BLST verification documentation](sources/blst_galois.md) states what its proofs cover and what they assume.

Ethereum documentation is outside the individual repository, but contributors can include project members.
Some pages also contain stale links or descriptions. These pages are corroboration, not independent originality ratings.
The auditor reports are externally authored commissioned assessments, not unconflicted originality evaluations.

## 3. Corrections and scope conflicts

| Repository / retained forecast | Strict finding | Interpretation |
|---|---|---|
| DAppNode / **0.646** | This repository contains ISO/build/install assets. Its [Compose file](sources/resolved/dappnode__DAppNode/docker-compose.yml) builds an installer. The README links separate core packages. | **Correct the original rationale:** the separate management application cannot automatically receive credit in this repository row. |
| TEVM / **0.607** | HEAD explicitly describes a breaking native migration. Published next.148 packages still use the earlier JavaScript stack. | Neither version independently implements all execution. The cutoff determines which architecture jurors assess. |
| libp2p / **0.858** | The umbrella repository links both implementations and specifications elsewhere. | R1 notes explicitly used implementation-level scope beyond the linked repository. A literal-repository interpretation is different. |
| TrueBlocks / **0.814** | The current [.gitmodules](sources/resolved/TrueBlocks__trueblocks-core/.gitmodules) points to separate chifra, SDK, and khedra repositories. | Same-project submodules are not automatically external dependencies. The credited code boundary is unresolved. |
| hardhat-deploy / **0.695** | Current published code lives in Rocketh; the official row retains the older name. | Do not mix historical standalone code and current package scope without identifying the evaluation version. |
| Aestus / **0.532** | Flashbots ancestry and original additions are both confirmed. R1 assigned **0.89**. | The large reduction remains a risky subjective judgment. Commit counts cannot validate it. |

The matrix also flags Ethstaker fork comparisons, powdr-legacy, the moved Steel component, Aderyn retirement, and the archived Lambda client.
Retirement, archival, and repository transfers do not independently justify numerical penalties.

### Moving HEAD

The audit pins **52 files from 24 repositories** to commit URLs.
Of those files, **51 match** the earlier saved files.
Reth's Cargo.toml adds two references to an internal `version-build` module.
The change does not alter the original Alloy/evm2 dependency finding.
The other repositories were not all refreshed or commit-pinned; their saved hashes establish local integrity only.

### Audit-report limits

The old NCC blst URL redirects to generic NCC HTML despite HTTP 200.
The saved [response](sources/blst_ncc.pdf) is not a PDF. It is not counted as a reviewed security report.

Trail of Bits reviewed noble-curves at commit `7262b4219f8428dfa39ac4c81b25660ddc6a4614` in early 2023.
Cure53's 2024 assessment includes noble-curves **1.5.0** and other scoped packages.
Neither report certifies the current noble-curves **2.4.0** release.

Galois documents older code, fixed input sizes, unproved assumptions, and incomplete general coverage.
Its scalar-multiplication discussion distinguishes checked smaller exponents from extrapolation to 255 bits.
Its documentation does not establish complete formal verification of current blst.
This audit reads the proof documentation; it does not rerun those proofs.

Security assessment, formal correctness, and originality are different properties.

## 4. Coverage across all 98 rows

| Evidence coverage | Rows |
|---|---:|
| Original assessment cited only a README | 35 |
| Now has selected manifest/build/config/code evidence beyond a README | 95 |
| Has additional package-registry metadata | 19 |
| Has selected files inspected from a published package | 6 |
| Has limited outside role/implementation corroboration | 23 |
| Has no such independent corroboration collected | **75** |
| Has a specific scope or historical-conflict flag | 11 |
| Has an independently validated originality percentage | **0** |

The 95-row count is evidence availability, **not** 95 exhaustive code audits.
The three rows without selected technical files are the two Web3j aliases and the libp2p umbrella row.
The six package-backed rows correspond to seven tarballs because TEVM has two inspected packages.
Coverage figures overlap and must not be added together.

The matrix separates repository evidence, publisher metadata, historical labels, and limited outside corroboration.
The shared official market feed is not counted as an independent technical review of every repository.

## 5. Predictive-method audit

The public SAE values reproduce correctly:

| Method | Visible R1 SAE |
|---|---:|
| November 16 raw UP prices | 2.465020099 |
| November 26 raw UP prices | **1.741816173** |
| November 26 normalized UP prices | 1.736881873 |
| Subjective evidence priors | 2.880000 |
| November 26 blend, with direct public-history use | **2.009000** |
| November 26 blend without direct history | 2.191000 |

The lower blended error is **not held-out evidence**.
Known public targets influence the original forecast directly.
External-data and public-label use is allowed; the problem concerns the interpretation of performance, not rule compliance.
Copying public targets could produce zero public error without demonstrating future prediction skill.

These refreshed calculations still use public historical targets and are not held-out results.
They do not establish that the subjective adjustments improve future accuracy or prove that raw markets will win.

Additional limitations remain:

- Evidence priors and weights have no measured calibration.
- Public history, market prices, and repository assessments are correlated inputs.
- Scenario bounds have no tested probability coverage.
- Three-decimal output precision does not imply three-decimal prediction accuracy.
- Absolute-error loss favors a predictive median, not necessarily this weighted average.
- A clear repository/version cutoff and exact final evaluation coverage are unavailable.
- New Round 3 jury targets do not exist, so future error and rank cannot be validated.

## 6. Numerical revision decision

**The forecast was recalculated from the November 26 market snapshot fetched at 09:00:23 UTC.**
Compared with the original November 16 11:10:32 UTC quote input, mean absolute UP movement is **0.037057**, median movement is **0.028521**, and 93 rounded forecast rows change.
The largest rounded forecast moves are Ethereum JS Cryptography (**0.293 → 0.378**), WhatsABI (**0.835 → 0.770**), Act (**0.754 → 0.807**), Solady (**0.755 → 0.807**), and Fe (**0.766 → 0.818**).
The largest raw market moves are Ethereum JS Cryptography (**+0.212731**) and WhatsABI (**−0.130291**).

The Reth change is immaterial to the dependency assessment.
The package checks reinforce several existing technical claims without validating their numerical priors.
The scope findings require different evaluation interpretations; they do not supply a uniquely defensible replacement percentage.

The DAppNode rationale needs correction, and the scope-sensitive rows should not be treated as audited numerical recommendations.
The refreshed values remain hypotheses rather than validated results.
A later revision should state the credited repository boundary, evaluation version, changed prior, and sensitivity explicitly.
Replacing one arbitrary number with another would not resolve the evidence gap.

## 7. Reproduction

From the project directory, run:

```powershell
python strict_audit.py
python -m unittest test_forecast.py test_strict_audit.py -v
```

The first command reads saved evidence and writes only the new audit JSON and matrix.
It does not refresh sources or overwrite the forecast.
The tests include rejection checks for wrong market addresses, wrong outcome tokens, and altered prices.
No package installation, wallet connection, trading, submission, or publication is required.

Web search was unavailable with HTTP 402. Direct official, repository, registry, and auditor sources remained accessible.
The saved evidence and explicit coverage gaps define the audit's research limits.
