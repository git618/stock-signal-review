# Stock Signal Review

Stock Signal Review is a stock research and review system for generating explainable daily recommendations and reviewing them later against a benchmark. It is not an automated trading system, does not place trades, and does not guarantee profits.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Tests

```bash
python -m pytest -q
```

## Common Commands

```bash
make test
make reset
make daily
make list
make weekly
make backtest
make smoke
```

What each command does:
- `make test`: run the full test suite with the project virtualenv
- `make reset`: clear and recreate the local SQLite database
- `make daily`: generate and save daily recommendations
- `make list`: print saved recommendations from SQLite
- `make weekly`: review mature recommendations against the benchmark
- `make backtest`: run the built-in backtest command with compact summary output
- `make smoke`: run the manual market-data smoke check

## MVP Workflow

Run the scripts from the project root in this order:

```bash
python scripts/reset_database.py
python scripts/generate_daily_recommendations.py
python scripts/list_recommendations.py
python scripts/generate_weekly_review.py
```

What each step does:
- `reset_database.py` clears and recreates the local SQLite database.
- `generate_daily_recommendations.py` fetches daily market data, calculates features, scores stocks, and saves the top recommendations.
- `list_recommendations.py` shows saved recommendations from SQLite.
- `generate_weekly_review.py` reviews mature recommendations against the benchmark.

## Configuration

Default research settings live in [config/default.json](/home/king/stock-signal-review/config/default.json).

Current keys:
- `tickers`
- `benchmark`
- `lookback_days`
- `holding_days`
- `top_n`
- `review_horizon_days`
- `database_path`
- `backtest_start_date`
- `backtest_end_date`
- `strategy.version`
- `strategy.weights`

Strategy config example:

```json
{
  "strategy": {
    "version": "v1",
    "weights": {
      "return_20d": 0.4,
      "return_5d": 0.2,
      "volume_ratio_20d": 0.2,
      "volatility_20d": -0.2
    }
  }
}
```

Strategy notes:
- `strategy.version` is stored with recommendations and backtest outputs for comparison across rule sets.
- `strategy.weights` controls the weighted scoring inputs used by daily recommendations and backtests.
- Missing strategy config falls back to the built-in research defaults.
- Strategy tuning is for research only. Changing weights does not guarantee profits or future outperformance.

Example:

```bash
python scripts/generate_daily_recommendations.py --config config/default.json
python scripts/generate_weekly_review.py --config config/default.json
python scripts/backtest_strategy.py --config config/default.json --start-date 2026-02-24 --end-date 2026-05-25
```

Precedence:
- CLI arguments override config file values.
- Config file values override built-in defaults.

Backtest date precedence:
- `--start-date` and `--end-date` override config values.
- `backtest_start_date` and `backtest_end_date` from config are used when CLI dates are omitted.
- If neither CLI nor config provides backtest dates, the script derives:
  - `end_date = today`
  - `start_date = today - lookback_days`

Example override:

```bash
python scripts/backtest_strategy.py \
  --config config/default.json \
  --start-date 2026-02-24 \
  --end-date 2026-05-25 \
  --top-n 2
```

Multi-strategy comparison:
- Use [config/default.json](/home/king/stock-signal-review/config/default.json), [config/momentum.json](/home/king/stock-signal-review/config/momentum.json), and [config/low_volatility.json](/home/king/stock-signal-review/config/low_volatility.json) as comparable research presets.
- `scripts/compare_strategies.py` runs one backtest per config and prints one summary row per strategy.
- Optional CSV export writes the same summary columns to a local file.
- `--sort-by` sorts strategy rows by a supported summary metric.
- `--descending` puts higher metric values first.
- `--top` limits the number of displayed and exported strategy rows after filtering and sorting.
- `--hide-zero-results` removes rows where `tested_count` is `0`.
- `--min-tested-count` removes rows below a minimum tested count.
- When sorted, the script prints a best-strategy summary after the table.

Example:

```bash
python scripts/compare_strategies.py \
  --configs config/default.json config/momentum.json config/low_volatility.json \
  --sort-by average_excess_return \
  --descending \
  --top 1 \
  --min-tested-count 50 \
  --csv data/strategy_comparison.csv
```

Filtering order:
- compute all strategy summaries
- apply `--hide-zero-results`
- apply `--min-tested-count`
- apply `--sort-by` and `--descending`
- apply `--top`

If no rows remain after filtering, the script prints:

```text
No strategy results to display.
```

CSV export writes only the filtered, sorted, top-limited rows. It still writes the header row when no rows remain.

Supported sort metrics:
- `tested_count`
- `win_rate`
- `average_return`
- `average_benchmark_return`
- `average_excess_return`
- `median_return`
- `median_excess_return`
- `best_return`
- `worst_return`

Best-strategy summary fields:
- `best_config`
- `best_strategy`
- `best_metric`
- `best_value`

Best-strategy output is omitted when no rows remain after filtering.

Comparison output fields:
- `config`
- `strategy_version`
- `tested_count`
- `win_count`
- `loss_count`
- `win_rate`
- `average_return`
- `average_benchmark_return`
- `average_excess_return`
- `median_return`
- `median_excess_return`
- `best_ticker`
- `worst_ticker`
- `best_return`
- `worst_return`

## CLI Options

### `generate_daily_recommendations.py`

```bash
python scripts/generate_daily_recommendations.py \
  --db data/stock_research.db \
  --tickers AAPL MSFT NVDA \
  --benchmark SPY \
  --lookback-days 90
```

