from __future__ import annotations

from app.rmos.runs_v2 import store as runs_store
from app.saw_lab.saw_lab_toolpaths_from_decision_service import generate_toolpaths_from_decision


def test_generate_toolpaths_from_decision_applies_patch_and_persists(monkeypatch):
    # Arrange: decision -> plan+spec
    decision = {
        "id": "dec1",
        "payload": {
            "session_id": "s1",
            "batch_label": "b1",
            "batch_plan_artifact_id": "plan1",
            "batch_spec_artifact_id": "spec1",
            "selected_setup_key": "setup_1",
            "selected_op_ids": ["op_1"],
            "applied_context_patch": {"feed_rate": 400.0},
            "applied_multipliers": {"feed": 0.5},
        },
    }
    plan = {"id": "plan1", "payload": {"batch_label": "b1", "session_id": "s1", "setups": [{"setup_key": "setup_1", "ops": [{"op_id": "op_1"}]}]}}
    spec = {"id": "spec1", "payload": {"batch_label": "b1", "session_id": "s1", "tool_id": "saw:thin_140", "feed_rate": 600.0}}

    def _fake_get_run(aid: str):
        return {"dec1": decision, "plan1": plan, "spec1": spec}.get(aid)

    stored = {}

    def _fake_store_artifact(*, kind: str, payload: dict, parent_id: str, session_id: str):
        stored["kind"] = kind
        stored["payload"] = payload
        stored["parent_id"] = parent_id
        stored["session_id"] = session_id
        return "tp1"

    # Fake toolpath generator; we assert context is tuned deterministically.
    def _fake_plan_saw_toolpaths_for_design(*, context, **kwargs):
        # base feed_rate 600 patched -> 400 then multiplied by 0.5 => 200
        assert abs(float(context["feed_rate"]) - 200.0) < 1e-6
        return {"gcode_text": "G1 X0 Y0", "statistics": {"move_count": 1}}

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)
    monkeypatch.setattr(runs_store, "store_artifact", _fake_store_artifact)
    monkeypatch.setattr("app.saw_lab_run_service.plan_saw_toolpaths_for_design", _fake_plan_saw_toolpaths_for_design)

    out = generate_toolpaths_from_decision(batch_decision_artifact_id="dec1", include_gcode=True)
    assert out["status"] == "OK"
    assert out["batch_toolpaths_artifact_id"] == "tp1"
    assert stored["kind"] == "saw_batch_toolpaths"
    assert stored["parent_id"] == "dec1"
    assert stored["payload"]["parent_batch_decision_artifact_id"] == "dec1"
    assert stored["payload"]["parent_batch_plan_artifact_id"] == "plan1"
    assert stored["payload"]["parent_batch_spec_artifact_id"] == "spec1"
    assert stored["payload"]["decision_apply_stamp"]["patch_applied"] is True
