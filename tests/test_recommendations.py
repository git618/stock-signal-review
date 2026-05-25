from src.database import get_recommendations, initialize_database, save_recommendations
from src.recommendations import generate_top_recommendations


def test_generating_top_5_recommendations():
    scored_stocks = [
        {"symbol": "AAA", "score": 0.10},
        {"symbol": "BBB", "score": 0.91},
        {"symbol": "CCC", "score": 0.32},
        {"symbol": "DDD", "score": 0.70},
        {"symbol": "EEE", "score": 0.61},
        {"symbol": "FFF", "score": 0.83},
        {"symbol": "GGG", "score": 0.40},
    ]

    assert generate_top_recommendations(scored_stocks, limit=5) == [
        {"symbol": "BBB", "score": 0.91, "rank": 1},
        {"symbol": "FFF", "score": 0.83, "rank": 2},
        {"symbol": "DDD", "score": 0.70, "rank": 3},
        {"symbol": "EEE", "score": 0.61, "rank": 4},
        {"symbol": "GGG", "score": 0.40, "rank": 5},
    ]


def test_saving_recommendations_to_sqlite(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)

    recommendations = [
        {"symbol": "BBB", "score": 0.91, "rank": 1},
        {"symbol": "FFF", "score": 0.83, "rank": 2},
    ]

    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=recommendations,
    )

    assert get_recommendations(db_path, trading_date="2025-01-10") == [
        {
            "trading_date": "2025-01-10",
            "symbol": "BBB",
            "score": 0.91,
            "rank": 1,
            "strategy_version": "v1",
        },
        {
            "trading_date": "2025-01-10",
            "symbol": "FFF",
            "score": 0.83,
            "rank": 2,
            "strategy_version": "v1",
        },
    ]
