"""Weekly review reporting."""

from datetime import date, timedelta
from decimal import Decimal


def review_recommendations_vs_benchmark(recommendations, price_lookup, benchmark_symbol):
    if not recommendations:
        raise ValueError("recommendations must not be empty")

    start_date = recommendations[0]["trading_date"]
    end_date = _add_days(start_date, 7)

    recommendation_returns = [
        _compute_return(
            price_lookup[(recommendation["symbol"], start_date)],
            price_lookup[(recommendation["symbol"], end_date)],
        )
        for recommendation in recommendations
    ]
    benchmark_return = _compute_return(
        price_lookup[(benchmark_symbol, start_date)],
        price_lookup[(benchmark_symbol, end_date)],
    )
    average_recommendation_return = float(
        sum(Decimal(str(value)) for value in recommendation_returns)
        / Decimal(len(recommendation_returns))
    )
    excess_return = average_recommendation_return - benchmark_return

    return {
        "benchmark_symbol": benchmark_symbol,
        "benchmark_return": benchmark_return,
        "average_recommendation_return": average_recommendation_return,
        "excess_return": excess_return,
        "recommendation_count": len(recommendations),
        "outperformed_benchmark": average_recommendation_return > benchmark_return,
    }


def _compute_return(start_price, end_price):
    return float((Decimal(str(end_price)) / Decimal(str(start_price))) - Decimal("1"))


def _add_days(iso_date, days):
    parsed = date.fromisoformat(iso_date)
    return (parsed + timedelta(days=days)).isoformat()
