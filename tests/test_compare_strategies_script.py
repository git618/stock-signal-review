import csv
from pathlib import Path
import runpy

from src.config import load_config


def test_compare_strategies_script_exists_and_accepts_configs(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_one = _write_config(tmp_path / "one.json", version="v1")
    config_two = _write_config(tmp_path / "two.json", version="v2")
    calls = []

    def fake_run_backtest(**kwargs):
        calls.append(kwargs)
        return {"summary": _summary(strategy_version="ignored"), "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_one),
            str(config_two),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert len(calls) == 2


def test_compare_strategies_runs_backtest_once_per_config(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_one = _write_config(tmp_path / "one.json", version="v1")
    config_two = _write_config(tmp_path / "two.json", version="v2")
    calls = []

    def fake_run_backtest(**kwargs):
        calls.append(kwargs)
        return {"summary": _summary(strategy_version=kwargs["strategy_version"]), "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_one),
            str(config_two),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert calls == [
        {
            "tickers": ["AAPL", "MSFT"],
            "benchmark_ticker": "SPY",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "holding_days": 5,
            "top_n": 3,
            "strategy_version": "v1",
            "strategy_weights": {
                "return_20d": 0.5,
                "return_5d": 0.3,
                "volume_ratio_20d": 0.2,
            },
        },
        {
            "tickers": ["AAPL", "MSFT"],
            "benchmark_ticker": "SPY",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "holding_days": 5,
            "top_n": 3,
            "strategy_version": "v2",
            "strategy_weights": {
                "return_20d": 0.2,
                "return_5d": 0.1,
                "volume_ratio_20d": 0.1,
                "volatility_20d": -0.4,
            },
        },
    ]


def test_compare_strategies_output_includes_one_row_per_config(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_one = _write_config(tmp_path / "one.json", version="v1")
    config_two = _write_config(tmp_path / "two.json", version="v2")

    def fake_run_backtest(**kwargs):
        return {"summary": _summary(strategy_version=kwargs["strategy_version"]), "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_one),
            str(config_two),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert str(config_one) in captured.out
    assert str(config_two) in captured.out
    assert "strategy_version" in captured.out
    assert "tested_count" in captured.out
    assert "average_excess_return" in captured.out


def test_compare_strategies_writes_csv_with_expected_headers(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_one = _write_config(tmp_path / "one.json", version="v1")
    csv_path = tmp_path / "strategy_comparison.csv"

    def fake_run_backtest(**kwargs):
        return {"summary": _summary(strategy_version=kwargs["strategy_version"]), "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_one),
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert csv_path.exists()
    assert f"Wrote CSV: {csv_path}" in captured.out
    header = csv_path.read_text().splitlines()[0]
    assert header == (
        "config,strategy_version,tested_count,win_count,loss_count,win_rate,"
        "average_return,average_benchmark_return,average_excess_return,"
        "median_return,median_excess_return,best_ticker,worst_ticker,"
        "best_return,worst_return"
    )


def test_compare_strategies_includes_zero_row_when_backtest_has_no_results(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_one = _write_config(tmp_path / "one.json", version="v1")

    def fake_run_backtest(**kwargs):
        return {"summary": _summary(strategy_version=kwargs["strategy_version"], tested_count=0), "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_one),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "tested_count" in captured.out
    assert "0" in captured.out


def test_example_strategy_configs_are_valid_json_and_load_correctly():
    base_dir = Path(__file__).resolve().parent.parent
    default_config = load_config(base_dir / "config/default.json")
    momentum_config = load_config(base_dir / "config/momentum.json")
    low_vol_config = load_config(base_dir / "config/low_volatility.json")

    assert default_config["strategy"]["version"] == "v1"
    assert momentum_config["strategy"]["version"] == "momentum-v1"
    assert low_vol_config["strategy"]["version"] == "low-vol-v1"


def _write_config(path, version):
    path.write_text(
        """{
  "tickers": ["AAPL", "MSFT"],
  "benchmark": "SPY",
  "holding_days": 5,
  "top_n": 3,
  "backtest_start_date": "2025-01-01",
  "backtest_end_date": "2025-01-31",
  "strategy": {
    "version": "%s",
    "weights": %s
  }
}"""
        % (
            version,
            (
                '{"return_20d": 0.5, "return_5d": 0.3, "volume_ratio_20d": 0.2}'
                if version == "v1"
                else '{"return_20d": 0.2, "return_5d": 0.1, "volume_ratio_20d": 0.1, "volatility_20d": -0.4}'
            ),
        )
    )
    return path


def _summary(strategy_version, tested_count=4):
    if tested_count == 0:
        return {
            "tested_count": 0,
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

    return {
        "tested_count": tested_count,
        "win_count": 3,
        "loss_count": 1,
        "win_rate": 0.75,
        "average_return": 0.12,
        "average_benchmark_return": 0.04,
        "average_excess_return": 0.08,
        "median_return": 0.11,
        "median_excess_return": 0.07,
        "best_ticker": "AAPL",
        "worst_ticker": "MSFT",
        "best_return": 0.2,
        "worst_return": -0.03,
        "strategy_version": strategy_version,
    }
