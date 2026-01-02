from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_rollup_history_and_diff(client: TestClient, monkeypatch):
    monkeypatch.setenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false")

    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-rollup-history-diff",
            "session_id": "sess_pytest_rollup_history_diff",
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
            "reason": "rollup history/diff test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]
    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]

    # Two job logs => two persisted execution rollups (hook runs on each write_job_log)
    jl1 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "ok", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 1, "parts_scrap": 0, "cut_time_s": 10, "setup_time_s": 2}},
    )
    assert jl1.status_code == 200, jl1.text
    jl2 = client.post(
        "/api/saw/batch/job-log",
        params={"batch_execution_artifact_id": exec_id, "operator": "op1", "notes": "scrap one", "status": "COMPLETED"},
        json={"metrics": {"parts_ok": 0, "parts_scrap": 1, "cut_time_s": 8, "setup_time_s": 1}},
    )
    assert jl2.status_code == 200, jl2.text

    hist = client.get("/api/saw/batch/executions/metrics-rollup/history", params={"batch_execution_artifact_id": exec_id, "limit": 10})
    assert hist.status_code == 200, hist.text
    items = hist.json()
    assert isinstance(items, list) and len(items) >= 2

    left_id = items[1].get("artifact_id") or items[1].get("id")
    right_id = items[0].get("artifact_id") or items[0].get("id")
    assert left_id and right_id

    d = client.get("/api/saw/batch/rollups/diff", params={"left_rollup_artifact_id": left_id, "right_rollup_artifact_id": right_id})
    assert d.status_code == 200, d.text
    body = d.json()
    assert body["left_artifact_id"] == left_id
    assert body["right_artifact_id"] == right_id
    assert "metrics" in body and isinstance(body["metrics"], dict)
