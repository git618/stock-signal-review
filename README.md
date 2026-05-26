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
- `--db`: SQLite database path
- `--benchmark`: benchmark ticker
- `--review-horizon-days`: minimum holding period before a recommendation is considered reviewable
- `--csv`: write per-row weekly review results to CSV while still printing the summary or empty-state message

### `list_recommendations.py`

```bash
python scripts/list_recommendations.py \
  --db data/stock_research.db \
  --limit 10
```

Options:
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
- `--tickers`: ticker list, either space-separated or comma-separated
- `--benchmark`: benchmark ticker
- `--start-date`: backtest start date
- `--end-date`: backtest end date
- `--holding-days`: forward holding period used for return measurement
- `--top-n`: number of recommendations selected on each recommendation date
- `--summary-only`: print only the summary block
- `--max-rows`: cap the number of detailed result rows printed
- `--csv`: write backtest rows to CSV

Backtest CSV export notes:
- writes detailed backtest rows to CSV
- `--summary-only` affects terminal output only
- CSV still includes the detailed result rows even when `--summary-only` is used

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
- Weekly review only works once recommendations are mature enough
- Free market data can fail, be delayed, or return incomplete data
- Backtest uses historical daily data and the current scoring rules; it is for research only and does not prove future profitability
- Generated CSV files under `data/*.csv` are local outputs and are ignored by Git

## Development Workflow

- TDD first
- Add failing tests before implementation
- Keep scripts small and explicit
- Avoid unnecessary dependencies
