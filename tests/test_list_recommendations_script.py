from pathlib import Path
import runpy

from src.database import initialize_database, save_recommendations


def test_list_recommendations_script_lists_saved_rows(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[
            {"ticker": "AAPL", "score": 0.91, "rank": 1, "entry_price": 150.0},
            {"ticker": "MSFT", "score": 0.83, "rank": 2, "entry_price": 310.0},
        ],
    )

    monkeypatch.setenv("STOCK_RESEARCH_DB_PATH", str(db_path))
    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "2025-01-10" in captured.out
    assert "1" in captured.out
    assert "AAPL" in captured.out
    assert "0.91" in captured.out
    assert "150.0" in captured.out
    assert "v1" in captured.out


def test_list_recommendations_script_handles_empty_database(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)

    monkeypatch.setenv("STOCK_RESEARCH_DB_PATH", str(db_path))
    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "No recommendations found." in captured.out


def test_list_recommendations_script_can_run_with_temporary_database(monkeypatch, tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)

    monkeypatch.setenv("STOCK_RESEARCH_DB_PATH", str(db_path))
    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    runpy.run_path(str(script_path), run_name="__main__")


def test_list_recommendations_output_includes_required_fields(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v2",
        recommendations=[
            {"ticker": "NVDA", "score": 0.77, "rank": 3, "entry_price": 420.0},
        ],
    )

    monkeypatch.setenv("STOCK_RESEARCH_DB_PATH", str(db_path))
    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "trading_date" in captured.out
    assert "rank" in captured.out
    assert "symbol" in captured.out or "ticker" in captured.out
    assert "score" in captured.out
    assert "entry_price" in captured.out
    assert "signal_strength" in captured.out
    assert "strategy_version" in captured.out


def test_list_recommendations_script_accepts_argparse_options(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "custom.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[
            {"ticker": "AAPL", "score": 0.91, "rank": 1, "entry_price": 150.0},
            {"ticker": "MSFT", "score": 0.83, "rank": 2, "entry_price": 310.0},
        ],
    )

    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--db",
            str(db_path),
            "--limit",
            "1",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "AAPL" in captured.out or "MSFT" in captured.out
    assert not ("AAPL" in captured.out and "MSFT" in captured.out)


def test_list_recommendations_script_writes_csv_when_requested(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "custom.db"
    csv_path = tmp_path / "recommendations.csv"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[
            {
                "ticker": "AAPL",
                "score": 0.91,
                "rank": 1,
                "entry_price": 150.0,
                "reasons": ["return_20d contributed 0.5"],
                "risk_notes": ["20-day volatility is elevated"],
                "signal_strength": "positive",
            },
        ],
    )

    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--db",
            str(db_path),
            "--csv",
            str(csv_path),
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert csv_path.exists()
    csv_text = csv_path.read_text()
    assert (
        "trading_date,rank,symbol,score,entry_price,signal_strength,reasons,risk_notes,strategy_version"
        in csv_text
    )
    assert "AAPL" in csv_text
    assert "positive" in csv_text
    assert "return_20d contributed 0.5" in csv_text
    assert "20-day volatility is elevated" in csv_text


def test_list_recommendations_details_shows_reasons_and_risk_notes(
    monkeypatch, capsys, tmp_path
):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[
            {
                "ticker": "AAPL",
                "score": 0.91,
                "rank": 1,
                "entry_price": 150.0,
                "reasons": ["return_20d contributed 0.5"],
                "risk_notes": ["20-day volatility is elevated"],
                "signal_strength": "positive",
            },
        ],
    )

    script_path = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script_path),
            "--db",
            str(db_path),
            "--details",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "interpretation=Positive but moderate signal today." in captured.out
    assert "reasons=['return_20d contributed 0.5']" in captured.out
    assert "risk_notes=['20-day volatility is elevated']" in captured.out
    assert "weak means score <= 0" in captured.out
