from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_execution_metrics_rollup_computes_and_persists(client: TestClient):
    # Spec -> Plan -> Approve -> Execute
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-rollup",
            "session_id": "sess_pytest_rollup",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 2, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    spec_id = spec.json()["batch_spec_artifact_id"]

    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    plan_id = plan_body["batch_plan_artifact_id"]

    setup_order = [s["setup_key"] for s in plan_body["setups"]]
    op_order = [op["op_id"] for s in plan_body["setups"] for op in s["ops"]]

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "rollup test",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    exec_id = exec_res.json()["batch_execution_artifact_id"]

    # Write a couple job logs with metrics
    jl1 = client.post(
        "/api/saw/batch/job-log",
        params={
            "batch_execution_artifact_id": exec_id,
            "operator": "pytest",
            "notes": "Ran clean.",
            "status": "COMPLETED",
        },
        json={"metrics": {"cut_time_s": 120, "setup_time_s": 60, "parts_ok": 2, "parts_scrap": 0}},
    )
    assert jl1.status_code == 200, jl1.text

    jl2 = client.post(
        "/api/saw/batch/job-log",
        params={
            "batch_execution_artifact_id": exec_id,
            "operator": "pytest2",
            "notes": "Slight burn at end.",
            "status": "COMPLETED",
        },
        json={"metrics": {"cut_time_s": 140, "setup_time_s": 40, "parts_ok": 1, "parts_scrap": 1, "burn": True}},
    )
    assert jl2.status_code == 200, jl2.text

    # Compute-only rollup
    r = client.get("/api/saw/batch/metrics/rollup/by-execution", params={"batch_execution_artifact_id": exec_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["batch_execution_artifact_id"] == exec_id
    assert body["log_count"] >= 2
    assert body["events"]["burn_events"] >= 1
    assert body["yield"]["parts_total"] is not None

    # Persist rollup artifact
    p = client.post("/api/saw/batch/metrics/rollup/by-execution", params={"batch_execution_artifact_id": exec_id})
    assert p.status_code == 200, p.text
    persisted = p.json()
    assert (persisted.get("kind") == "saw_batch_execution_rollup") or (persisted.get("payload", {}).get("batch_execution_artifact_id") == exec_id)

    # Alias lookup returns the rollup
    alias = client.get("/api/saw/batch/metrics/rollup/alias", params={"batch_execution_artifact_id": exec_id})
    assert alias.status_code == 200, alias.text
    items = alias.json()
    assert isinstance(items, list) and len(items) >= 1
    assert any((it.get("kind") == "saw_batch_execution_rollup") for it in items if isinstance(it, dict))
