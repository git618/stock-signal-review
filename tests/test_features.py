from src.features import calculate_features


def test_calculating_features_from_price_data():
    price_rows = [
        {"date": "2025-01-02", "close": 100.0, "volume": 1000},
        {"date": "2025-01-03", "close": 102.0, "volume": 1100},
        {"date": "2025-01-06", "close": 105.0, "volume": 1200},
        {"date": "2025-01-07", "close": 103.0, "volume": 1300},
        {"date": "2025-01-08", "close": 108.0, "volume": 1400},
    ]

    features = calculate_features(price_rows)

    assert features == {
        "close": 108.0,
        "return_1d": 0.04854368932038835,
        "return_5d": 0.08,
        "volume_ratio_5d": 1.1666666666666667,
    }
