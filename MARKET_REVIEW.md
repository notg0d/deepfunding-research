# Current market review

**Checked: November 26, 2026 at 09:00:23 UTC (14:30:23 IST).**

The current submission now uses the official Seer Round 3 quote feed fetched at that time. The feed returned all 98 expected markets; every market ID matched the official repository universe, each market was open, and all 196 UP/DOWN quotes passed the saved token-orientation and tick-price checks. The raw response and fetch metadata are saved in [`sources/market/live_markets.json`](sources/market/live_markets.json) and its provenance sidecar. [Official Seer market feed](https://deep.seer.pm/.netlify/functions/get-originality-r3-v3-markets-data)

## What changed

Compared with the original November 16, 2026 11:10:32 UTC forecast input, absolute UP-price movement averaged **0.037057** and had a **0.028521** median. The largest increases were Ethereum JS Cryptography (**+0.212731**), EIPs (**+0.098733**), Act (**+0.096306**), and ChainSafe BLS (**+0.096116**). The largest decreases were WhatsABI (**−0.130291**) and Checkpointz (**−0.072515**).

Reapplying the existing blend formula with current raw UP quotes, while keeping the same evidence priors, evidence weights, and historical-rating inputs, changes **93 of 98** rounded forecast values.

| Repository | Previous | Refreshed | Change |
|---|---:|---:|---:|
| `ethereum/js-ethereum-cryptography` | 0.293 | 0.378 | +0.085 |
| `shazow/whatsabi` | 0.835 | 0.770 | −0.065 |
| `argotorg/act` | 0.754 | 0.807 | +0.053 |
| `Vectorized/solady` | 0.755 | 0.807 | +0.052 |
| `argotorg/fe` | 0.766 | 0.818 | +0.052 |
| `ethstaker/eth-docker` | 0.533 | 0.578 | +0.045 |
| `ethereum/py_ecc` | 0.767 | 0.811 | +0.044 |
| `ethstaker/ethstaker-deposit-cli` | 0.610 | 0.653 | +0.043 |

The current submission still has the official `repo,originality` format, 98 repositories in official order, values in `[0,1]`, and identical forecasts for the two Web3j aliases. The original November 16 submission and generated files remain archived in [`strict_audit/baseline/`](strict_audit/baseline/).

## Current snapshot diagnostics

The current mean raw UP quote is **0.756861**. UP + DOWN ranges from **0.985060 to 1.059781**. The market feeds provide marginal pool quotes; they do not establish executable depth or guarantee trade prices. The chart feed has 98 leaf-market records ending at **08:30 UTC on November 26**. The largest recorded seven-day movements were JS Ethereum Cryptography (**+0.212367**) and WhatsABI (**−0.129830**). Volume and liquidity remain denominated in separate repository collateral tokens, not USD.

Against the 33 public Originality R1 averages, the current raw UP quotes have an SAE of **1.741816**, normalized UP has **1.736882**, and the refreshed blend scores **2.009000**. The previous blend scored **2.277000** on those same targets. These are retrospective comparisons using public labels already visible to the research; they are not held-out tests. Round 3 jury averages remain unavailable, so the refresh does not verify future accuracy. The official competition page was still marked **Running** when checked. [Competition page](https://huggingface.co/spaces/DeepFunding/PredictiveFundingChallengeforOpenSourceDependencies)

The evidence priors were not recalibrated during this market refresh. Rows with unresolved repository boundaries or disagreement with historical jury ratings remain judgment-sensitive; see the [strict audit](strict_audit/AUDIT_REPORT.md).
