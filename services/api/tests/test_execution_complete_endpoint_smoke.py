from __future__ import annotations

from fastapi.testclient import TestClient


def test_execution_complete_endpoint_writes_complete_artifact(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        assert run_id == "exec1"
        return {"id": "exec1", "kind": "saw_batch_execution", "payload": {"status": "OK"}}

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind")
        if kind == "saw_batch_job_log":
            return {
                "items": [
                    {
                        "id": "jl1",
                        "kind": kind,
                        "parent_id": "exec1",
                        "payload": {
                            "status": "OK",
                            "metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 12.0},
                        },
                    }
                ]
            }
        return {"items": []}

    def _fake_store_artifact(**kwargs):
        assert kwargs["kind"] == "saw_batch_execution_complete"
        assert kwargs["parent_id"] == "exec1"
        assert kwargs["session_id"] == "s1"
        assert kwargs["batch_label"] == "b1"

        payload = kwargs["payload"]
        assert payload["state"] == "COMPLETED"
        assert payload["outcome"] == "SUCCESS"
        assert payload["operator_id"] == "op1"
        assert "notes" in payload
        assert payload["checklist"]["all_cuts_complete"] is True
        assert payload["checklist"]["workpiece_inspected"] is True
        return "complete1"

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec1",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
            "notes": "All cuts completed successfully.",
            "operator_id": "op1",
            "checklist": {
                "all_cuts_complete": True,
                "material_removed": True,
                "workpiece_inspected": True,
                "area_cleared": True,
            },
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["batch_execution_artifact_id"] == "exec1"
    assert data["complete_artifact_id"] == "complete1"
    assert data["state"] == "COMPLETED"


def test_execution_complete_404_when_execution_missing(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return None

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "missing",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
            "notes": "No execution existed.",
        },
    )
    assert r.status_code == 404


def test_execution_complete_without_checklist(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": "exec2", "kind": "saw_batch_execution", "payload": {}}

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind")
        if kind == "saw_batch_job_log":
            return {
                "items": [
                    {
                        "id": "jl2",
                        "kind": kind,
                        "parent_id": "exec2",
                        "payload": {
                            "status": "OK",
                            "metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 5.0},
                        },
                    }
                ]
            }
        return {"items": []}

    def _fake_store_artifact(**kwargs):
        payload = kwargs["payload"]
        assert payload["state"] == "COMPLETED"
        assert payload["outcome"] == "PARTIAL"
        assert "checklist" not in payload or payload["checklist"] is None
        return "complete2"

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec2",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "PARTIAL",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "COMPLETED"


def test_execution_complete_409_when_execution_already_aborted(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": run_id, "kind": "saw_batch_execution", "payload": {}}

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind")
        if kind == "saw_batch_execution_abort":
            return {"items": [{"id": "ab1", "kind": kind, "parent_id": "exec3"}]}
        if kind == "saw_batch_execution_complete":
            return {"items": []}
        return {"items": []}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec3",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
        },
    )
    assert r.status_code == 409


def test_execution_complete_409_when_execution_already_completed(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": run_id, "kind": "saw_batch_execution", "payload": {}}

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind")
        if kind == "saw_batch_execution_abort":
            return {"items": []}
        if kind == "saw_batch_execution_complete":
            return {"items": [{"id": "c1", "kind": kind, "parent_id": "exec4"}]}
        return {"items": []}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec4",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
        },
    )
    assert r.status_code == 409


def test_execution_complete_409_when_no_job_logs(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": run_id, "kind": "saw_batch_execution", "payload": {}}

    def _fake_list_runs_filtered(**kwargs):
        # No job logs returned for this session/batch
        kind = kwargs.get("kind")
        if kind in ("saw_batch_execution_abort", "saw_batch_execution_complete", "saw_batch_job_log"):
            return {"items": []}
        return {"items": []}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec_no_logs",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
        },
    )
    assert r.status_code == 409
    assert "qualifying job log" in r.json()["detail"]


def test_execution_complete_409_when_job_log_not_qualifying(monkeypatch):
    """Job log exists but is ABORTED or has no work metrics — should reject."""
    from app.rmos.runs_v2 import store as runs_store
    from app.main import app

    def _fake_get_run(run_id: str):
        return {"id": run_id, "kind": "saw_batch_execution", "payload": {}}

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind")
        if kind == "saw_batch_execution_abort":
            return {"items": []}
        if kind == "saw_batch_execution_complete":
            return {"items": []}
        if kind == "saw_batch_job_log":
            # Non-qualifying: ABORTED status OR metrics show no work
            return {
                "items": [
                    {
                        "id": "jl_bad",
                        "kind": kind,
                        "parent_id": "exec_bad",
                        "payload": {"status": "ABORTED", "metrics": {"parts_ok": 0, "parts_scrap": 0}},
                    }
                ]
            }
        return {"items": []}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.post(
        "/api/saw/batch/execution/complete",
        json={
            "batch_execution_artifact_id": "exec_bad",
            "session_id": "s1",
            "batch_label": "b1",
            "outcome": "SUCCESS",
        },
    )
    assert r.status_code == 409
    assert "qualifying job log" in r.json()["detail"]
