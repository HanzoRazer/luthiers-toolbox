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

import pytest


def test_api_dir_is_services_api_with_app_package():
    api_dir = gdr._api_dir()
    assert api_dir.is_dir()
    assert api_dir.name == "api"
    assert (api_dir / "app" / "ci" / "generate_debt_report.py").exists()
    # Regression: the old cwd was _repo_root()/services/api, i.e.
    # services/api/services/api — which does not exist.
    assert not (api_dir / "services" / "api" / "app").exists()


def test_run_check_resolves_cwd_and_returns_data():
    # bare_except needs no radon and is fast. Before the cwd fix this returned
    # {"error": ...} because the subprocess cwd did not exist.
    result = gdr.run_check("app.ci.check_bare_except")
    assert "error" not in result, f"run_check failed (cwd bug regressed?): {result}"
    assert isinstance(result, list)


def test_summary_has_no_spurious_error_rows():
    pytest.importorskip("radon")  # complexity / file-size rows need radon
    report = gdr.generate_report()
    summary = report.split("## Details")[0]
    # No check should render the spurious ERROR placeholder on a runnable tree.
    assert "| ERROR |" not in summary, summary
    # Ratchet checks reflect the gate-step conclusion (PASS on a clean tree).
    assert "Complexity (>15) | PASS" in summary
    assert "File size (>500) | PASS" in summary
