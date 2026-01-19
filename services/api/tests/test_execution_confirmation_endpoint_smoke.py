from __future__ import annotations

from fastapi.testclient import TestClient


def test_execution_confirm_endpoint_smoke(monkeypatch):
    # Import store module first so we can patch it
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    # Execution exists
    def _fake_get_run(run_id: str):
        assert run_id == "exec1"
        return {"id": "exec1", "kind": "saw_batch_execution", "payload": {"status": "OK"}}

    # Store confirmation artifact
    def _fake_store_artifact(**kwargs):
        assert kwargs["kind"] == "saw_batch_execution_confirmation"
        assert kwargs["parent_id"] == "exec1"
        assert kwargs["payload"]["operator_id"] == "op1"
        assert kwargs["payload"]["checks"]["material_loaded"] is True
        return "conf1"

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/confirm",
        json={
            "batch_execution_artifact_id": "exec1",
            "session_id": "s1",
            "batch_label": "b1",
            "operator_id": "op1",
            "checks": {
                "material_loaded": True,
                "clamps_engaged": True,
                "blade_verified": True,
                "zero_set": True,
                "dust_collection_on": True,
            },
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["confirmation_artifact_id"] == "conf1"
    assert data["batch_execution_artifact_id"] == "exec1"
    assert data["state"] == "CONFIRMED"


def test_execution_confirm_blocks_when_any_check_false(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": "exec1", "kind": "saw_batch_execution"}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/confirm",
        json={
            "batch_execution_artifact_id": "exec1",
            "session_id": "s1",
            "batch_label": "b1",
            "operator_id": "op1",
            "checks": {
                "material_loaded": True,
                "clamps_engaged": False,
            },
        },
    )
    assert r.status_code == 409
    assert "blocked" in r.text.lower()
