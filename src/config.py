"""Application configuration."""

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "stock_research.db"
CONFIG_DIR = BASE_DIR / "config"

DEFAULT_CONFIG = {
    "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
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


def get_default_config_path():
    return CONFIG_DIR / "default.json"


def load_config(path=None):
    config_path = get_default_config_path() if path is None else Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    try:
        loaded = json.loads(config_path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in config file: {config_path}") from error

    merged = dict(DEFAULT_CONFIG)
    merged.update(loaded)
    merged["strategy"] = _merge_strategy_config(
        DEFAULT_CONFIG["strategy"],
        loaded.get("strategy"),
    )
    return merged


def _merge_strategy_config(default_strategy, loaded_strategy):
    merged = {
        "version": default_strategy["version"],
        "weights": dict(default_strategy["weights"]),
    }
    if not loaded_strategy:
        return merged
    if "version" in loaded_strategy:
        merged["version"] = loaded_strategy["version"]
    if "weights" in loaded_strategy:
        merged["weights"].update(loaded_strategy["weights"])
    return merged
