"""Guard tests for the debt-report summary generator.

Regression lock for the ``run_check`` cwd bug: ``generate_debt_report`` re-runs
each debt check in a subprocess, and a wrong cwd (``services/api/services/api``,
produced by appending ``/services/api`` to ``_repo_root()`` which itself already
resolved to ``services/api``) made every subprocess raise. The summary then
rendered a spurious ``| <check> | ERROR | - | - |`` row for every check even
when the ``debt-gates`` job passed — misleading reviewers into reading a green
gate as red.

Run: services/api/.venv pytest tests/test_generate_debt_report.py -q
"""
from app.ci import generate_debt_report as gdr


def _summary_rows(report: str) -> dict[str, list[str]]:
    rows = {}
    for line in report.split("## Details")[0].splitlines():
        if not line.startswith("| ") or line.startswith("| Check ") or line.startswith("|-------"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows[cells[0]] = cells[1:]
    return rows


def test_api_dir_is_services_api_with_app_package():
    api_dir = gdr._api_dir()
    assert api_dir.is_dir()
    assert api_dir.name == "api"
    assert (api_dir / "app" / "ci" / "generate_debt_report.py").exists()
    # Regression: the old cwd was _repo_root()/services/api, i.e.
    # services/api/services/api — which does not exist.
    assert not (api_dir / "services" / "api" / "app").exists()


def test_api_dir_walks_up_from_nested_file(tmp_path):
    api_dir = tmp_path / "services" / "api"
    nested = api_dir / "app" / "ci" / "nested" / "tool.py"
    nested.parent.mkdir(parents=True)
    (api_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")

    assert gdr._api_dir(nested) == api_dir


def test_run_check_resolves_cwd_and_returns_data():
    # bare_except needs no radon and is fast. Before the cwd fix this returned
    # {"error": ...} because the subprocess cwd did not exist.
    result = gdr.run_check("app.ci.check_bare_except")
    assert "error" not in result, f"run_check failed (cwd bug regressed?): {result}"
    assert isinstance(result, list)


def test_run_check_reports_missing_required_baseline(tmp_path, monkeypatch):
    api_dir = tmp_path / "api"
    (api_dir / "app" / "ci").mkdir(parents=True)
    (api_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    monkeypatch.setattr(gdr, "_api_dir", lambda: api_dir)

    result = gdr.run_check(
        "app.ci.check_complexity",
        required_paths=[gdr.COMPLEXITY_BASELINE],
    )

    assert result["exit_code"] == -1
    assert "complexity_baseline.json" in result["error"]


def test_run_check_preserves_json_from_nonzero_subprocess(tmp_path, monkeypatch):
    api_dir = tmp_path / "api"
    api_dir.mkdir()
    monkeypatch.setattr(gdr, "_api_dir", lambda: api_dir)

    class Result:
        stdout = '[{"file": "x.py"}]'
        stderr = ""
        returncode = 1

    monkeypatch.setattr(gdr.subprocess, "run", lambda *args, **kwargs: Result())

    assert gdr.run_check("app.ci.check_complexity") == [{"file": "x.py"}]


def test_run_check_reports_nonzero_without_json(tmp_path, monkeypatch):
    api_dir = tmp_path / "api"
    api_dir.mkdir()
    monkeypatch.setattr(gdr, "_api_dir", lambda: api_dir)

    class Result:
        stdout = ""
        stderr = "boom"
        returncode = 2

    monkeypatch.setattr(gdr.subprocess, "run", lambda *args, **kwargs: Result())

    assert gdr.run_check("app.ci.check_complexity") == {"error": "boom", "exit_code": 2}


def test_summary_has_no_spurious_error_rows(monkeypatch):
    def fake_run_check(module, extra_args=None, required_paths=None):
        if module == "app.ci.fence_checker_v2":
            return {"failed": 0}
        if module == "app.ci.check_duplication":
            return {
                "passed": True,
                "stats": {"clone_groups": 0, "duplicate_lines": 0},
                "duplicates": [],
            }
        return []

    monkeypatch.setattr(gdr, "run_check", fake_run_check)

    report = gdr.generate_report()
    summary = report.split("## Details")[0]
    rows = _summary_rows(report)
    # No check should render the spurious ERROR placeholder on a runnable tree.
    assert "| ERROR |" not in summary, summary
    # Ratchet checks reflect the gate-step conclusion (PASS on a clean tree).
    assert rows["Complexity (>15)"][0] == "PASS"
    assert rows["File size (>500)"][0] == "PASS"


def test_generate_report_invokes_duplication_with_workflow_threshold(monkeypatch):
    calls = []

    def fake_run_check(module, extra_args=None, required_paths=None):
        calls.append((module, extra_args, required_paths))
        if module == "app.ci.fence_checker_v2":
            return {"failed": 0}
        if module == "app.ci.check_duplication":
            return {
                "passed": True,
                "stats": {"clone_groups": 0, "duplicate_lines": 0},
                "duplicates": [],
            }
        return []

    monkeypatch.setattr(gdr, "run_check", fake_run_check)

    rows = _summary_rows(gdr.generate_report())

    assert any(
        module == "app.ci.check_duplication"
        and args == ["--threshold", gdr.DUPLICATION_THRESHOLD]
        for module, args, _required_paths in calls
    )
    assert rows["Duplication"][2] == f"{gdr.DUPLICATION_THRESHOLD} groups"
