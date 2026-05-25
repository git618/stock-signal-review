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

### `list_recommendations.py`

```bash
python scripts/list_recommendations.py \
  --db data/stock_research.db \
  --limit 10
```

Options:
- `--db`: SQLite database path
- `--limit`: number of rows to display

### `reset_database.py`

```bash
python scripts/reset_database.py --db data/stock_research.db
```

Options:
- `--db`: SQLite database path to delete and recreate

## Current Limitations

- Uses `yfinance` and daily historical data only
- No real-time trading
- No broker integration
- No profit guarantees
- Weekly review only works once recommendations are mature enough
- Free market data can fail, be delayed, or return incomplete data

## Development Workflow

- TDD first
- Add failing tests before implementation
- Keep scripts small and explicit
- Avoid unnecessary dependencies
