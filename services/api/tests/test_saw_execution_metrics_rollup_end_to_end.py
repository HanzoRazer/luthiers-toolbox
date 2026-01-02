from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_execution_metrics_rollup_preview_and_persist(client: TestClient, monkeypatch):
    # Ensure learning emission doesn't interfere; metrics are derived from job logs either way.
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-metrics-rollup",
            "session_id": "sess_pytest_metrics_rollup",
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
            "reason": "metrics rollup test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]

    # Post two job logs with metrics
    jl1 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "ok", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 60, "setup_time_s": 10}},
    )
    assert jl1.status_code == 200, jl1.text
    jl2 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "minor issue", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 1, "cut_time_s": 75, "setup_time_s": 5}},
    )
    assert jl2.status_code == 200, jl2.text

    # Preview rollup
    prev = client.get("/api/saw/batch/executions/metrics-rollup/by-execution", params={"batch_execution_artifact_id": exec_id})
    assert prev.status_code == 200, prev.text
    body = prev.json()
    assert body["counts"]["job_log_count"] == 2
    assert body["metrics"]["parts_ok"] == 2
    assert body["metrics"]["parts_scrap"] == 1
    assert body["metrics"]["cut_time_s"] == 135.0
    assert body["metrics"]["setup_time_s"] == 15.0
    assert body["metrics"]["total_time_s"] == 150.0

    # Persist rollup artifact
    persisted = client.post("/api/saw/batch/executions/metrics-rollup/by-execution", params={"batch_execution_artifact_id": exec_id})
    assert persisted.status_code == 200, persisted.text
    art = persisted.json()
    assert (art.get("kind") == "saw_batch_execution_metrics_rollup") or (art.get("payload", {}).get("batch_execution_artifact_id") == exec_id)
