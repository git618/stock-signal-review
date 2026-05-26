from datetime import date, timedelta
from pathlib import Path
import runpy

from src.backtest import _add_days, run_backtest


def test_run_backtest_returns_summary_from_mocked_price_history():
    tickers = ["AAPL", "MSFT", "NVDA", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0),
        "MSFT": _price_rows(100.0, 1.0),
        "NVDA": _price_rows(100.0, 3.0),
        "SPY": _price_rows(100.0, 0.5),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-25",
        holding_days=5,
        top_n=2,
        price_history_by_ticker=price_history,
    )

    assert result["summary"]["recommendation_count"] > 0
    assert "win_rate" in result["summary"]
    assert "average_return" in result["summary"]
    assert "average_benchmark_return" in result["summary"]
    assert "average_excess_return" in result["summary"]
    assert "median_return" in result["summary"]
    assert "median_excess_return" in result["summary"]
    assert "best_ticker" in result["summary"]
    assert "worst_ticker" in result["summary"]
    assert "best_return" in result["summary"]
    assert "worst_return" in result["summary"]


def test_run_backtest_summary_includes_median_values():
    tickers = ["AAPL", "MSFT", "NVDA", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0),
        "MSFT": _price_rows(100.0, 1.0),
        "NVDA": _price_rows(100.0, 3.0),
        "SPY": _price_rows(100.0, 0.5),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-25",
        holding_days=5,
        top_n=2,
        price_history_by_ticker=price_history,
    )

    assert isinstance(result["summary"]["median_return"], float)
    assert isinstance(result["summary"]["median_excess_return"], float)


def test_run_backtest_summary_includes_best_and_worst_return_values():
    tickers = ["AAPL", "MSFT", "NVDA", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0),
        "MSFT": _price_rows(100.0, 1.0),
        "NVDA": _price_rows(100.0, 3.0),
        "SPY": _price_rows(100.0, 0.5),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-25",
        holding_days=5,
        top_n=2,
        price_history_by_ticker=price_history,
    )

    assert isinstance(result["summary"]["best_return"], float)
    assert isinstance(result["summary"]["worst_return"], float)
    assert result["summary"]["best_return"] >= result["summary"]["worst_return"]


def test_run_backtest_uses_only_data_available_on_recommendation_date():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0),
        "SPY": _price_rows(100.0, 1.0),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-20",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    first_row = result["rows"][0]
    assert first_row["recommendation_date"] == "2025-01-20"
    assert first_row["ticker"] == "AAPL"


def test_backtest_script_accepts_cli_options(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT,NVDA",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "3",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT", "NVDA"],
        "benchmark_ticker": "SPY",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "holding_days": 5,
        "top_n": 3,
    }


def test_backtest_script_uses_config_values(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """{
  "tickers": ["AAPL", "MSFT"],
  "benchmark": "QQQ",
  "holding_days": 7,
  "top_n": 4,
  "backtest_start_date": "2025-01-01",
  "backtest_end_date": "2025-01-31"
}"""
    )
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--config",
            str(config_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark_ticker": "QQQ",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "holding_days": 7,
        "top_n": 4,
    }


def test_backtest_script_cli_overrides_config_values(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """{
  "tickers": ["AAPL", "MSFT"],
  "benchmark": "QQQ",
  "holding_days": 7,
  "top_n": 4,
  "backtest_start_date": "2024-01-01",
  "backtest_end_date": "2024-01-31"
}"""
    )
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--config",
            str(config_path),
            "--tickers",
            "NVDA,TSLA",
            "--benchmark",
            "SPY",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["NVDA", "TSLA"],
        "benchmark_ticker": "SPY",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "holding_days": 5,
        "top_n": 2,
    }


def test_backtest_script_runs_with_config_only(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """{
  "tickers": ["AAPL", "MSFT"],
  "benchmark": "QQQ",
  "holding_days": 7,
  "top_n": 4,
  "backtest_start_date": "2025-02-01",
  "backtest_end_date": "2025-02-28"
}"""
    )
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--config",
            str(config_path),
            "--summary-only",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark_ticker": "QQQ",
        "start_date": "2025-02-01",
        "end_date": "2025-02-28",
        "holding_days": 7,
        "top_n": 4,
    }


def test_backtest_script_fallback_derives_dates_from_lookback_days(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """{
  "tickers": ["AAPL", "MSFT"],
  "benchmark": "QQQ",
  "lookback_days": 30,
  "holding_days": 7,
  "top_n": 4
}"""
    )
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--config",
            str(config_path),
            "--summary-only",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    expected_end = date.today().isoformat()
    expected_start = (date.today() - timedelta(days=30)).isoformat()
    assert captured == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark_ticker": "QQQ",
        "start_date": expected_start,
        "end_date": expected_end,
        "holding_days": 7,
        "top_n": 4,
    }


