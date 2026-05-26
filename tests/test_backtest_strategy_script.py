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
    assert "best_ticker" in result["summary"]
    assert "worst_ticker" in result["summary"]


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
