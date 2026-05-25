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


def test_calculating_all_mvp_features_from_20_day_price_data():
    price_rows = [
        {"date": "2025-01-01", "close": 100.0, "volume": 1000},
        {"date": "2025-01-02", "close": 101.0, "volume": 1010},
        {"date": "2025-01-03", "close": 102.0, "volume": 1020},
        {"date": "2025-01-04", "close": 103.0, "volume": 1030},
        {"date": "2025-01-05", "close": 104.0, "volume": 1040},
        {"date": "2025-01-06", "close": 105.0, "volume": 1050},
        {"date": "2025-01-07", "close": 106.0, "volume": 1060},
        {"date": "2025-01-08", "close": 107.0, "volume": 1070},
        {"date": "2025-01-09", "close": 108.0, "volume": 1080},
        {"date": "2025-01-10", "close": 109.0, "volume": 1090},
        {"date": "2025-01-11", "close": 110.0, "volume": 1100},
        {"date": "2025-01-12", "close": 111.0, "volume": 1110},
        {"date": "2025-01-13", "close": 112.0, "volume": 1120},
        {"date": "2025-01-14", "close": 113.0, "volume": 1130},
        {"date": "2025-01-15", "close": 114.0, "volume": 1140},
        {"date": "2025-01-16", "close": 115.0, "volume": 1150},
        {"date": "2025-01-17", "close": 116.0, "volume": 1160},
        {"date": "2025-01-18", "close": 117.0, "volume": 1170},
        {"date": "2025-01-19", "close": 118.0, "volume": 1180},
        {"date": "2025-01-20", "close": 119.0, "volume": 1190},
    ]

    features = calculate_features(price_rows)

    assert features["return_5d"] == 0.043478260869565216
    assert features["return_20d"] == 0.19
    assert features["ma_20"] == 109.5
    assert features["volatility_20d"] == 5.916079783099616
    assert features["volume_ratio_20d"] == 1.08675799086758
