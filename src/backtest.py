"""Simple historical backtest for the current strategy."""

from datetime import date, timedelta
from decimal import Decimal
from statistics import median

from src.features import calculate_features
from src.market_data import YFinanceMarketDataProvider
from src.recommendations import generate_top_recommendations
from src.strategy import WeightedStrategy


def run_backtest(
    tickers,
    benchmark_ticker,
    start_date,
    end_date,
    holding_days,
    top_n,
    provider=None,
    price_history_by_ticker=None,
    strategy_version=None,
    strategy_weights=None,
):
    provider = provider or YFinanceMarketDataProvider()
    strategy = WeightedStrategy(
        version=strategy_version or "v1",
        weights=strategy_weights
        or {
            "return_20d": 0.5,
            "return_5d": 0.3,
            "volume_ratio_20d": 0.2,
        },
    )

    history_map = {
        ticker: _normalize_price_history(
            _get_price_history(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            price_history_by_ticker=price_history_by_ticker,
            )
        )
        for ticker in set(tickers + [benchmark_ticker])
    }
    benchmark_lookup = {row["date"]: row for row in history_map.get(benchmark_ticker, [])}
    recommendation_dates = _recommendation_dates(
        benchmark_rows=history_map.get(benchmark_ticker, []),
        start_date=start_date,
        end_date=end_date,
        holding_days=holding_days,
    )

    rows = []
    for recommendation_date in recommendation_dates:
        exit_date = _trading_day_exit_date(
            history_map.get(benchmark_ticker, []),
            recommendation_date,
            holding_days,
        )
        if exit_date is None:
            continue
        scored_stocks = []
        for ticker in tickers:
            if ticker == benchmark_ticker:
                continue
            ticker_rows = history_map.get(ticker, [])
            historical_rows = [row for row in ticker_rows if row["date"] <= recommendation_date]
            if len(historical_rows) < 2:
                continue
            if _row_for_date(ticker_rows, recommendation_date) is None:
                continue
            if _row_for_date(ticker_rows, exit_date) is None:
                continue
            if benchmark_lookup.get(recommendation_date) is None:
                continue
            if benchmark_lookup.get(exit_date) is None:
                continue

            features = calculate_features(historical_rows)
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

        recommendations = generate_top_recommendations(scored_stocks, limit=top_n)
        for recommendation in recommendations:
            ticker = recommendation["ticker"]
            ticker_rows = history_map[ticker]
            entry_price = _row_for_date(ticker_rows, recommendation_date)["close"]
            exit_price = _row_for_date(ticker_rows, exit_date)["close"]
            benchmark_entry = benchmark_lookup[recommendation_date]["close"]
            benchmark_exit = benchmark_lookup[exit_date]["close"]
            return_pct = _compute_return(entry_price, exit_price)
            benchmark_return_pct = _compute_return(benchmark_entry, benchmark_exit)
            excess_return_pct = return_pct - benchmark_return_pct
            rows.append(
                {
                    "recommendation_date": recommendation_date,
                    "exit_date": exit_date,
                    "ticker": ticker,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "return_pct": return_pct,
                    "benchmark_return_pct": benchmark_return_pct,
                    "excess_return_pct": excess_return_pct,
                    "is_win": excess_return_pct > 0,
                }
            )

    return {
        "summary": _build_summary(rows),
        "rows": rows,
    }


def _build_summary(rows):
    if not rows:
        return {
            "tested_count": 0,
            "recommendation_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "median_return": 0.0,
            "median_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
            "best_return": 0.0,
            "worst_return": 0.0,
        }

    tested_count = len(rows)
    win_count = sum(1 for row in rows if row["is_win"])
    loss_count = tested_count - win_count
    average_return = _average(row["return_pct"] for row in rows)
    average_benchmark_return = _average(row["benchmark_return_pct"] for row in rows)
    average_excess_return = _average(row["excess_return_pct"] for row in rows)
    median_return = _median(row["return_pct"] for row in rows)
    median_excess_return = _median(row["excess_return_pct"] for row in rows)
    best_row = max(rows, key=lambda row: row["return_pct"])
    worst_row = min(rows, key=lambda row: row["return_pct"])

    return {
        "tested_count": tested_count,
        "recommendation_count": tested_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_count / tested_count,
        "average_return": average_return,
        "average_benchmark_return": average_benchmark_return,
        "average_excess_return": average_excess_return,
        "median_return": median_return,
        "median_excess_return": median_excess_return,
        "best_ticker": best_row["ticker"],
        "worst_ticker": worst_row["ticker"],
        "best_return": best_row["return_pct"],
        "worst_return": worst_row["return_pct"],
    }


def _get_price_history(ticker, start_date, end_date, provider, price_history_by_ticker):
    if price_history_by_ticker is not None:
        return price_history_by_ticker.get(ticker, [])
    return provider.fetch_daily_prices(ticker, start_date, end_date)


def _normalize_price_history(rows):
    normalized_rows = [
        {
            **row,
            "date": _normalize_date(row["date"]),
        }
        for row in rows
    ]
    return sorted(normalized_rows, key=lambda row: row["date"])


def _recommendation_dates(benchmark_rows, start_date, end_date, holding_days):
    return [
        row["date"]
        for row in benchmark_rows
        if start_date <= row["date"] <= end_date
    ]


def _row_for_date(rows, target_date):
    for row in rows:
        if row["date"] == target_date:
            return row
    return None


def _trading_day_exit_date(rows, recommendation_date, holding_days):
    future_dates = [row["date"] for row in rows if row["date"] > recommendation_date]
    if len(future_dates) < holding_days:
        return None
    return future_dates[holding_days - 1]


def _compute_return(entry_price, exit_price):
    return float((Decimal(str(exit_price)) / Decimal(str(entry_price))) - Decimal("1"))


def _average(values):
    values = list(values)
    return float(sum(Decimal(str(value)) for value in values) / Decimal(len(values)))


def _median(values):
    values = list(values)
    return float(median(values))


def _add_days(iso_date, days):
    normalized = _normalize_date(iso_date)
    return (date.fromisoformat(normalized) + timedelta(days=days)).isoformat()


def _normalize_date(value):
    if hasattr(value, "date"):
        try:
            return value.date().isoformat()
        except TypeError:
            pass

    text = str(value)
    if " " in text:
        text = text.split(" ", 1)[0]
    if "T" in text:
        text = text.split("T", 1)[0]
    return text
