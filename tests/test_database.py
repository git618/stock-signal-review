import sqlite3

from src.database import get_daily_prices, initialize_database, insert_daily_prices


def test_initialize_database_creates_required_tables(tmp_path):
    db_path = tmp_path / "research.db"

    initialize_database(db_path)

    connection = sqlite3.connect(db_path)
    try:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert {"daily_prices", "recommendations"}.issubset(table_names)


def test_inserting_and_reading_daily_ohlcv_prices(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)

    prices = [
        {
            "date": "2025-01-02",
            "open": 100.0,
            "high": 105.0,
            "low": 99.5,
            "close": 104.0,
            "volume": 1_000_000,
        },
        {
            "date": "2025-01-03",
            "open": 104.0,
            "high": 106.0,
            "low": 103.0,
            "close": 105.5,
            "volume": 1_250_000,
        },
    ]

    insert_daily_prices(db_path, "AAPL", prices)

    assert get_daily_prices(db_path, "AAPL") == [
        {
            "symbol": "AAPL",
            "date": "2025-01-02",
            "open": 100.0,
            "high": 105.0,
            "low": 99.5,
            "close": 104.0,
            "volume": 1_000_000,
        },
        {
            "symbol": "AAPL",
            "date": "2025-01-03",
            "open": 104.0,
            "high": 106.0,
            "low": 103.0,
            "close": 105.5,
            "volume": 1_250_000,
        },
    ]
