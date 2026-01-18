from __future__ import annotations


def test_resolve_latest_metrics_for_batch_picks_latest_execution_then_metrics(monkeypatch):
    from app.saw_lab.latest_batch_chain_service import resolve_latest_metrics_for_batch

    # Latest execution is exec2
    exec1 = {"id": "exec1", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:01:00+00:00"}
    exec2 = {"id": "exec2", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:02:00+00:00"}

    # One approved decision
    dec1 = {"id": "dec1", "kind": "saw_batch_decision", "created_utc": "2026-01-01T00:01:30+00:00", "payload": {"state": "APPROVED"}}

    # Metrics for exec2
    mx1 = {"id": "mx1", "kind": "saw_batch_execution_metrics", "created_utc": "2026-01-01T00:03:00+00:00", "parent_id": "exec2", "payload": {"batch_execution_artifact_id": "exec2", "kpis": {"totals": {"job_log_count": 2}}}}

    def _fake_list_runs_filtered(**kwargs):
        # Includes execs + decision + metrics
        return {"items": [exec1, exec2, dec1, mx1]}

    monkeypatch.setattr("app.rmos.runs_v2.store.list_runs_filtered", _fake_list_runs_filtered)

    out = resolve_latest_metrics_for_batch(session_id="s1", batch_label="b1", tool_kind="saw")
    assert out["latest_execution_artifact_id"] == "exec2"
    assert out["latest_metrics_artifact_id"] == "mx1"
    assert out["latest_approved_decision_artifact_id"] == "dec1"
    assert out["kpis"]["totals"]["job_log_count"] == 2
