# Changelog

## v1.0.0

- Final release polish for a stable local research workflow.
- Added release-oriented documentation, changelog coverage, and validation checklist.
- Consolidated the project as a documented, tested stock signal research MVP with CI.

## v0.9.0

- Added GitHub Actions CI for `python -m pytest -q` on push and pull requests.
- Fixed clean-checkout database initialization by creating parent directories automatically.
- Strengthened test coverage for workflow config and reset-database behavior.

## v0.8.0

- Added `scripts/generate_report.py` for a local static HTML report.
- Combined recommendations, weekly review, backtest, and strategy comparison into one report.
- Ignored generated `data/*.html` outputs in Git.

## v0.7.0

- Added filtering to `scripts/compare_strategies.py`.
- Supported `--top`, `--hide-zero-results`, and `--min-tested-count`.
- Preserved CSV export with filtered and sorted output.

## v0.6.0

- Added sorting to `scripts/compare_strategies.py`.
- Supported `--sort-by` and `--descending`.
- Added best-strategy summary output after sorted comparisons.

## v0.5.0

- Added multi-strategy comparison with `scripts/compare_strategies.py`.
- Added example strategy configs for momentum and low-volatility research presets.
- Added CSV export for strategy comparison summaries.

## v0.4.0

- Made strategy version and weights configurable from JSON config.
- Wired configurable strategy settings into daily recommendations and backtests.
- Documented research-only strategy tuning behavior.

## v0.3.0

- Added JSON config-file support with `config/default.json`.
- Added config precedence rules across daily, weekly, backtest, and listing scripts.
- Allowed config-driven backtest defaults and derived fallback dates.

## v0.2.0

- Switched review and backtest exits from calendar days to trading-day logic.
- Added richer backtest summary metrics including medians and best/worst returns.
- Documented trading-day holding periods and backtest summary behavior.

## v0.1.0

- Established the initial local stock signal research workflow.
- Added SQLite persistence, daily recommendations, listing, weekly review, and reset tooling.
- Added backtesting, CSV export, HTML-free terminal workflows, and Makefile automation.
