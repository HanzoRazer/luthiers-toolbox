from __future__ import annotations

from fastapi.testclient import TestClient


def test_latest_metrics_by_batch_returns_shape(monkeypatch):
    """
    Smoke: endpoint responds and returns the expected keys.
    Does not require DB; stubs list_runs_filtered.
    """
    from app.main import app

    # Minimal artifacts in the batch: execution + metrics
    exec1 = {"id": "exec1", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:02:00+00:00"}
    mx1 = {
        "id": "mx1",
        "kind": "saw_batch_execution_metrics",
        "created_utc": "2026-01-01T00:03:00+00:00",
        "parent_id": "exec1",
        "payload": {"batch_execution_artifact_id": "exec1", "kpis": {"totals": {"job_log_count": 1}}},
    }

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [exec1, mx1]}

    monkeypatch.setattr("app.rmos.runs_v2.store.list_runs_filtered", _fake_list_runs_filtered)

    c = TestClient(app)
    r = c.get("/api/saw/batch/execution/metrics/latest-by-batch?session_id=s1&batch_label=b1")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == "s1"
    assert data["batch_label"] == "b1"
    assert data["latest_execution_artifact_id"] == "exec1"
    assert data["latest_metrics_artifact_id"] == "mx1"
    assert isinstance(data.get("kpis"), dict)
