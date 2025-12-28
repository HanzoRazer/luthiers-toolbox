from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_job_log_round_trip(client: TestClient):
    # Full chain
    spec = client.post("/api/saw/batch/spec", json={
        "batch_label": "pytest-job-log",
        "session_id": "sess_job_log",
        "tool_id": "saw:thin_140",
        "items": [{"part_id": "p1", "qty": 1, "material_id": "maple",
                   "thickness_mm": 6, "length_mm": 300, "width_mm": 30}]
    })
    plan = client.post("/api/saw/batch/plan",
                       json={"batch_spec_artifact_id": spec.json()["batch_spec_artifact_id"]})
    approve = client.post("/api/saw/batch/approve", json={
        "batch_plan_artifact_id": plan.json()["batch_plan_artifact_id"],
        "approved_by": "pytest",
        "reason": "job log test",
        "setup_order": [s["setup_key"] for s in plan.json()["setups"]],
        "op_order": [op["op_id"] for s in plan.json()["setups"] for op in s["ops"]],
    })
    exec_res = client.post("/api/saw/batch/toolpaths",
                           json={"batch_decision_artifact_id": approve.json()["batch_decision_artifact_id"]})
    exec_id = exec_res.json()["batch_execution_artifact_id"]

    # Write job log
    log = client.post("/api/saw/batch/job-log", params={
        "batch_execution_artifact_id": exec_id,
        "operator": "pytest",
        "notes": "Cut ran clean. No burn.",
        "status": "COMPLETED",
    })
    assert log.status_code == 200

    # Retrieve
    logs = client.get("/api/saw/batch/job-log/by-execution",
                      params={"batch_execution_artifact_id": exec_id})
    assert len(logs.json()) >= 1
