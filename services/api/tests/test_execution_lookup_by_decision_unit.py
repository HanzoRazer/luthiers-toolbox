from __future__ import annotations

from app.saw_lab.executions_lookup_service import get_latest_execution_for_decision
from app.rmos.runs_v2 import store as runs_store


def test_get_latest_execution_for_decision_picks_latest(monkeypatch):
    decision = {"id": "dec1", "payload": {"session_id": "s1", "batch_label": "b1"}}

    ex_old = {
        "id": "ex_old",
        "kind": "saw_batch_execution",
        "payload": {"created_utc": "2026-01-01T00:05:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"},
    }
    ex_new = {
        "id": "ex_new",
        "kind": "saw_batch_execution",
        "payload": {"created_utc": "2026-01-01T00:06:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1", "metrics": {"duration_s": 12}},
    }

    def _fake_get_run(aid: str):
        return {"dec1": decision}.get(aid)

    def _fake_list_runs_filtered(**kwargs):
        assert kwargs.get("session_id") == "s1"
        assert kwargs.get("batch_label") == "b1"
        return {"items": [ex_old, ex_new]}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    out = get_latest_execution_for_decision(batch_decision_artifact_id="dec1")
    assert out is not None
    assert out["batch_execution_artifact_id"] == "ex_new"
    assert out["statistics"]["duration_s"] == 12
