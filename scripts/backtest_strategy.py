"""Run a simple historical backtest for the current strategy."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest import run_backtest


DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
DEFAULT_BENCHMARK = "SPY"


def main(argv=None):
    args = _parse_args(argv)
    result = run_backtest(
        tickers=_normalize_tickers(args.tickers),
        benchmark_ticker=args.benchmark,
        start_date=args.start_date,
        end_date=args.end_date,
        holding_days=args.holding_days,
        top_n=args.top_n,
    )

    summary = result["summary"]
    print(f"tested_count={summary.get('tested_count')}")
    print(f"win_rate={summary.get('win_rate')}")
    print(f"average_return={summary.get('average_return')}")
    print(f"average_benchmark_return={summary.get('average_benchmark_return')}")
    print(f"average_excess_return={summary.get('average_excess_return')}")
    print(f"best_ticker={summary.get('best_ticker')}")
    print(f"worst_ticker={summary.get('worst_ticker')}")
    print()

    if args.summary_only:
        return 0

    rows = result["rows"]
    if args.max_rows is not None:
        rows = rows[: args.max_rows]

    for row in rows:
        print(f"recommendation_date={row['recommendation_date']}")
        print(f"exit_date={row['exit_date']}")
        print(f"ticker={row['ticker']}")
        print(f"entry_price={row['entry_price']}")
        print(f"exit_price={row['exit_price']}")
        print(f"return_pct={row['return_pct']}")
        print(f"benchmark_return_pct={row['benchmark_return_pct']}")
        print(f"excess_return_pct={row['excess_return_pct']}")
        print(f"is_win={row['is_win']}")
        print()

    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--holding-days", type=int, default=5)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--max-rows", type=int)
    return parser.parse_known_args(argv)[0]


def _normalize_tickers(raw_tickers):
    if len(raw_tickers) == 1 and "," in raw_tickers[0]:
        return [ticker.strip() for ticker in raw_tickers[0].split(",") if ticker.strip()]
    return raw_tickers


if __name__ == "__main__":
    main()
