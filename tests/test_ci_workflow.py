from pathlib import Path


def test_ci_workflow_file_exists():
    workflow_path = Path(__file__).resolve().parent.parent / ".github/workflows/ci.yml"

    assert workflow_path.exists()


def test_ci_workflow_uses_checkout_and_setup_python():
    workflow_text = _read_workflow()

    assert "actions/checkout" in workflow_text
    assert "actions/setup-python" in workflow_text


def test_ci_workflow_runs_pytest_q():
    workflow_text = _read_workflow()

    assert "python -m pytest -q" in workflow_text


def test_ci_workflow_triggers_on_push_and_pull_request():
    workflow_text = _read_workflow()

    assert "push:" in workflow_text
    assert "pull_request:" in workflow_text


def _read_workflow():
    workflow_path = Path(__file__).resolve().parent.parent / ".github/workflows/ci.yml"
    return workflow_path.read_text()
