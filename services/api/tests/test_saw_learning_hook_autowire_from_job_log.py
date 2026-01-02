from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_job_log_autowires_learning_event_when_flag_enabled(client: TestClient, monkeypatch):
    # Enable the hook for this test only
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-learning-hook",
            "session_id": "sess_pytest_learning_hook",
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
            "reason": "learning hook test",
            "setup_order": [s["setup_key"] for s in plan_body["setups"]],
            "op_order": [op["op_id"] for s in plan_body["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    exec_id = exec_res.json()["batch_execution_artifact_id"]

    # Post job log with a burn signal
    jl = client.post(
        "/api/saw/batch/job-log",
        params={
            "batch_execution_artifact_id": exec_id,
            "operator": "pytest",
            "notes": "Slight burn at end.",
            "status": "COMPLETED",
        },
        json={"metrics": {"burn": True, "cut_time_s": 120, "parts_ok": 1, "parts_scrap": 0}},
    )
    assert jl.status_code == 200, jl.text
    jl_body = jl.json()

    # The job-log response should include learning_event when flag enabled (best-effort)
    assert jl_body.get("learning_hook_enabled") is True
    assert "learning_event" in jl_body and jl_body["learning_event"] is not None

    # Alias endpoint should find at least one learning event for this execution
    ev = client.get("/api/saw/batch/learning-events/by-execution", params={"batch_execution_artifact_id": exec_id, "limit": 50})
    assert ev.status_code == 200, ev.text
    items = ev.json()
    assert isinstance(items, list) and len(items) >= 1
    assert any((it.get("kind") == "saw_lab_learning_event") for it in items if isinstance(it, dict))
