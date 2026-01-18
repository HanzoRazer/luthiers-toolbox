from __future__ import annotations

from fastapi.testclient import TestClient


def test_start_execution_from_toolpaths_blocks_when_lint_fails(monkeypatch):
    # Import the source modules where functions are defined
    from app.saw_lab import toolpaths_lint_service
    from app.rmos.runs_v2 import store as runs_store

    def _fake_write_lint(**kwargs):
        return {
            "lint_artifact_id": "lint_bad",
            "result": {"ok": False, "errors": ["Missing G21"], "warnings": [], "summary": {}},
        }

    def _fake_store_artifact(**kwargs):
        # execution artifact must still be written
        assert kwargs["kind"] == "saw_batch_execution"
        assert kwargs["payload"]["status"] == "BLOCKED"
        return "exec_blocked_1"

    # Patch on the source module (where the function is defined)
    monkeypatch.setattr(
        toolpaths_lint_service,
        "write_toolpaths_lint_report_artifact",
        _fake_write_lint,
    )
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)

    from app.main import app

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/start-from-toolpaths",
        json={
            "session_id": "s1",
            "batch_label": "b1",
            "toolpaths_artifact_id": "tp1",
            "validate_first": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "BLOCKED"
    assert data["lint_artifact_id"] == "lint_bad"
    assert data["batch_execution_artifact_id"] == "exec_blocked_1"
