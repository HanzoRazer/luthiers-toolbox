from __future__ import annotations

from fastapi.testclient import TestClient


def test_latest_metrics_by_execution_endpoint_is_mounted():
    from app.main import app

    c = TestClient(app)
    r = c.get("/api/_meta/routing-truth")
    assert r.status_code == 200
    paths = {x["path"] for x in r.json().get("routes", []) if isinstance(x, dict) and "path" in x}
    assert "/api/saw/batch/execution/metrics/latest" in paths


def test_latest_metrics_by_execution_returns_shape(monkeypatch):
    """
    Smoke: endpoint responds and returns the expected keys.
    """
    from app.main import app
    from app.rmos.runs_v2 import store as runs_store

    # Metrics artifact for exec1
    mx1 = {
        "id": "mx1",
        "kind": "saw_batch_execution_metrics",
        "created_utc": "2026-01-01T00:03:00+00:00",
        "parent_id": "exec1",
        "payload": {"batch_execution_artifact_id": "exec1", "kpis": {"totals": {"job_log_count": 3}}},
    }

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [mx1]}

    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.get("/api/saw/batch/execution/metrics/latest?batch_execution_artifact_id=exec1")
    assert r.status_code == 200
    data = r.json()
    assert data["batch_execution_artifact_id"] == "exec1"
    assert data["latest_metrics_artifact_id"] == "mx1"
    assert data["kpis"]["totals"]["job_log_count"] == 3


def test_latest_metrics_by_execution_returns_null_when_no_metrics(monkeypatch):
    """
    If no metrics exist for the execution, endpoint returns nulls (not 404).
    """
    from app.main import app
    from app.rmos.runs_v2 import store as runs_store

    def _fake_list_runs_filtered(**kwargs):
        return {"items": []}

    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.get("/api/saw/batch/execution/metrics/latest?batch_execution_artifact_id=exec_no_metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["batch_execution_artifact_id"] == "exec_no_metrics"
    assert data["latest_metrics_artifact_id"] is None
    assert data["kpis"] is None
