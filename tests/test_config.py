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