def test_backtest_script_explicit_cli_dates_still_work_without_config(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--start-date",
            "2026-02-24",
            "--end-date",
            "2026-05-25",
            "--summary-only",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured["start_date"] == "2026-02-24"
    assert captured["end_date"] == "2026-05-25"


def test_backtest_script_accepts_summary_only(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--summary-only",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark_ticker": "SPY",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "holding_days": 5,
        "top_n": 2,
    }


def test_summary_only_suppresses_per_row_detail_output(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
                "tested_count": 2,
                "win_count": 1,
                "loss_count": 1,
                "win_rate": 0.5,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "median_return": 0.09,
                "median_excess_return": 0.07,
                "best_ticker": "AAPL",
                "worst_ticker": "MSFT",
                "best_return": 0.15,
                "worst_return": 0.05,
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-20",
                    "exit_date": "2025-01-25",
                    "ticker": "AAPL",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                }
            ],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--summary-only",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "tested_count=2" in captured.out
    assert "win_count=1" in captured.out
    assert "loss_count=1" in captured.out
    assert "median_return=0.09" in captured.out
    assert "median_excess_return=0.07" in captured.out
    assert "best_return=0.15" in captured.out
    assert "worst_return=0.05" in captured.out
    assert "recommendation_date=" not in captured.out
    assert "entry_price=" not in captured.out


def test_backtest_script_accepts_max_rows(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    captured = {}

    def fake_run_backtest(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--max-rows",
            "1",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT"],
        "benchmark_ticker": "SPY",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "holding_days": 5,
        "top_n": 2,
    }


def test_max_rows_limits_printed_detail_rows(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
                "tested_count": 3,
                "win_rate": 0.67,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "best_ticker": "AAPL",
                "worst_ticker": "MSFT",
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-20",
                    "exit_date": "2025-01-25",
                    "ticker": "AAPL",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                },
                {
                    "recommendation_date": "2025-01-21",
                    "exit_date": "2025-01-26",
                    "ticker": "MSFT",
                    "entry_price": 200.0,
                    "exit_price": 210.0,
                    "return_pct": 0.05,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.03,
                    "is_win": True,
                },
            ],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--max-rows",
            "1",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert captured.out.count("recommendation_date=") == 1


def test_default_behavior_still_prints_all_detail_rows(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
                "tested_count": 2,
                "win_rate": 0.5,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "best_ticker": "AAPL",
                "worst_ticker": "MSFT",
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-20",
                    "exit_date": "2025-01-25",
                    "ticker": "AAPL",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                },
                {
                    "recommendation_date": "2025-01-21",
                    "exit_date": "2025-01-26",
                    "ticker": "MSFT",
                    "entry_price": 200.0,
                    "exit_price": 190.0,
                    "return_pct": -0.05,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": -0.07,
                    "is_win": False,
                },
            ],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert captured.out.count("recommendation_date=") == 2


def test_backtest_script_writes_csv_when_requested(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    csv_path = tmp_path / "backtest.csv"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
                "tested_count": 1,
                "win_count": 1,
                "loss_count": 0,
                "win_rate": 1.0,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "median_return": 0.1,
                "median_excess_return": 0.08,
                "best_ticker": "AAPL",
                "worst_ticker": "AAPL",
                "best_return": 0.1,
                "worst_return": 0.1,
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-20",
                    "exit_date": "2025-01-25",
                    "ticker": "AAPL",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                }
            ],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert csv_path.exists()
    csv_text = csv_path.read_text()
    assert "recommendation_date,exit_date,ticker,entry_price,exit_price,return_pct,benchmark_return_pct,excess_return_pct,is_win" in csv_text
    assert "AAPL" in csv_text
    assert "tested_count=1" in captured.out


def test_backtest_csv_export_headers_remain_unchanged(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    csv_path = tmp_path / "backtest.csv"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
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
            },
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "1",
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    header = csv_path.read_text().splitlines()[0]
    assert header == (
        "recommendation_date,exit_date,ticker,entry_price,exit_price,"
        "return_pct,benchmark_return_pct,excess_return_pct,is_win"
    )


