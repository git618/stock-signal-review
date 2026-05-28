from pathlib import Path
import runpy

from src.database import initialize_database, save_recommendations


def test_generate_report_script_exists_and_accepts_output(monkeypatch, tmp_path):
    db_path = tmp_path / "research.db"
    output_path = tmp_path / "report.html"
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_report.py"
    _write_config(tmp_path / "default.json", db_path=db_path)
    _write_config(tmp_path / "momentum.json", db_path=db_path, version="momentum-v1")
    _write_config(tmp_path / "low_vol.json", db_path=db_path, version="low-vol-v1")
    initialize_database(db_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--output",
            str(output_path),
            "--db",
            str(db_path),
            "--config",
            str(tmp_path / "default.json"),
            "--strategy-configs",
            str(tmp_path / "default.json"),
            str(tmp_path / "momentum.json"),
            str(tmp_path / "low_vol.json"),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert output_path.exists()


def test_generate_report_creates_html_with_required_sections(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "research.db"
    output_path = tmp_path / "report.html"
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_report.py"
    config_path = _write_config(tmp_path / "default.json", db_path=db_path)
    strategy_paths = [
        config_path,
        _write_config(tmp_path / "momentum.json", db_path=db_path, version="momentum-v1"),
        _write_config(tmp_path / "low_vol.json", db_path=db_path, version="low-vol-v1"),
    ]
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[
            {"ticker": "AAPL", "score": 0.91, "rank": 1, "entry_price": 150.0},
        ],
    )

    monkeypatch.setattr(
        "src.review.generate_weekly_review",
        lambda **kwargs: {
            "summary": {
                "reviewed_count": 1,
                "win_count": 1,
                "loss_count": 0,
                "win_rate": 1.0,
                "average_return": 0.1,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.08,
                "best_ticker": "AAPL",
                "worst_ticker": "AAPL",
            },
            "rows": [
                {
                    "ticker": "AAPL",
                    "entry_price": 150.0,
                    "exit_price": 165.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                }
            ],
        },
    )
    monkeypatch.setattr(
        "src.backtest.run_backtest",
        lambda **kwargs: {
            "summary": {
                "tested_count": 2,
                "win_count": 1,
                "loss_count": 1,
                "win_rate": 0.5,
                "average_return": 0.04,
                "average_benchmark_return": 0.02,
                "average_excess_return": 0.02,
                "median_return": 0.04,
                "median_excess_return": 0.02,
                "best_ticker": "AAPL",
                "worst_ticker": "MSFT",
                "best_return": 0.1,
                "worst_return": -0.02,
            },
            "rows": [
                {
                    "recommendation_date": "2025-01-10",
                    "exit_date": "2025-01-17",
                    "ticker": "AAPL",
                    "entry_price": 150.0,
                    "exit_price": 165.0,
                    "return_pct": 0.1,
                    "benchmark_return_pct": 0.02,
                    "excess_return_pct": 0.08,
                    "is_win": True,
                }
            ],
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--output",
            str(output_path),
            "--db",
            str(db_path),
            "--config",
            str(config_path),
            "--strategy-configs",
            *(str(path) for path in strategy_paths),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()
    html = output_path.read_text()

    assert f"Wrote report: {output_path}" in captured.out
    assert "Stock Signal Research Report" in html
    assert "Generated:" in html
    assert "Saved Recommendations Summary" in html
    assert "Weekly Review Summary" in html
    assert "Backtest Summary" in html
    assert "Strategy Comparison Summary" in html


def test_generate_report_handles_empty_data_gracefully(monkeypatch, tmp_path):
    db_path = tmp_path / "research.db"
    output_path = tmp_path / "report.html"
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_report.py"
    config_path = _write_config(tmp_path / "default.json", db_path=db_path)
    initialize_database(db_path)

    monkeypatch.setattr(
        "src.review.generate_weekly_review",
        lambda **kwargs: {"summary": {"reviewed_count": 0}, "rows": []},
    )
    monkeypatch.setattr(
        "src.backtest.run_backtest",
        lambda **kwargs: {
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
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--output",
            str(output_path),
            "--db",
            str(db_path),
            "--config",
            str(config_path),
            "--strategy-configs",
            str(config_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    html = output_path.read_text()

    assert "No recommendations found." in html
    assert "No recommendations ready for review." in html
    assert "No backtest rows available." in html
    assert "No strategy results to display." in html


def test_data_html_is_ignored_by_git():
    gitignore_path = Path(__file__).resolve().parent.parent / ".gitignore"
    gitignore_text = gitignore_path.read_text()

    assert "data/*.html" in gitignore_text


def _write_config(path, db_path, version="v1"):
    path.write_text(
        "{\n"
        '  "tickers": ["AAPL", "MSFT"],\n'
        '  "benchmark": "SPY",\n'
        '  "lookback_days": 30,\n'
        '  "holding_days": 5,\n'
        '  "top_n": 2,\n'
        '  "review_horizon_days": 5,\n'
        f'  "database_path": "{db_path}",\n'
        '  "backtest_start_date": "2025-01-01",\n'
        '  "backtest_end_date": "2025-01-31",\n'
        '  "strategy": {\n'
        f'    "version": "{version}",\n'
        '    "weights": {\n'
        '      "return_20d": 0.5,\n'
        '      "return_5d": 0.3,\n'
        '      "volume_ratio_20d": 0.2\n'
        "    }\n"
        "  }\n"
        "}\n"
    )
    return path
