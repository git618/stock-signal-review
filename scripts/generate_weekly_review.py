"""Generate a weekly review of saved recommendations."""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.review import generate_weekly_review


def main(argv=None):
    args = _parse_args(argv)
    config = load_config(args.config)
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    review_kwargs = {
        "db_path": Path(args.db if args.db is not None else config["database_path"]),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "benchmark_ticker": args.benchmark if args.benchmark is not None else config["benchmark"],
    }
    if args.review_horizon_days is not None:
        review_kwargs["review_horizon_days"] = args.review_horizon_days
    elif config.get("review_horizon_days") is not None:
        review_kwargs["review_horizon_days"] = config["review_horizon_days"]

    review = generate_weekly_review(
        **review_kwargs,
    )

    if args.csv:
        csv_path = Path(args.csv)
        _write_csv(csv_path, review["rows"])
        print(f"Wrote CSV: {csv_path}")

    summary = review["summary"]
    if summary.get("reviewed_count") == 0:
        print("No recommendations ready for review.")
        return 0

    print(f"reviewed_count={summary.get('reviewed_count')}")
    print(f"win_rate={summary.get('win_rate')}")
    print(f"average_return={summary.get('average_return')}")
    print(f"average_benchmark_return={summary.get('average_benchmark_return')}")
    print(f"average_excess_return={summary.get('average_excess_return')}")
    print(f"best_ticker={summary.get('best_ticker')}")
    print(f"worst_ticker={summary.get('worst_ticker')}")
    print()

    for row in review["rows"]:
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
    parser.add_argument("--db")
    parser.add_argument("--benchmark")
    parser.add_argument("--review-horizon-days", type=int)
    parser.add_argument("--csv")
    return parser.parse_known_args(argv)[0]


def _write_csv(csv_path, rows):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
