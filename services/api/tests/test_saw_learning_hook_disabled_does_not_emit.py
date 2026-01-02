from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_job_log_does_not_emit_learning_event_when_flag_disabled(client: TestClient, monkeypatch):
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-learning-hook-off",
            "session_id": "sess_pytest_learning_hook_off",
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
            "reason": "learning hook off test",
            "setup_order": [s["setup_key"] for s in plan_body["setups"]],
            "op_order": [op["op_id"] for s in plan_body["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    exec_id = exec_res.json()["batch_execution_artifact_id"]

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
    body = jl.json()
    assert body.get("learning_hook_enabled") is False
    assert body.get("learning_event") is None

    # Alias should return empty (or at least not contain a new event for this execution)
    ev = client.get("/api/saw/batch/learning-events/by-execution", params={"batch_execution_artifact_id": exec_id, "limit": 50})
    assert ev.status_code == 200, ev.text
    items = ev.json()
    assert isinstance(items, list)
    assert len(items) == 0
