import json
from pathlib import Path

import pytest

from src.config import get_default_config_path, load_config


def test_load_config_loads_default_json():
    config = load_config()

    assert get_default_config_path().name == "default.json"
    assert config == {
        "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
        "benchmark": "SPY",
        "lookback_days": 90,
        "holding_days": 5,
        "top_n": 5,
        "review_horizon_days": 5,
        "database_path": "data/stock_research.db",
        "backtest_start_date": "2026-02-24",
        "backtest_end_date": "2026-05-25",
        "strategy": {
            "version": "v1",
            "weights": {
                "return_20d": 0.4,
                "return_5d": 0.2,
                "volume_ratio_20d": 0.2,
                "volatility_20d": -0.2,
            },
        },
    }


def test_load_config_loads_custom_config_file(tmp_path):
    config_path = tmp_path / "custom.json"
    config_path.write_text(
        json.dumps(
            {
                "tickers": ["AAPL", "QQQ"],
                "benchmark": "QQQ",
                "lookback_days": 45,
                "holding_days": 10,
                "top_n": 3,
                "review_horizon_days": 7,
                "database_path": "data/custom.db",
            }
        )
    )

    config = load_config(config_path)

    assert config == {
        "tickers": ["AAPL", "QQQ"],
        "benchmark": "QQQ",
        "lookback_days": 45,
        "holding_days": 10,
        "top_n": 3,
        "review_horizon_days": 7,
        "database_path": "data/custom.db",
        "backtest_start_date": None,
        "backtest_end_date": None,
        "strategy": {
            "version": "v1",
            "weights": {
                "return_20d": 0.5,
                "return_5d": 0.3,
                "volume_ratio_20d": 0.2,
            },
        },
    }


def test_load_config_missing_optional_keys_fall_back_to_defaults(tmp_path):
    config_path = tmp_path / "partial.json"
    config_path.write_text(
        json.dumps(
            {
                "tickers": ["AAPL", "MSFT"],
            }
        )
    )

    config = load_config(config_path)

    assert config == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark": "SPY",
        "lookback_days": 90,
        "holding_days": 5,
        "top_n": 5,
        "review_horizon_days": 5,
        "database_path": "data/stock_research.db",
        "backtest_start_date": None,
        "backtest_end_date": None,
        "strategy": {
            "version": "v1",
            "weights": {
                "return_20d": 0.5,
                "return_5d": 0.3,
                "volume_ratio_20d": 0.2,
            },
        },
    }


def test_load_config_invalid_json_raises_value_error(tmp_path):
    config_path = tmp_path / "broken.json"
    config_path.write_text("{not valid json")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(config_path)


def test_load_config_missing_file_raises_file_not_found_error(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_config(missing_path)


def test_load_config_custom_strategy_weights_are_loaded(tmp_path):
    config_path = tmp_path / "custom.json"
    config_path.write_text(
        json.dumps(
            {
                "strategy": {
                    "version": "v9",
                    "weights": {
                        "return_20d": 0.1,
                        "return_5d": 0.1,
                        "volume_ratio_20d": 0.1,
                        "volatility_20d": -0.7,
                    },
                }
            }
        )
    )

    config = load_config(config_path)

    assert config["strategy"] == {
        "version": "v9",
        "weights": {
            "return_20d": 0.1,
            "return_5d": 0.1,
            "volume_ratio_20d": 0.1,
            "volatility_20d": -0.7,
        },
    }
