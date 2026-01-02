from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_executions_with_learning_finds_applied_runs(client: TestClient, monkeypatch):
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "true")

    # Spec -> Plan -> Approve -> Execute #1 (to create learning event via job log)
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-learning-applied",
            "session_id": "sess_pytest_exec_learning_applied",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec.json()["batch_spec_artifact_id"]})
    assert plan.status_code == 200, plan.text
    pb = plan.json()
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": pb["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "applied lookup test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec1 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec1.status_code == 200, exec1.text
    exec1_id = exec1.json()["batch_execution_artifact_id"]

    # Job log => learning event emitted (burn)
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

    # ACCEPT the event
    dec = client.post(
        "/api/saw/batch/learning-events/approve",
        params={"learning_event_artifact_id": ev_id, "policy_decision": "ACCEPT", "approved_by": "pytest", "reason": "apply"},
    )
    assert dec.status_code == 200, dec.text

    # Execute #2 => should apply
    exec2 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec2.status_code == 200, exec2.text
    exec2_id = exec2.json()["batch_execution_artifact_id"]
    assert exec2.json()["learning"]["tuning_stamp"]["applied"] is True

    # Alias should find at least one applied execution
    r = client.get(
        "/api/saw/batch/executions/with-learning",
        params={"only_applied": "true", "batch_label": "pytest-exec-learning-applied"},
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) >= 1
    assert any((it.get("artifact_id") == exec2_id or it.get("id") == exec2_id) for it in items if isinstance(it, dict))
