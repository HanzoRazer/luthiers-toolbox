from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_decision_metrics_rollup_preview_and_persist(client: TestClient, monkeypatch):
    # Keep learning off; rollup still works (it just counts learning events if they exist)
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "false")

    # Spec -> Plan -> Approve -> Execute twice under same decision
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-decision-rollup",
            "session_id": "sess_pytest_decision_rollup",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 2, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
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
            "reason": "decision rollup test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exe1 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe1.status_code == 200, exe1.text
    ex1 = exe1.json()["batch_execution_artifact_id"]

    exe2 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe2.status_code == 200, exe2.text
    ex2 = exe2.json()["batch_execution_artifact_id"]

    # Add job logs to both executions
    jl1 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": ex1, "operator": "op1", "notes": "ok", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 60, "setup_time_s": 10}},
    )
    assert jl1.status_code == 200, jl1.text
    jl2 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": ex2, "operator": "op2", "notes": "scrap one", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 0, "parts_scrap": 1, "cut_time_s": 50, "setup_time_s": 5}},
    )
    assert jl2.status_code == 200, jl2.text

    # Preview rollup by decision
    prev = client.get(
        "/api/saw/batch/decisions/metrics-rollup/by-decision",
        params={"batch_decision_artifact_id": decision_id},
    )
    assert prev.status_code == 200, prev.text
    body = prev.json()
    assert body["counts"]["execution_count"] >= 2
    assert body["counts"]["job_log_count"] >= 2
    assert body["metrics"]["parts_ok"] == 1
    assert body["metrics"]["parts_scrap"] == 1

    # Persist rollup artifact
    persisted = client.post(
        "/api/saw/batch/decisions/metrics-rollup/by-decision",
        params={"batch_decision_artifact_id": decision_id},
    )
    assert persisted.status_code == 200, persisted.text
    art = persisted.json()
    assert art.get("kind") == "saw_batch_decision_metrics_rollup" or art.get("payload", {}).get("batch_decision_artifact_id") == decision_id
