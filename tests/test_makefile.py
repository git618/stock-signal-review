from pathlib import Path


def test_makefile_exists():
    assert (Path(__file__).resolve().parent.parent / "Makefile").exists()


def test_makefile_contains_required_targets():
    makefile_text = _makefile_text()

    for target in ["test:", "reset:", "daily:", "list:", "weekly:", "backtest:", "smoke:"]:
        assert target in makefile_text


def test_test_target_uses_project_python_and_pytest_q():
    makefile_text = _makefile_text()
    assert "./.venv/bin/python -m pytest -q" in makefile_text


def test_backtest_target_includes_summary_only():
    makefile_text = _makefile_text()
    assert "scripts/backtest_strategy.py" in makefile_text
    assert "--summary-only" in makefile_text


def test_smoke_target_runs_smoke_yfinance_script():
    makefile_text = _makefile_text()
    assert "scripts/smoke_yfinance.py" in makefile_text


def _makefile_text():
    return (Path(__file__).resolve().parent.parent / "Makefile").read_text()
