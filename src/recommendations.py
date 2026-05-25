"""Recommendation generation."""

from src.database import (
    initialize_database,
    insert_daily_prices,
    save_recommendations as persist_recommendations,
)
from src.features import calculate_features
from src.market_data import YFinanceMarketDataProvider
from src.strategy import WeightedStrategy


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


def generate_daily_recommendations(
    tickers,
    benchmark_ticker,
    start_date,
    end_date,
    db_path=None,
    database_path=None,
    provider=None,
    price_history_by_ticker=None,
):
    del benchmark_ticker  # Reserved for downstream review/reporting flows.

    db_path = db_path if db_path is not None else database_path
    initialize_database(db_path)

    provider = provider or YFinanceMarketDataProvider()
    strategy = WeightedStrategy(
        version="v1",
        weights={
            "return_20d": 0.5,
            "return_5d": 0.3,
            "volume_ratio_20d": 0.2,
        },
    )

    scored_stocks = []
    for ticker in tickers:
        prices = _get_price_history(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            price_history_by_ticker=price_history_by_ticker,
        )
        if not prices:
            continue

        insert_daily_prices(db_path, ticker, prices)
        features = calculate_features(prices)
        scored = strategy.score(ticker, features)
        scored_stocks.append(
            {
                "ticker": scored["ticker"],
                "score": scored["score"],
                "entry_price": features["close"],
                "strategy_version": scored["strategy_version"],
                "reasons": scored["reasons"],
                "risk_notes": scored["risk_notes"],
            }
        )

    recommendations = generate_top_recommendations(scored_stocks, limit=5)
    save_recommendation_batch(db_path, end_date, strategy.version, recommendations)
    return recommendations


def _get_price_history(ticker, start_date, end_date, provider, price_history_by_ticker):
    if price_history_by_ticker is not None:
        return price_history_by_ticker.get(ticker, [])
    return provider.fetch_daily_prices(ticker, start_date, end_date)
