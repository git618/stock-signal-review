"""Recommendation generation."""

from src.database import save_recommendations as persist_recommendations


def score_stocks(strategy, feature_map):
    return [strategy.score(symbol, features) for symbol, features in feature_map.items()]


def generate_top_recommendations(scored_stocks, limit=5):
    ranked = sorted(
        scored_stocks,
        key=lambda item: (-item["score"], item["symbol"]),
    )[:limit]

    return [
        {
            "symbol": stock["symbol"],
            "score": stock["score"],
            "rank": index,
        }
        for index, stock in enumerate(ranked, start=1)
    ]


def save_recommendation_batch(db_path, trading_date, strategy_version, recommendations):
    persist_recommendations(db_path, trading_date, strategy_version, recommendations)
