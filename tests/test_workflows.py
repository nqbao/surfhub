import yaml
from pathlib import Path


WORKFLOWS_DIR = Path(__file__).parent.parent / ".github" / "workflows"


def test_workflow_files_exist():
    assert WORKFLOWS_DIR.is_dir()
    files = list(WORKFLOWS_DIR.glob("*.yml"))
    assert len(files) > 0


def test_test_workflow_valid_yaml():
    path = WORKFLOWS_DIR / "test.yml"
    assert path.exists()
    content = yaml.safe_load(path.read_text())
    assert content["name"] == "test"
    assert content["jobs"]["test"]["runs-on"] == "ubuntu-latest"


def test_test_workflow_python_version():
    path = WORKFLOWS_DIR / "test.yml"
    content = yaml.safe_load(path.read_text())
    for step in content["jobs"]["test"]["steps"]:
        if "setup-python" in step.get("uses", ""):
            assert step["with"]["python-version"] == "3.11"


def test_gitleaks_workflow_valid_yaml():
    path = WORKFLOWS_DIR / "gitleaks.yml"
    assert path.exists()
    content = yaml.safe_load(path.read_text())
    assert content["name"] == "gitleaks"
    assert content[True] == ["pull_request", "push", "workflow_dispatch"]
    assert content["jobs"]["scan"]["runs-on"] == "ubuntu-latest"


def test_gitleaks_uses_gitleaks_action():
    path = WORKFLOWS_DIR / "gitleaks.yml"
    content = yaml.safe_load(path.read_text())
    steps = content["jobs"]["scan"]["steps"]
    uses_values = [step.get("uses", "") for step in steps]
    assert any("gitleaks/gitleaks-action" in u for u in uses_values)
