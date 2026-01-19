from __future__ import annotations

from fastapi.testclient import TestClient


def test_execution_abort_endpoint_writes_abort_artifact(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    # Execution exists
    def _fake_get_run(run_id: str):
        assert run_id == "exec1"
        return {"id": "exec1", "kind": "saw_batch_execution", "payload": {"status": "OK"}}

    # Abort artifact write
    def _fake_store_artifact(**kwargs):
        assert kwargs["kind"] == "saw_batch_execution_abort"
        assert kwargs["parent_id"] == "exec1"
        assert kwargs["session_id"] == "s1"
        assert kwargs["batch_label"] == "b1"
        payload = kwargs["payload"]
        assert payload["state"] == "ABORTED"
        assert payload["reason"] == "JAM"
        assert payload["operator_id"] == "op1"
        assert "notes" in payload
        return "abort1"

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/abort",
        json={
            "batch_execution_artifact_id": "exec1",
            "session_id": "s1",
            "batch_label": "b1",
            "reason": "JAM",
            "notes": "Blade stalled on entry.",
            "operator_id": "op1",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["batch_execution_artifact_id"] == "exec1"
    assert data["abort_artifact_id"] == "abort1"
    assert data["state"] == "ABORTED"


def test_execution_abort_404_when_execution_missing(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return None

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/abort",
        json={
            "batch_execution_artifact_id": "missing",
            "session_id": "s1",
            "batch_label": "b1",
            "reason": "OTHER",
            "notes": "No execution existed.",
        },
    )
    assert r.status_code == 404
