from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def _make_decision_and_execute(client: TestClient, batch_label: str, session_id: str):
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": batch_label,
            "session_id": session_id,
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
    pb = plan.json()

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": pb["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "lookup test",
            "setup_order": [s["setup_key"] for s in pb["setups"]],
            "op_order": [op["op_id"] for s in pb["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exe = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exe.status_code == 200, exe.text
    exec_id = exe.json()["batch_execution_artifact_id"]
    return decision_id, exec_id


def test_executions_by_decision_alias(client: TestClient):
    decision_id, exec_id = _make_decision_and_execute(client, "pytest-exec-lookup", "sess_pytest_exec_lookup")

    r = client.get("/api/saw/batch/executions/by-decision", params={"batch_decision_artifact_id": decision_id})
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) >= 1
    assert any((it.get("artifact_id") == exec_id or it.get("id") == exec_id) for it in items if isinstance(it, dict))


def test_executions_with_learning_alias(client: TestClient, monkeypatch):
    # apply disabled by default => none should be marked applied
    decision_id, exec_id = _make_decision_and_execute(client, "pytest-exec-learning-lookup", "sess_pytest_exec_learning_lookup")

    r = client.get(
        "/api/saw/batch/executions/with-learning",
        params={"only_applied": "true", "batch_label": "pytest-exec-learning-lookup"},
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list)
    assert len(items) == 0
