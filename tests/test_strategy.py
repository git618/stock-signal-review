from src.strategy import WeightedStrategy


def test_scoring_one_stock_with_explainable_weighted_strategy():
    strategy = WeightedStrategy(
        version="v1",
        weights={
            "return_5d": 0.6,
            "return_1d": 0.3,
            "volume_ratio_5d": 0.1,
        },
    )
    features = {
        "return_5d": 0.08,
        "return_1d": 0.02,
        "volume_ratio_5d": 1.2,
    }

    scored = strategy.score("NVDA", features)

    assert scored == {
        "symbol": "NVDA",
        "strategy_version": "v1",
        "score": 0.174,
        "component_scores": {
            "return_5d": 0.048,
            "return_1d": 0.006,
            "volume_ratio_5d": 0.12,
        },
    }
