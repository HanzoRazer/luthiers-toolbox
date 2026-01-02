from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_accept_learning_event_and_resolve_overrides(client: TestClient, monkeypatch):
    # Enable auto-learning emission for this test
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-learning-resolve",
            "session_id": "sess_pytest_learning_resolve",
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
            "reason": "learning resolve test",
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
    # Depending on store shape, learning_event may be dict artifact or include artifact_id.
    ev = jl_body["learning_event"]
    ev_id = ev.get("artifact_id") or ev.get("id") or ev.get("payload", {}).get("refs", {}).get("job_log_artifact_id")
    assert ev_id, "Expected learning_event artifact id in job-log response"

    # Approve it (create decision artifact)
    dec = client.post(
        "/api/saw/batch/learning-events/approve",
        params={
            "learning_event_artifact_id": ev_id,
            "policy_decision": "ACCEPT",
            "approved_by": "pytest",
            "reason": "accept for resolver test",
        },
    )
    assert dec.status_code == 200, dec.text

    # Resolve overrides: should now reflect accepted suggestion
    resolved = client.get("/api/saw/batch/learning-overrides/resolve", params={"limit_events": 200})
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    r = body["resolved"]
    assert r["spindle_rpm_mult"] <= 1.0
    assert r["feed_rate_mult"] >= 1.0
    assert body["source_count"] >= 1
