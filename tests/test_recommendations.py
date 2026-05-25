from src.database import get_recommendations, initialize_database, save_recommendations
from src.recommendations import generate_top_recommendations, score_stocks


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


def test_top_5_recommendations_preserve_full_explanation_fields():
    scored_stocks = [
        {
            "ticker": "AAA",
            "score": 0.10,
            "entry_price": 100.0,
            "strategy_version": "v2",
            "reasons": ["weak momentum"],
            "risk_notes": ["low liquidity"],
        },
        {
            "ticker": "BBB",
            "score": 0.91,
            "entry_price": 210.0,
            "strategy_version": "v2",
            "reasons": ["strong momentum"],
            "risk_notes": [],
        },
        {
            "ticker": "CCC",
            "score": 0.32,
            "entry_price": 95.0,
            "strategy_version": "v2",
            "reasons": ["moderate trend"],
            "risk_notes": [],
        },
        {
            "ticker": "DDD",
            "score": 0.70,
            "entry_price": 130.0,
            "strategy_version": "v2",
            "reasons": ["breakout"],
            "risk_notes": ["high volatility"],
        },
        {
            "ticker": "EEE",
            "score": 0.61,
            "entry_price": 88.0,
            "strategy_version": "v2",
            "reasons": ["relative strength"],
            "risk_notes": [],
        },
        {
            "ticker": "FFF",
            "score": 0.83,
            "entry_price": 155.0,
            "strategy_version": "v2",
            "reasons": ["earnings revision"],
            "risk_notes": [],
        },
    ]

    assert generate_top_recommendations(scored_stocks, limit=5) == [
        {
            "ticker": "BBB",
            "rank": 1,
            "score": 0.91,
            "entry_price": 210.0,
            "strategy_version": "v2",
            "reasons": ["strong momentum"],
            "risk_notes": [],
        },
        {
            "ticker": "FFF",
            "rank": 2,
            "score": 0.83,
            "entry_price": 155.0,
            "strategy_version": "v2",
            "reasons": ["earnings revision"],
            "risk_notes": [],
        },
        {
            "ticker": "DDD",
            "rank": 3,
            "score": 0.70,
            "entry_price": 130.0,
            "strategy_version": "v2",
            "reasons": ["breakout"],
            "risk_notes": ["high volatility"],
        },
        {
            "ticker": "EEE",
            "rank": 4,
            "score": 0.61,
            "entry_price": 88.0,
            "strategy_version": "v2",
            "reasons": ["relative strength"],
            "risk_notes": [],
        },
        {
            "ticker": "CCC",
            "rank": 5,
            "score": 0.32,
            "entry_price": 95.0,
            "strategy_version": "v2",
            "reasons": ["moderate trend"],
            "risk_notes": [],
        },
    ]


def test_scoring_multiple_tickers_preserves_strategy_output_shape():
    class FakeStrategy:
        version = "v3"

        def score(self, symbol, features):
            return {
                "ticker": symbol,
                "score": features["score_seed"],
                "component_scores": {"score_seed": features["score_seed"]},
                "reasons": [f"{symbol} scored from score_seed"],
                "risk_notes": [],
                "strategy_version": self.version,
            }

    feature_map = {
        "AAPL": {"score_seed": 0.5},
        "MSFT": {"score_seed": 0.7},
    }

    assert score_stocks(FakeStrategy(), feature_map) == [
        {
            "ticker": "AAPL",
            "score": 0.5,
            "component_scores": {"score_seed": 0.5},
            "reasons": ["AAPL scored from score_seed"],
            "risk_notes": [],
            "strategy_version": "v3",
        },
        {
            "ticker": "MSFT",
            "score": 0.7,
            "component_scores": {"score_seed": 0.7},
            "reasons": ["MSFT scored from score_seed"],
            "risk_notes": [],
            "strategy_version": "v3",
        },
    ]
