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


def test_initialize_database_creates_missing_parent_directory(tmp_path):
    db_path = tmp_path / "nested" / "deeper" / "research.db"

    initialize_database(db_path)

    assert db_path.parent.exists()
    assert db_path.exists()


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


def test_initialize_database_migrates_old_recommendation_schema(tmp_path):
    db_path = tmp_path / "research.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE recommendations (
                trading_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                score REAL NOT NULL,
                rank INTEGER NOT NULL,
                strategy_version TEXT NOT NULL,
                PRIMARY KEY (trading_date, symbol, strategy_version)
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    initialize_database(db_path)

    connection = sqlite3.connect(db_path)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(recommendations)").fetchall()
        }
    finally:
        connection.close()

    assert {
        "entry_price",
        "component_scores",
        "reasons",
        "risk_notes",
        "signal_strength",
    }.issubset(columns)
