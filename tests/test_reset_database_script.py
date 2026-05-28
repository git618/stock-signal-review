from pathlib import Path
import runpy
import sqlite3

from src.database import get_recommendations, initialize_database, save_recommendations


def test_reset_database_recreates_schema_for_existing_database(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "dev.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.91, "rank": 1}],
    )

    script_path = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    monkeypatch.setattr("sys.argv", [str(script_path), "--db", str(db_path)])

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert db_path.exists()
    assert get_recommendations(db_path) == []
    table_names = _table_names(db_path)
    assert {"daily_prices", "recommendations"}.issubset(table_names)
    assert "Database reset complete" in captured.out


def test_reset_database_works_when_database_file_does_not_exist(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "missing.db"
    script_path = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    monkeypatch.setattr("sys.argv", [str(script_path), "--db", str(db_path)])

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert db_path.exists()
    assert get_recommendations(db_path) == []
    assert "Database reset complete" in captured.out


def test_reset_database_creates_missing_default_parent_directory(
    monkeypatch, capsys, tmp_path
):
    reset_script = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    target_db_path = tmp_path / "data" / "stock_research.db"

    monkeypatch.setattr("src.config.DEFAULT_DB_PATH", target_db_path)
    monkeypatch.setattr("sys.argv", [str(reset_script)])

    runpy.run_path(str(reset_script), run_name="__main__")
    captured = capsys.readouterr()

    assert target_db_path.exists()
    assert target_db_path.parent.exists()
    assert "Database reset complete" in captured.out


def test_reset_database_accepts_db_argument(monkeypatch, tmp_path):
    db_path = tmp_path / "custom.db"
    script_path = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    monkeypatch.setattr("sys.argv", [str(script_path), "--db", str(db_path)])

    runpy.run_path(str(script_path), run_name="__main__")

    assert db_path.exists()


def test_reset_database_leaves_empty_recommendations_after_reset(monkeypatch, tmp_path):
    db_path = tmp_path / "dev.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.91, "rank": 1}],
    )

    script_path = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    monkeypatch.setattr("sys.argv", [str(script_path), "--db", str(db_path)])

    runpy.run_path(str(script_path), run_name="__main__")

    assert get_recommendations(db_path) == []


def test_reset_script_default_database_path_matches_list_script_default_database_path():
    reset_script = (
        Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    ).read_text()
    list_script = (
        Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"
    ).read_text()

    assert 'data/stock_research.db' in reset_script
    assert 'data/stock_research.db' in list_script


def test_reset_script_clears_rows_visible_to_list_script_with_default_paths(
    monkeypatch, capsys, tmp_path
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "stock_research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.91, "rank": 1}],
    )

    reset_script = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    list_script = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", [str(reset_script)])
    runpy.run_path(str(reset_script), run_name="__main__")

    monkeypatch.setattr("sys.argv", [str(list_script)])
    runpy.run_path(str(list_script), run_name="__main__")
    captured = capsys.readouterr()

    assert "No recommendations found." in captured.out


def test_list_script_prints_no_recommendations_immediately_after_default_reset(
    monkeypatch, capsys, tmp_path
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "stock_research.db"
    initialize_database(db_path)

    reset_script = Path(__file__).resolve().parent.parent / "scripts/reset_database.py"
    list_script = Path(__file__).resolve().parent.parent / "scripts/list_recommendations.py"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", [str(reset_script)])
    runpy.run_path(str(reset_script), run_name="__main__")

    monkeypatch.setattr("sys.argv", [str(list_script)])
    runpy.run_path(str(list_script), run_name="__main__")
    captured = capsys.readouterr()

    assert "No recommendations found." in captured.out


def _table_names(db_path):
    connection = sqlite3.connect(db_path)
    try:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()
