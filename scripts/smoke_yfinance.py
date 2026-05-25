"""Manual smoke test for yfinance market-data fetching."""

from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.market_data import YFinanceMarketDataProvider


def main():
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    provider = YFinanceMarketDataProvider()
    tickers = ["AAPL", "MSFT", "SPY"]
    any_missing = False

    for ticker in tickers:
        rows = provider.fetch_daily_prices(
            ticker,
            start_date.isoformat(),
            end_date.isoformat(),
        )
        print(f"{ticker}: rows={len(rows)}")
        if not rows:
            any_missing = True
            continue
        print(f"{ticker}: last_close={rows[-1]['close']}")

    if any_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
