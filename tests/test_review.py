from src.review import review_recommendations_vs_benchmark


def test_reviewing_recommendation_returns_against_spy():
    recommendations = [
        {"trading_date": "2025-01-03", "symbol": "AAA"},
        {"trading_date": "2025-01-03", "symbol": "BBB"},
    ]
    price_lookup = {
        ("AAA", "2025-01-03"): 100.0,
        ("AAA", "2025-01-10"): 110.0,
        ("BBB", "2025-01-03"): 200.0,
        ("BBB", "2025-01-10"): 210.0,
        ("SPY", "2025-01-03"): 500.0,
        ("SPY", "2025-01-10"): 510.0,
    }

    review = review_recommendations_vs_benchmark(
        recommendations=recommendations,
        price_lookup=price_lookup,
        benchmark_symbol="SPY",
    )

    assert review == {
        "benchmark_symbol": "SPY",
        "benchmark_return": 0.02,
        "average_recommendation_return": 0.075,
        "excess_return": 0.05499999999999999,
        "recommendation_count": 2,
        "outperformed_benchmark": True,
    }
