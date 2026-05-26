"""List saved recommendations from SQLite."""

import argparse
import csv
from pathlib import Path
import os
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_DB_PATH, load_config
from src.database import initialize_database

# Shared default database path: data/stock_research.db


def main(argv=None):
    args = _parse_args(argv)
    config = load_config(args.config) if args.config else None
    db_path = Path(
        args.db
        if args.db is not None
        else (
            config["database_path"]
            if config is not None
            else os.environ.get("STOCK_RESEARCH_DB_PATH", str(DEFAULT_DB_PATH))
        )
    )
    initialize_database(db_path)
    rows = _read_recommendations(db_path, args.limit)

    if args.csv:
        csv_path = Path(args.csv)
        _write_csv(csv_path, rows)
        print(f"Wrote CSV: {csv_path}")

    if not rows:
        print("No recommendations found.")
        return 0

    header = (
        f"{'trading_date':<12} {'rank':<4} {'symbol':<8} "
        f"{'score':<8} {'entry_price':<11} {'strategy_version':<16}"
    )
    print(header)
    for row in rows:
        entry_price = "" if row["entry_price"] is None else str(row["entry_price"])
        print(
            f"{row['trading_date']:<12} {row['rank']:<4} {row['symbol']:<8} "
            f"{row['score']:<8} {entry_price:<11} {row['strategy_version']:<16}"
        )

    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--db")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--csv")
    return parser.parse_known_args(argv)[0]


def _read_recommendations(db_path, limit):
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT trading_date, rank, symbol, score, entry_price, strategy_version
            FROM recommendations
            ORDER BY trading_date DESC, rank ASC, symbol ASC
            LIMIT ?
            """
            ,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "trading_date": row[0],
            "rank": row[1],
            "symbol": row[2],
            "score": row[3],
            "entry_price": row[4],
            "strategy_version": row[5],
        }
        for row in rows
    ]


def _write_csv(csv_path, rows):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "trading_date",
        "rank",
        "symbol",
        "score",
        "entry_price",
        "strategy_version",
    ]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
