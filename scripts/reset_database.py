"""Reset the local development SQLite database."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_DB_PATH
from src.database import initialize_database


# Shared default database path: data/stock_research.db


def main(argv=None):
    args = _parse_args(argv)
    db_path = Path(args.db)

    if db_path.exists():
        db_path.unlink()

    initialize_database(db_path)
    print(f"Database reset complete: {db_path}")
    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    return parser.parse_known_args(argv)[0]


if __name__ == "__main__":
    main()
