from __future__ import annotations


def test_resolve_latest_metrics_by_decision_prefers_latest_execution_then_latest_metrics(monkeypatch):
    from app.saw_lab import metrics_lookup_service
    from app.rmos.runs_v2 import store as runs_store

    # Two executions for same decision; newest is exec2
    exec1 = {"id": "exec1", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:01:00+00:00", "payload": {"decision_artifact_id": "dec1"}}
    exec2 = {"id": "exec2", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:02:00+00:00", "payload": {"decision_artifact_id": "dec1"}}

    # Metrics exist for exec2 only
    mx1 = {"id": "mx1", "kind": "saw_batch_execution_metrics", "created_utc": "2026-01-01T00:03:00+00:00", "parent_id": "exec2", "payload": {"batch_execution_artifact_id": "exec2", "kpis": {"totals": {"job_log_count": 2}}}}

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [exec1, exec2, mx1]}

    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    out = metrics_lookup_service.resolve_latest_metrics_by_decision(decision_artifact_id="dec1", session_id="s1", batch_label="b1", tool_kind="saw")
    assert out["latest_execution_artifact_id"] == "exec2"
    assert out["latest_metrics_artifact_id"] == "mx1"
    assert out["kpis"]["totals"]["job_log_count"] == 2
