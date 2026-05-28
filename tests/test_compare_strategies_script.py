import csv
from pathlib import Path
import runpy

import pytest

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


def test_compare_strategies_sorts_by_average_excess_return_ascending(
    monkeypatch, capsys, tmp_path
):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    low_config = _write_config(tmp_path / "low.json", version="low")
    high_config = _write_config(tmp_path / "high.json", version="high")

    def fake_run_backtest(**kwargs):
        return {
            "summary": _summary_with_excess(
                kwargs["strategy_version"],
                _excess_by_strategy(kwargs["strategy_version"]),
            ),
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(high_config),
            str(low_config),
            "--sort-by",
            "average_excess_return",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()
    rows = _printed_data_rows(captured.out)

    assert rows[0].startswith(str(low_config))
    assert rows[1].startswith(str(high_config))


def test_compare_strategies_sorts_by_average_excess_return_descending(
    monkeypatch, capsys, tmp_path
):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    low_config = _write_config(tmp_path / "low.json", version="low")
    high_config = _write_config(tmp_path / "high.json", version="high")

    def fake_run_backtest(**kwargs):
        return {
            "summary": _summary_with_excess(
                kwargs["strategy_version"],
                _excess_by_strategy(kwargs["strategy_version"]),
            ),
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(low_config),
            str(high_config),
            "--sort-by",
            "average_excess_return",
            "--descending",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()
    rows = _printed_data_rows(captured.out)

    assert rows[0].startswith(str(high_config))
    assert rows[1].startswith(str(low_config))


def test_compare_strategies_prints_best_strategy_summary_when_sorted(
    monkeypatch, capsys, tmp_path
):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    low_config = _write_config(tmp_path / "low.json", version="low")
    high_config = _write_config(tmp_path / "high.json", version="high")

    def fake_run_backtest(**kwargs):
        return {
            "summary": _summary_with_excess(
                kwargs["strategy_version"],
                _excess_by_strategy(kwargs["strategy_version"]),
            ),
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(low_config),
            str(high_config),
            "--sort-by",
            "average_excess_return",
            "--descending",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert f"best_config={high_config}" in captured.out
    assert "best_strategy=high" in captured.out
    assert "best_metric=average_excess_return" in captured.out
    assert "best_value=0.2" in captured.out


def test_compare_strategies_csv_preserves_sorted_order(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    low_config = _write_config(tmp_path / "low.json", version="low")
    high_config = _write_config(tmp_path / "high.json", version="high")
    csv_path = tmp_path / "comparison.csv"

    def fake_run_backtest(**kwargs):
        return {
            "summary": _summary_with_excess(
                kwargs["strategy_version"],
                _excess_by_strategy(kwargs["strategy_version"]),
            ),
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(low_config),
            str(high_config),
            "--sort-by",
            "average_excess_return",
            "--descending",
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    rows = list(csv.DictReader(csv_path.open()))
    assert rows[0]["config"] == str(high_config)
    assert rows[1]["config"] == str(low_config)


def test_compare_strategies_invalid_sort_by_exits_with_readable_error(
    monkeypatch, capsys, tmp_path
):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    config_path = _write_config(tmp_path / "one.json", version="v1")

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(config_path),
            "--sort-by",
            "not_a_metric",
        ],
    )

    with pytest.raises(SystemExit):
        runpy.run_path(str(script_path), run_name="__main__")

    captured = capsys.readouterr()
    assert "invalid choice" in captured.err or "Invalid --sort-by metric" in captured.err


def test_compare_strategies_without_sort_by_preserves_input_order(
    monkeypatch, capsys, tmp_path
):
    script_path = Path(__file__).resolve().parent.parent / "scripts/compare_strategies.py"
    first_config = _write_config(tmp_path / "first.json", version="first")
    second_config = _write_config(tmp_path / "second.json", version="second")

    def fake_run_backtest(**kwargs):
        return {
            "summary": _summary_with_excess(
                kwargs["strategy_version"],
                _excess_by_strategy(kwargs["strategy_version"]),
            ),
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--configs",
            str(second_config),
            str(first_config),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()
    rows = _printed_data_rows(captured.out)

    assert rows[0].startswith(str(second_config))
    assert rows[1].startswith(str(first_config))
    assert "best_config=" not in captured.out


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


def _summary_with_excess(strategy_version, excess_return):
    summary = _summary(strategy_version)
    summary["average_excess_return"] = excess_return
    return summary


def _excess_by_strategy(strategy_version):
    return {
        "high": 0.2,
        "low": -0.1,
        "first": 0.1,
        "second": 0.3,
    }.get(strategy_version, 0.0)


def _printed_data_rows(output):
    return [
        line
        for line in output.splitlines()
        if line and not line.startswith("config ") and not line.startswith("best_")
    ]
