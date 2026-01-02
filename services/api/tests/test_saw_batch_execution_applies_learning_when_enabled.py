from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_batch_execution_stamps_learning_applied_when_enabled(client: TestClient, monkeypatch):
    # Enable learning event emission + apply stage
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "true")

    # Spec -> Plan -> Approve
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-learn-apply",
            "session_id": "sess_pytest_exec_learn_apply",
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
            "reason": "exec learning apply test",
            "setup_order": [s["setup_key"] for s in plan_body["setups"]],
            "op_order": [op["op_id"] for s in plan_body["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    # First execution to create a job-log + learning event path requires an execution id
    exec1 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec1.status_code == 200, exec1.text
    exec1_id = exec1.json()["batch_execution_artifact_id"]

    # Post job log that triggers burn suggestion => learning event emitted
    jl = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec1_id, "operator": "pytest", "notes": "burn", "status": "COMPLETED"},
        json={"metrics": {"burn": True}},
    )
    assert jl.status_code == 200, jl.text
    ev = jl.json().get("learning_event")
    assert ev is not None
    ev_id = ev.get("artifact_id") or ev.get("id")
    assert ev_id

    # ACCEPT the learning event
    dec = client.post(
        "/api/saw/batch/learning-events/approve",
        params={"learning_event_artifact_id": ev_id, "policy_decision": "ACCEPT", "approved_by": "pytest", "reason": "enable apply"},
    )
    assert dec.status_code == 200, dec.text

    # Second execution should apply accepted learning and stamp it
    exec2 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec2.status_code == 200, exec2.text
    body = exec2.json()
    assert body["learning"]["apply_enabled"] is True
    assert body["learning"]["resolved"]["source_count"] >= 1
    stamp = body["learning"]["tuning_stamp"]
    assert stamp and stamp.get("applied") is True
