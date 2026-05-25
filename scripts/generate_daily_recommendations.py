"""Generate and persist daily stock recommendations."""

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendations import generate_daily_recommendations


DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
DEFAULT_BENCHMARK = "SPY"
DEFAULT_DB_PATH = Path("data/stock_research.db")


def main(argv=None):
    args = _parse_args(argv)
    end_date = date.today()
    start_date = end_date - timedelta(days=args.lookback_days)

    recommendations = generate_daily_recommendations(
        tickers=_normalize_tickers(args.tickers),
        benchmark_ticker=args.benchmark,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        db_path=Path(args.db),
    )

    for recommendation in recommendations:
        print(f"rank={recommendation['rank']}")
        print(f"ticker={recommendation['ticker']}")
        print(f"score={recommendation['score']}")
        print(f"entry_price={recommendation['entry_price']}")
        print(f"strategy_version={recommendation['strategy_version']}")
        print(f"reasons={recommendation['reasons']}")
        print(f"risk_notes={recommendation['risk_notes']}")
        print()

    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK)
    parser.add_argument("--lookback-days", type=int, default=90)
    return parser.parse_known_args(argv)[0]


def _normalize_tickers(raw_tickers):
    if len(raw_tickers) == 1 and "," in raw_tickers[0]:
        return [ticker.strip() for ticker in raw_tickers[0].split(",") if ticker.strip()]
    return raw_tickers


if __name__ == "__main__":
    main()
