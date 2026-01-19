from __future__ import annotations


def test_latest_toolpaths_for_execution(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.saw_lab.toolpaths_lookup_service import resolve_latest_toolpaths_for_execution

    tp1 = {
        "id": "tp1",
        "kind": "saw_batch_toolpaths",
        "created_utc": "2026-01-01T00:03:00+00:00",
        "parent_id": "exec1",
        "payload": {"batch_execution_artifact_id": "exec1", "attachments": {"gcode_sha256": "aaa"}},
    }
    tp2 = {
        "id": "tp2",
        "kind": "saw_batch_toolpaths",
        "created_utc": "2026-01-01T00:04:00+00:00",
        "parent_id": "exec1",
        "payload": {"batch_execution_artifact_id": "exec1", "attachments": {"gcode_sha256": "bbb"}},
    }

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [tp1, tp2]}

    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)
    out = resolve_latest_toolpaths_for_execution(batch_execution_artifact_id="exec1", session_id="s1", batch_label="b1", tool_kind="saw")
    assert out["id"] == "tp2"


def test_latest_toolpaths_for_batch_uses_latest_execution(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.saw_lab.toolpaths_lookup_service import resolve_latest_toolpaths_for_batch

    exec1 = {"id": "exec1", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:01:00+00:00"}
    exec2 = {"id": "exec2", "kind": "saw_batch_execution", "created_utc": "2026-01-01T00:02:00+00:00"}
    tp = {"id": "tp2", "kind": "saw_batch_toolpaths", "created_utc": "2026-01-01T00:03:00+00:00", "parent_id": "exec2", "payload": {"batch_execution_artifact_id": "exec2"}}

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [exec1, exec2, tp]}

    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)
    out = resolve_latest_toolpaths_for_batch(session_id="s1", batch_label="b1", tool_kind="saw")
    assert out["latest_execution_artifact_id"] == "exec2"
    assert out["latest_toolpaths_artifact_id"] == "tp2"
