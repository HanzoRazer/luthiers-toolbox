from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_apply_preview_returns_tuned_context(client: TestClient, monkeypatch):
    """
    The apply preview endpoint should return tuned_context (copy with multipliers applied).
    Even with no accepted learning events, the endpoint should succeed and return default multipliers.
    """
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "true")

    context = {"spindle_rpm": 8000, "feed_rate": 1200, "doc_mm": 3.0}

    res = client.post("/api/saw/batch/learning-overrides/apply", json=context)
    assert res.status_code == 200, res.text
    body = res.json()

    # Verify structure
    assert "apply_enabled" in body
    assert body["apply_enabled"] is True
    assert "resolved" in body
    assert "tuning_stamp" in body
    assert "tuned_context" in body

    # Verify tuning_stamp structure
    stamp = body["tuning_stamp"]
    assert stamp["applied"] is True
    assert "before" in stamp
    assert "after" in stamp
    assert "multipliers" in stamp

    # With no accepted learning events, multipliers default to 1.0
    # so tuned_context should equal original context
    tuned = body["tuned_context"]
    assert tuned["spindle_rpm"] == context["spindle_rpm"]
    assert tuned["feed_rate"] == context["feed_rate"]
    assert tuned["doc_mm"] == context["doc_mm"]


def test_apply_preview_with_accepted_learning_event(client: TestClient, monkeypatch):
    """
    Full integration: create learning event, accept it, then verify apply preview uses the multipliers.
    """
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "true")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-apply-preview",
            "session_id": "sess_pytest_apply_preview",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    spec_id = spec.json()["batch_spec_artifact_id"]

    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_body["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "apply preview test",
            "setup_order": [s["setup_key"] for s in plan_body["setups"]],
            "op_order": [op["op_id"] for s in plan_body["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    exec_id = exec_res.json()["batch_execution_artifact_id"]

    # Post job log that triggers a suggestion (burn => rpm_mult=0.9, feed_mult=1.05)
    jl = client.post(
        "/api/saw/batch/job-log",
        params={
            "batch_execution_artifact_id": exec_id,
            "operator": "pytest",
            "notes": "burn",
            "status": "COMPLETED",
        },
        json={"metrics": {"burn": True}},
    )
    assert jl.status_code == 200, jl.text
    jl_body = jl.json()
    assert jl_body.get("learning_event") is not None

    # Extract the emitted learning event artifact id
    ev = jl_body["learning_event"]
    ev_id = ev.get("artifact_id") or ev.get("id") or ev.get("payload", {}).get("refs", {}).get("job_log_artifact_id")
    assert ev_id, "Expected learning_event artifact id in job-log response"

    # Accept the learning event
    dec = client.post(
        "/api/saw/batch/learning-events/approve",
        params={
            "learning_event_artifact_id": ev_id,
            "policy_decision": "ACCEPT",
            "approved_by": "pytest",
            "reason": "accept for apply preview test",
        },
    )
    assert dec.status_code == 200, dec.text

    # Now call apply preview
    context = {"spindle_rpm": 8000, "feed_rate": 1200, "doc_mm": 3.0}
    res = client.post("/api/saw/batch/learning-overrides/apply", json=context)
    assert res.status_code == 200, res.text
    body = res.json()

    # Verify multipliers were applied
    # burn signal => rpm_mult=0.9, feed_mult=1.05
    tuned = body["tuned_context"]
    assert tuned["spindle_rpm"] < context["spindle_rpm"]  # reduced due to 0.9 mult
    assert tuned["feed_rate"] > context["feed_rate"]  # increased due to 1.05 mult

    # Verify stamp shows the change
    stamp = body["tuning_stamp"]
    assert stamp["before"]["spindle_rpm"] == context["spindle_rpm"]
    assert stamp["after"]["spindle_rpm"] == tuned["spindle_rpm"]
