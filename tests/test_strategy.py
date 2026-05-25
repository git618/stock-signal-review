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


def test_strategy_score_includes_reasons_risk_notes_and_ticker():
    strategy = WeightedStrategy(
        version="v2",
        weights={
            "return_20d": 0.5,
            "return_5d": 0.3,
            "volume_ratio_20d": 0.2,
        },
    )
    features = {
        "return_20d": 0.15,
        "return_5d": 0.04,
        "volume_ratio_20d": 1.1,
        "volatility_20d": 0.35,
    }

    scored = strategy.score("MSFT", features)

    assert scored == {
        "ticker": "MSFT",
        "score": 0.307,
        "component_scores": {
            "return_20d": 0.075,
            "return_5d": 0.012,
            "volume_ratio_20d": 0.22000000000000003,
        },
        "reasons": [
            "return_20d contributed 0.075",
            "return_5d contributed 0.012",
            "volume_ratio_20d contributed 0.22000000000000003",
        ],
        "risk_notes": [
            "20-day volatility is elevated",
        ],
        "strategy_version": "v2",
    }
