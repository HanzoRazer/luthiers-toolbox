from __future__ import annotations

from app.rmos.runs_v2.batch_dashboard import build_batch_summary_dashboard_card


def test_build_batch_summary_dashboard_card_counts_latest_and_links(monkeypatch):
    # Stub list_batch_tree to avoid DB/store dependency
    def _fake_list_batch_tree(**kwargs):
        return {
            "root_artifact_id": "spec1",
            "node_count": 5,
            "nodes": [
                {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2026-01-01T00:00:00+00:00"},
                {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2026-01-01T00:01:00+00:00"},
                {"id": "dec1", "kind": "saw_batch_decision", "created_utc": "2026-01-01T00:02:00+00:00"},
                {"id": "jl1", "kind": "saw_batch_job_log", "created_utc": "2026-01-01T00:03:00+00:00", "payload": {"statistics": {"total_length_mm": 10.0, "cut_count": 1, "move_count": 4}, "notes": "burn"}},
                {"id": "le1", "kind": "saw_lab_learning_event", "created_utc": "2026-01-01T00:04:00+00:00"},
            ],
        }

    monkeypatch.setattr("app.rmos.runs_v2.batch_tree.list_batch_tree", _fake_list_batch_tree)

    out = build_batch_summary_dashboard_card(session_id="s1", batch_label="b1", tool_kind="saw", include_links=True, include_kpis=True)
    assert out["root_artifact_id"] == "spec1"
    assert out["counts"]["spec"] == 1
    assert out["counts"]["plan"] == 1
    assert out["counts"]["decision"] == 1
    assert out["counts"]["job_logs"] == 1
    assert out["counts"]["learning"] == 1
    assert out["latest_ids"]["job_log"] == "jl1"
    assert out["kpi_rollup"]["source"] in {"execution_metrics_artifact", "job_log_heuristic"}
    assert "batch_audit_export_zip" in (out["links"] or {})
