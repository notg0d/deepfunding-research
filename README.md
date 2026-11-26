# Deep Funding research

This project researches and forecasts originality ratings for the 98 repositories in Deep Funding Originality Round 3. The current `submission.csv` was regenerated from the official Seer market snapshot fetched on November 26, 2026 at 09:00:23 UTC. It combines the raw UP quote with a subjective repository-evidence prior and available public Round 1 ratings. The new Round 3 jury scores are not available, so its predictive accuracy is unknown.

Start with the [research report](REPORT.md), the [current market review](MARKET_REVIEW.md), and the [strict audit](strict_audit/AUDIT_REPORT.md). `submission.csv` is the file in the competition's `repo,originality` format. `repository_forecasts.md` and `forecast_details.csv` show the repository estimates and calculation inputs. The original November 16 forecast artifacts are retained in `strict_audit/baseline/`.

To rebuild the generated forecast files using the saved market and repository evidence, run from the project directory:

```powershell
python build_forecast.py
python -m unittest test_forecast.py test_strict_audit.py test_insight_review.py -v
python sources/dataset/metric.py submission.csv --solution sources/dataset/public_leaderboard_targets.csv
```

`build_forecast.py` uses saved files and does not fetch markets, submit a forecast, or trade. To refresh the market input first, run `python collect_sources.py markets`, followed by `python analyze_data.py` and `python build_forecast.py`. Recheck `MARKET_REVIEW.md` and the source timestamps after any refresh.

Forecast weights and evidence priors are manually set and uncalibrated. Public Round 1 error figures are retrospective and use visible labels; they do not establish accuracy for Round 3. Market quotes are marginal prices, not guaranteed executable prices.
