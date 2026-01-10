from __future__ import annotations

from app.saw_lab.executions_list_service import list_executions_for_decision


def test_list_executions_for_decision_filters_and_paginates(monkeypatch):
    decision = {"id": "dec1", "payload": {"session_id": "s1", "batch_label": "b1"}}

    # 3 executions, 1 unrelated execution, 1 non-execution
    arts = [
        {"id": "ex1", "kind": "saw_batch_execution", "payload": {"created_utc": "2026-01-01T00:01:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"}},
        {"id": "ex2", "kind": "saw_batch_execution", "payload": {"created_utc": "2026-01-01T00:02:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"}},
        {"id": "ex3", "kind": "saw_batch_execution", "payload": {"created_utc": "2026-01-01T00:03:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"}},
        {"id": "exX", "kind": "saw_batch_execution", "payload": {"created_utc": "2026-01-01T00:04:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "other"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "payload": {"created_utc": "2026-01-01T00:05:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"}},
    ]

    def _fake_get_run(aid: str):
        return {"dec1": decision}.get(aid)

    def _fake_list_runs_filtered(**kwargs):
        assert kwargs.get("session_id") == "s1"
        assert kwargs.get("batch_label") == "b1"
        return {"items": arts}

    # Patch the module imports inside executions_list_service
    import app.rmos.runs_v2.store as store_mod
    monkeypatch.setattr(store_mod, "get_run", _fake_get_run)
    monkeypatch.setattr(store_mod, "list_runs_filtered", _fake_list_runs_filtered)

    out = list_executions_for_decision(batch_decision_artifact_id="dec1", limit=2, offset=0, newest_first=True)
    assert out is not None
    assert out["total"] == 3
    assert len(out["items"]) == 2
    # newest first => ex3, ex2
    assert out["items"][0]["artifact_id"] == "ex3"
    assert out["items"][1]["artifact_id"] == "ex2"

    out2 = list_executions_for_decision(batch_decision_artifact_id="dec1", limit=2, offset=2, newest_first=True)
    assert len(out2["items"]) == 1
    assert out2["items"][0]["artifact_id"] == "ex1"
