"""Weekly review reporting."""

from datetime import date, timedelta
from decimal import Decimal

from src.database import get_recommendations
from src.market_data import YFinanceMarketDataProvider


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


def generate_weekly_review(
    db_path=None,
    database_path=None,
    start_date=None,
    end_date=None,
    benchmark_ticker="SPY",
    provider=None,
):
    db_path = db_path if db_path is not None else database_path
    recommendations = [
        recommendation
        for recommendation in get_recommendations(db_path)
        if start_date <= recommendation["trading_date"] <= end_date
    ]
    if not recommendations:
        return _empty_review()

    provider = provider or YFinanceMarketDataProvider()
    rows = []

    for recommendation in recommendations:
        ticker = recommendation["symbol"]
        trading_date = recommendation["trading_date"]
        ticker_prices = provider.fetch_daily_prices(ticker, trading_date, end_date)
        benchmark_prices = provider.fetch_daily_prices(
            benchmark_ticker,
            trading_date,
            end_date,
        )

        try:
            entry_price = _lookup_close(ticker_prices, trading_date)
            exit_price = _lookup_close(ticker_prices, end_date)
            benchmark_entry = _lookup_close(benchmark_prices, trading_date)
            benchmark_exit = _lookup_close(benchmark_prices, end_date)
        except KeyError:
            continue

        return_pct = _compute_return(entry_price, exit_price)
        benchmark_return_pct = _compute_return(benchmark_entry, benchmark_exit)
        excess_return_pct = return_pct - benchmark_return_pct

        rows.append(
            {
                "ticker": ticker,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "return_pct": return_pct,
                "benchmark_return_pct": benchmark_return_pct,
                "excess_return_pct": excess_return_pct,
                "is_win": excess_return_pct > 0,
            }
        )

    if not rows:
        return _empty_review()

    return {
        "summary": _build_summary(rows),
        "rows": rows,
    }


def _empty_review():
    return {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def _lookup_close(price_rows, target_date):
    for row in price_rows:
        if row["date"] == target_date:
            return row["close"]
    raise KeyError(f"missing close for {target_date}")


def _build_summary(rows):
    reviewed_count = len(rows)
    win_count = sum(1 for row in rows if row["is_win"])
    loss_count = reviewed_count - win_count
    average_return = _average(row["return_pct"] for row in rows)
    average_benchmark_return = _average(row["benchmark_return_pct"] for row in rows)
    average_excess_return = average_return - average_benchmark_return
    best_row = max(rows, key=lambda row: row["return_pct"])
    worst_row = min(rows, key=lambda row: row["return_pct"])

    return {
        "reviewed_count": reviewed_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_count / reviewed_count,
        "average_return": average_return,
        "average_benchmark_return": average_benchmark_return,
        "average_excess_return": average_excess_return,
        "best_ticker": best_row["ticker"],
        "worst_ticker": worst_row["ticker"],
    }


def _average(values):
    values = list(values)
    if not values:
        return 0.0
    return float(sum(Decimal(str(value)) for value in values) / Decimal(len(values)))
