"""Run a simple historical backtest for the current strategy."""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.backtest import run_backtest


def main(argv=None):
    args = _parse_args(argv)
    config = load_config(args.config)
    start_date, end_date = _resolve_backtest_dates(args, config)
    result = run_backtest(
        tickers=_normalize_tickers(args.tickers) if args.tickers is not None else config["tickers"],
        benchmark_ticker=args.benchmark if args.benchmark is not None else config["benchmark"],
        start_date=start_date,
        end_date=end_date,
        holding_days=args.holding_days if args.holding_days is not None else config["holding_days"],
        top_n=args.top_n if args.top_n is not None else config["top_n"],
    )

    if args.csv:
        csv_path = Path(args.csv)
        _write_csv(csv_path, result["rows"])
        print(f"Wrote CSV: {csv_path}")

    summary = result["summary"]
    print(f"tested_count={summary.get('tested_count')}")
    print(f"win_count={summary.get('win_count')}")
    print(f"loss_count={summary.get('loss_count')}")
    print(f"win_rate={summary.get('win_rate')}")
    print(f"average_return={summary.get('average_return')}")
    print(f"average_benchmark_return={summary.get('average_benchmark_return')}")
    print(f"average_excess_return={summary.get('average_excess_return')}")
    print(f"median_return={summary.get('median_return')}")
    print(f"median_excess_return={summary.get('median_excess_return')}")
    print(f"best_ticker={summary.get('best_ticker')}")
    print(f"worst_ticker={summary.get('worst_ticker')}")
    print(f"best_return={summary.get('best_return')}")
    print(f"worst_return={summary.get('worst_return')}")
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
    parser.add_argument("--config")
    parser.add_argument("--tickers", nargs="+")
    parser.add_argument("--benchmark")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--holding-days", type=int)
    parser.add_argument("--top-n", type=int)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--csv")
    return parser.parse_known_args(argv)[0]


def _normalize_tickers(raw_tickers):
    if len(raw_tickers) == 1 and "," in raw_tickers[0]:
        return [ticker.strip() for ticker in raw_tickers[0].split(",") if ticker.strip()]
    return raw_tickers


def _resolve_backtest_dates(args, config):
    if args.start_date is not None and args.end_date is not None:
        return args.start_date, args.end_date
    if args.start_date is not None or args.end_date is not None:
        today = date.today()
        lookback_days = config["lookback_days"]
        start_date = args.start_date if args.start_date is not None else (today - timedelta(days=lookback_days)).isoformat()
        end_date = args.end_date if args.end_date is not None else today.isoformat()
        return start_date, end_date

    config_start = config.get("backtest_start_date")
    config_end = config.get("backtest_end_date")
    if config_start is not None and config_end is not None:
        return config_start, config_end

    today = date.today()
    lookback_days = config["lookback_days"]
    return (today - timedelta(days=lookback_days)).isoformat(), today.isoformat()


def _write_csv(csv_path, rows):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "recommendation_date",
        "exit_date",
        "ticker",
        "entry_price",
        "exit_price",
        "return_pct",
        "benchmark_return_pct",
        "excess_return_pct",
        "is_win",
    ]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
