"""SQLite persistence layer."""

import json
from pathlib import Path
import sqlite3


def initialize_database(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_prices (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                PRIMARY KEY (symbol, date)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                trading_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                score REAL NOT NULL,
                rank INTEGER NOT NULL,
                entry_price REAL,
                strategy_version TEXT NOT NULL,
                PRIMARY KEY (trading_date, symbol, strategy_version)
            )
            """
        )
        try:
            connection.execute(
                "ALTER TABLE recommendations ADD COLUMN entry_price REAL"
            )
        except sqlite3.OperationalError:
            pass
        for column_name, column_type in [
            ("component_scores", "TEXT"),
            ("reasons", "TEXT"),
            ("risk_notes", "TEXT"),
            ("signal_strength", "TEXT"),
        ]:
            try:
                connection.execute(
                    f"ALTER TABLE recommendations ADD COLUMN {column_name} {column_type}"
                )
            except sqlite3.OperationalError:
                pass
        connection.commit()
    finally:
        connection.close()


def insert_daily_prices(db_path, symbol, prices):
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT OR REPLACE INTO daily_prices
            (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    symbol,
                    row["date"],
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                    row["volume"],
                )
                for row in prices
            ],
        )
        connection.commit()
    finally:
        connection.close()


def get_daily_prices(db_path, symbol):
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT symbol, date, open, high, low, close, volume
            FROM daily_prices
            WHERE symbol = ?
            ORDER BY date
            """,
            (symbol,),
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "symbol": row[0],
            "date": row[1],
            "open": row[2],
            "high": row[3],
            "low": row[4],
            "close": row[5],
            "volume": row[6],
        }
        for row in rows
    ]


def save_recommendations(db_path, trading_date, strategy_version, recommendations):
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT OR IGNORE INTO recommendations
            (
                trading_date,
                symbol,
                score,
                rank,
                entry_price,
                component_scores,
                reasons,
                risk_notes,
                signal_strength,
                strategy_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    trading_date,
                    recommendation.get("symbol", recommendation.get("ticker")),
                    recommendation["score"],
                    recommendation["rank"],
                    recommendation.get("entry_price"),
                    json.dumps(recommendation.get("component_scores", {})),
                    json.dumps(recommendation.get("reasons", [])),
                    json.dumps(recommendation.get("risk_notes", [])),
                    recommendation.get("signal_strength", _signal_strength(recommendation["score"])),
                    strategy_version,
                )
                for recommendation in recommendations
            ],
        )
        connection.commit()
    finally:
        connection.close()


def get_recommendations(db_path, trading_date=None):
    connection = sqlite3.connect(db_path)
    try:
        if trading_date is None:
            rows = connection.execute(
                """
                SELECT
                    trading_date,
                    symbol,
                    score,
                    rank,
                    entry_price,
                    component_scores,
                    reasons,
                    risk_notes,
                    signal_strength,
                    strategy_version
                FROM recommendations
                ORDER BY trading_date, rank, symbol
                """
            ).fetchall()
        else:
            rows = connection.execute(
                 """
                 SELECT
                    trading_date,
                    symbol,
                    score,
                    rank,
                    entry_price,
                    component_scores,
                    reasons,
                    risk_notes,
                    signal_strength,
                    strategy_version
                 FROM recommendations
                 WHERE trading_date = ?
                 ORDER BY rank, symbol
                 """,
                (trading_date,),
            ).fetchall()
    finally:
        connection.close()

    return [
        {
            "trading_date": row[0],
            "symbol": row[1],
            "score": row[2],
            "rank": row[3],
            "component_scores": _deserialize_json(row[5], {}),
            "reasons": _deserialize_json(row[6], []),
            "risk_notes": _deserialize_json(row[7], []),
            "signal_strength": row[8] or _signal_strength(row[2]),
            "strategy_version": row[9],
        }
        for row in rows
    ]


def _deserialize_json(value, default):
    if value in (None, ""):
        return default
    return json.loads(value)


def _signal_strength(score):
    if score > 1:
        return "strong"
    if score > 0:
        return "positive"
    return "weak"
