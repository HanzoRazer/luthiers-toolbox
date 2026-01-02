from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_job_logs_csv_export(client: TestClient, monkeypatch):
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "false")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-csv-joblogs",
            "session_id": "sess_pytest_csv_joblogs",
            "tool_id": "saw:thin_140",
            "items": [{"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0}],
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
            "reason": "csv job logs",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]
    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]

    jl = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "ok", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 10, "setup_time_s": 2}},
    )
    assert jl.status_code == 200, jl.text

    r = client.get("/api/saw/batch/executions/job-logs.csv", params={"batch_execution_artifact_id": exec_id})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text
    assert "job_log_artifact_id" in text
    assert "parts_ok" in text


def test_execution_rollups_csv_export(client: TestClient, monkeypatch):
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute -> Job log (persist rollup)
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-csv-rollups",
            "session_id": "sess_pytest_csv_rollups",
            "tool_id": "saw:thin_140",
            "items": [{"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0}],
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
            "reason": "csv rollups",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]
    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]

    jl = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "ok", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 10, "setup_time_s": 2}},
    )
    assert jl.status_code == 200, jl.text

    r = client.get("/api/saw/batch/decisions/execution-rollups.csv", params={"batch_decision_artifact_id": decision_id})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text
    assert "rollup_artifact_id" in text
    assert "scrap_rate" in text
