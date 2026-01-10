from __future__ import annotations

from app.rmos.runs_v2 import store as runs_store
from app.saw_lab.toolpaths_lookup_service import get_latest_toolpaths_for_decision


def test_get_latest_toolpaths_for_decision_picks_latest(monkeypatch):
    decision = {"id": "dec1", "payload": {"session_id": "s1", "batch_label": "b1"}}

    tp_old = {
        "id": "tp_old",
        "kind": "saw_batch_toolpaths",
        "payload": {"created_utc": "2026-01-01T00:01:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1"},
    }
    tp_new = {
        "id": "tp_new",
        "kind": "saw_batch_toolpaths",
        "payload": {"created_utc": "2026-01-01T00:02:00+00:00", "status": "OK", "parent_batch_decision_artifact_id": "dec1", "statistics": {"move_count": 7}},
    }

    def _fake_get_run(aid: str):
        return {"dec1": decision}.get(aid)

    def _fake_list_runs_filtered(**kwargs):
        assert kwargs.get("session_id") == "s1"
        assert kwargs.get("batch_label") == "b1"
        return {"items": [tp_old, tp_new]}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "list_runs_filtered", _fake_list_runs_filtered)

    out = get_latest_toolpaths_for_decision(batch_decision_artifact_id="dec1")
    assert out is not None
    assert out["batch_toolpaths_artifact_id"] == "tp_new"
    assert out["statistics"]["move_count"] == 7