def test_summary_only_still_allows_backtest_csv_export(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/backtest_strategy.py"
    csv_path = tmp_path / "backtest.csv"

    def fake_run_backtest(**kwargs):
        return {
            "summary": {
                "tested_count": 1,
                "win_rate": 1.0,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "best_ticker": "AAPL",
                "worst_ticker": "AAPL",
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-20",
                    "exit_date": "2025-01-25",
                    "ticker": "AAPL",
                    "entry_price": 100.0,
                    "exit_price": 110.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                }
            ],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.backtest.run_backtest", fake_run_backtest)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--tickers",
            "AAPL,MSFT",
            "--benchmark",
            "SPY",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--holding-days",
            "5",
            "--top-n",
            "2",
            "--summary-only",
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert csv_path.exists()
    csv_text = csv_path.read_text()
    assert "AAPL" in csv_text
    assert "recommendation_date=" not in captured.out


def test_add_days_handles_timezone_datetime_string():
    assert _add_days("2026-02-24 00:00:00-05:00", 5) == "2026-03-01"


def test_run_backtest_handles_timezone_datetime_strings_in_rows():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows_with_timezone_dates(100.0, 2.0),
        "SPY": _price_rows_with_timezone_dates(100.0, 1.0),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-20",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    assert result["rows"][0]["ticker"] == "AAPL"


def test_run_backtest_normalizes_output_dates_to_yyyy_mm_dd():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows_with_timezone_dates(100.0, 2.0),
        "SPY": _price_rows_with_timezone_dates(100.0, 1.0),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-20",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    assert result["rows"][0]["recommendation_date"] == "2025-01-20"
    assert result["rows"][0]["exit_date"] == "2025-01-25"


def test_backtest_exit_date_uses_available_trading_days_not_calendar_days():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows_with_gaps(
            [
                "2025-01-16",
                "2025-01-17",
                "2025-01-20",
                "2025-01-21",
                "2025-01-22",
                "2025-01-23",
                "2025-01-24",
                "2025-01-27",
            ],
            100.0,
            2.0,
        ),
        "SPY": _price_rows_with_gaps(
            [
                "2025-01-16",
                "2025-01-17",
                "2025-01-20",
                "2025-01-21",
                "2025-01-22",
                "2025-01-23",
                "2025-01-24",
                "2025-01-27",
            ],
            100.0,
            1.0,
        ),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-20",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    assert result["rows"][0]["exit_date"] == "2025-01-27"


def test_backtest_skips_weekend_and_non_trading_gaps():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows_with_gaps(
            [
                "2025-01-14",
                "2025-01-15",
                "2025-01-16",
                "2025-01-17",
                "2025-01-21",
                "2025-01-22",
                "2025-01-23",
                "2025-01-24",
            ],
            100.0,
            2.0,
        ),
        "SPY": _price_rows_with_gaps(
            [
                "2025-01-14",
                "2025-01-15",
                "2025-01-16",
                "2025-01-17",
                "2025-01-21",
                "2025-01-22",
                "2025-01-23",
                "2025-01-24",
            ],
            100.0,
            1.0,
        ),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-16",
        end_date="2025-01-16",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    assert result["rows"][0]["exit_date"] == "2025-01-24"


def test_backtest_skips_row_when_future_trading_days_are_insufficient():
    tickers = ["AAPL", "SPY"]
    price_history = {
        "AAPL": _price_rows_with_gaps(
            ["2025-01-20", "2025-01-21", "2025-01-22"],
            100.0,
            2.0,
        ),
        "SPY": _price_rows_with_gaps(
            ["2025-01-20", "2025-01-21", "2025-01-22"],
            100.0,
            1.0,
        ),
    }

    result = run_backtest(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-20",
        end_date="2025-01-20",
        holding_days=5,
        top_n=1,
        price_history_by_ticker=price_history,
    )

    assert result["summary"]["tested_count"] == 0
    assert result["rows"] == []


def _price_rows(start_close, close_step):
    rows = []
    close = start_close
    for day in range(30):
        rows.append(
            {
                "date": f"2025-01-{day + 1:02d}",
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000 + day * 10,
                "ticker": "IGNORED",
            }
        )
        close += close_step
    return rows


def _price_rows_with_timezone_dates(start_close, close_step):
    rows = []
    close = start_close
    for day in range(30):
        rows.append(
            {
                "date": f"2025-01-{day + 1:02d} 00:00:00-05:00",
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000 + day * 10,
                "ticker": "IGNORED",
            }
        )
        close += close_step
    return rows


def _price_rows_with_gaps(dates, start_close, close_step):
    rows = []
    close = start_close
    for index, day in enumerate(dates):
        rows.append(
            {
                "date": day,
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000 + index * 10,
                "ticker": "IGNORED",
            }
        )
        close += close_step
    return rows