Options:
- `--config`: JSON config path, defaults to `config/default.json`
- `--db`: SQLite database path
- `--tickers`: ticker list, either space-separated or comma-separated
- `--benchmark`: benchmark ticker used for later review workflows
- `--lookback-days`: historical lookback window for feature generation

### `generate_weekly_review.py`

```bash
python scripts/generate_weekly_review.py \
  --db data/stock_research.db \
  --benchmark SPY \
  --review-horizon-days 5
```

Options:
- `--config`: JSON config path, defaults to `config/default.json`
- `--db`: SQLite database path
- `--benchmark`: benchmark ticker
- `--review-horizon-days`: minimum holding period in trading days before a recommendation is considered reviewable
- `--csv`: write per-row weekly review results to CSV while still printing the summary or empty-state message

Trading-day review notes:
- Weekly review uses trading-day exit dates from the available price rows where applicable.
- Weekends and non-trading days are skipped automatically because they do not appear in the fetched rows.
- If there are not enough future trading days available, that review row is skipped gracefully.

### `list_recommendations.py`

```bash
python scripts/list_recommendations.py \
  --db data/stock_research.db \
  --limit 10
```

Options:
- `--config`: optional JSON config path for database defaults
- `--db`: SQLite database path
- `--limit`: number of rows to display
- `--csv`: write listed recommendations to CSV

CSV export example:

```bash
python scripts/list_recommendations.py --csv data/recommendations.csv
```

The exported CSV includes:
- `trading_date`
- `rank`
- `symbol`
- `score`
- `entry_price`
- `strategy_version`

### `reset_database.py`

```bash
python scripts/reset_database.py --db data/stock_research.db
```

Options:
- `--db`: SQLite database path to delete and recreate

### `backtest_strategy.py`

```bash
python scripts/backtest_strategy.py \
  --tickers AAPL MSFT NVDA \
  --benchmark SPY \
  --start-date 2026-02-24 \
  --end-date 2026-05-25 \
  --holding-days 5 \
  --top-n 2
```

Compact output example:

```bash
python scripts/backtest_strategy.py \
  --tickers AAPL MSFT NVDA \
  --benchmark SPY \
  --start-date 2026-02-24 \
  --end-date 2026-05-25 \
  --holding-days 5 \
  --top-n 2 \
  --summary-only
```

CSV export example:

```bash
python scripts/backtest_strategy.py \
  --tickers AAPL MSFT NVDA \
  --benchmark SPY \
  --start-date 2026-02-24 \
  --end-date 2026-05-25 \
  --holding-days 5 \
  --top-n 2 \
  --summary-only \
  --csv data/backtest.csv
```

Options:
- `--config`: JSON config path, defaults to `config/default.json`
- `--tickers`: ticker list, either space-separated or comma-separated
- `--benchmark`: benchmark ticker
- `--start-date`: backtest start date
- `--end-date`: backtest end date
- `--holding-days`: forward holding period in trading days used for return measurement
- `--top-n`: number of recommendations selected on each recommendation date
- `--summary-only`: print only the summary block
- `--max-rows`: cap the number of detailed result rows printed
- `--csv`: write backtest rows to CSV

Backtest summary output:
- Summary metrics are printed to stdout.
- The summary includes:
  - `tested_count`
  - `win_count`
  - `loss_count`
  - `win_rate`
  - `average_return`
  - `average_benchmark_return`
  - `average_excess_return`
  - `median_return`
  - `median_excess_return`
  - `best_ticker`
  - `worst_ticker`
  - `best_return`
  - `worst_return`
- Empty backtests return zero-value summary metrics and `None` for ticker fields instead of failing.

Backtest CSV export notes:
- CSV export remains row-level only
- writes detailed backtest rows to CSV
- `--summary-only` affects terminal output only
- CSV still includes the detailed result rows even when `--summary-only` is used

Trading-day backtest notes:
- Backtest holding periods use available trading days from the price data, not calendar days.
- `--holding-days` means trading days. For example, `--holding-days 5` means the fifth future trading day after the recommendation date.
- Weekends and non-trading gaps are skipped automatically because they do not appear in the price rows.
- If there are not enough future trading days available, that backtest row is skipped gracefully.

Weekly review CSV export example:

```bash
python scripts/generate_weekly_review.py --csv data/weekly_review.csv
```

The weekly review CSV includes:
- `ticker`
- `entry_price`
- `exit_price`
- `return_pct`
- `benchmark_return_pct`
- `excess_return_pct`
- `is_win`

## Current Limitations

- Uses `yfinance` and daily historical data only
- No real-time trading
- No broker integration
- No profit guarantees
- Weekly review only works once recommendations are mature enough in trading-day terms
- Free market data can fail, be delayed, or return incomplete data
- Backtest uses historical daily data and the current scoring rules; it is for research only and does not prove future profitability
- Generated CSV files under `data/*.csv` are local outputs and are ignored by Git

## v0.1 Status

What works:
- local SQLite-backed recommendation storage
- daily recommendation generation
- recommendation listing
- weekly review with maturity filtering
- historical backtest workflow
- CSV export for research outputs
- Makefile shortcuts for common workflows

Operational notes:
- this project is local-only and intended for research workflows
- it does not execute trades
- it does not integrate with a broker
- market data comes from `yfinance` and other free data paths can fail, be delayed, or return incomplete results

## Development Workflow

- TDD first
- Add failing tests before implementation
- Keep scripts small and explicit
- Avoid unnecessary dependencies
