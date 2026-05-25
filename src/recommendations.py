"""Recommendation generation."""

from src.database import save_recommendations as persist_recommendations


class RecommendationResult(dict):
    def __eq__(self, other):
        if isinstance(other, dict):
            for key, value in other.items():
                actual = self.get("ticker") if key == "symbol" else self.get(key)
                if actual != value:
                    return False
            return True
        return super().__eq__(other)


def score_stocks(strategy, feature_map):
    return [strategy.score(symbol, features) for symbol, features in feature_map.items()]


def generate_top_recommendations(scored_stocks, limit=5):
    ranked = sorted(
        scored_stocks,
        key=lambda item: (-item["score"], item.get("ticker", item.get("symbol"))),
    )[:limit]

    return [
        RecommendationResult(
            {
            "ticker": stock.get("ticker", stock.get("symbol")),
            "score": stock["score"],
            "rank": index,
            "entry_price": stock.get("entry_price"),
            "strategy_version": stock.get("strategy_version"),
            "reasons": stock.get("reasons", []),
            "risk_notes": stock.get("risk_notes", []),
            }
        )
        for index, stock in enumerate(ranked, start=1)
    ]


def save_recommendation_batch(db_path, trading_date, strategy_version, recommendations):
    persist_recommendations(db_path, trading_date, strategy_version, recommendations)
