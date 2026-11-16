---
license: mit
pretty_name: "Deep Funding Originality: Round 3"
configs:
- config_name: repos
  data_files: repos.csv
- config_name: sample_submission
  data_files: sample_submission.csv
- config_name: r1_juror_ratings
  data_files: r1_juror_ratings.csv
- config_name: public_leaderboard_targets
  data_files: public_leaderboard_targets.csv
- config_name: market_prices
  data_files: market_prices.csv
---

# Deep Funding Originality: Round 3: data

All files are in the dataset [DeepFunding/originality-r3-data](https://huggingface.co/datasets/DeepFunding/originality-r3-data), which is linked from the competition [Deep Funding Originality: Round 3](https://huggingface.co/spaces/DeepFunding/PredictiveFundingChallengeforOpenSourceDependencies).

| File | Rows | What it holds |
|---|---|---|
| `repos.csv` | 98 | The competition repositories, spelled as the markets spell them, with GitHub URL, market bundle and Seer market. |
| `sample_submission.csv` | 98 | A correctly formatted submission. Every value is 0.5: a format example, not a forecast. |
| `r1_juror_ratings.csv` | 51 | Every juror rating from Deep Funding's first originality round (Originality R1): repository, the name the juror used, the 0–100 rating and the juror's note, if any. |
| `public_leaderboard_targets.csv` | 33 | The public leaderboard's answers: each R1-rated repository's average rating divided by 100, with the number of ratings. |
| `market_prices.csv` | 98 | UP and DOWN prices of each repository's Round 3 originality market on deep.seer.pm at 2026-10-16 10:55 UTC. |
| `metric.py` | | The leaderboard's scorer. Run it to check a submission and score it against the public targets. |

## Notes

- Originality R1 used two older names, mapped here onto the market names: `ethereum/solidity` → `argotorg/solidity` (the repository moved) and `account-abstraction` → `eth-infinitism/account-abstraction`.
- Each Round 3 market pays UP in proportion to the repository's final average originality, so the UP price is the market's estimate of it. Prices are in units of the market's repo token. UP and DOWN trade in separate pools, and part of the value sits in the market's Invalid outcome, so UP + DOWN is not exactly 1 (0.85 to 1.05 in this snapshot); `up_share` = UP / (UP + DOWN) rescales the pair to sum to 1. Live prices are on [deep.seer.pm](https://deep.seer.pm).
- The private leaderboard's answers are the Round 3 jurors' averages. They are not here because they do not exist yet.

## License

`r1_juror_ratings.csv` and `public_leaderboard_targets.csv` come from [deepfunding/oss-evals](https://github.com/deepfunding/oss-evals) (MIT License, © 2026 Deep Funding). The full license text is in `LICENSE`.
