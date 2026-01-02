from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_retry_endpoint_creates_new_execution_and_retry_artifact(client: TestClient):
    # Create initial chain
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-retry",
            "session_id": "sess_pytest_exec_retry",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
                {"part_id": "p2", "qty": 1, "material_id": "ebony", "thickness_mm": 6.0, "length_mm": 200.0, "width_mm": 20.0},
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
            "reason": "retry test",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    source_execution_id = exec_res.json()["batch_execution_artifact_id"]

    # Retry (will retry BLOCKED/ERROR only; if none, creates an empty retry execution)
    retry = client.post(
        "/api/saw/batch/executions/retry",
        params={"batch_execution_artifact_id": source_execution_id, "reason": "pytest-retry"},
    )
    assert retry.status_code == 200, retry.text
    body = retry.json()

    assert body["source_execution_artifact_id"] == source_execution_id
    assert body["new_execution_artifact_id"]
    assert body["retry_artifact_id"]

    # New execution should be discoverable
    new_exec_id = body["new_execution_artifact_id"]
    lookup = client.get("/api/saw/batch/op-toolpaths/by-execution", params={"batch_execution_artifact_id": new_exec_id})
    assert lookup.status_code == 200, lookup.text
