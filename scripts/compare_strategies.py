"""Compare multiple strategy configs side by side using backtest summaries."""

import argparse
import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest import run_backtest
from src.config import load_config


SUMMARY_FIELDS = [
    "config",
    "strategy_version",
    "tested_count",
    "win_count",
    "loss_count",
    "win_rate",
    "average_return",
    "average_benchmark_return",
    "average_excess_return",
    "median_return",
    "median_excess_return",
    "best_ticker",
    "worst_ticker",
    "best_return",
    "worst_return",
]


def main(argv=None):
    args = _parse_args(argv)
    rows = []

    for config_path_text in args.configs:
        config_path = Path(config_path_text)
        config = load_config(config_path)
        result = run_backtest(
            tickers=config["tickers"],
            benchmark_ticker=config["benchmark"],
            start_date=config["backtest_start_date"],
            end_date=config["backtest_end_date"],
            holding_days=config["holding_days"],
            top_n=config["top_n"],
            strategy_version=config["strategy"]["version"],
            strategy_weights=config["strategy"]["weights"],
        )
        row = {
            "config": str(config_path),
            "strategy_version": config["strategy"]["version"],
            **result["summary"],
        }
        rows.append({field: row.get(field) for field in SUMMARY_FIELDS})

    if args.csv:
        csv_path = Path(args.csv)
        _write_csv(csv_path, rows)
        print(f"Wrote CSV: {csv_path}")

    _print_rows(rows)
    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--csv")
    return parser.parse_known_args(argv)[0]


def _write_csv(csv_path, rows):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _print_rows(rows):
    header = " ".join(SUMMARY_FIELDS)
    print(header)
    for row in rows:
        print(" ".join(str(row.get(field)) for field in SUMMARY_FIELDS))


if __name__ == "__main__":
    main()
