from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_latest_rollup_endpoints_return_found_false_when_none(client: TestClient):
    r1 = client.get("/api/saw/batch/executions/metrics-rollup/latest", params={"batch_execution_artifact_id": "does_not_exist"})
    assert r1.status_code == 200
    assert r1.json().get("found") is False

    r2 = client.get("/api/saw/batch/decisions/metrics-rollup/latest", params={"batch_decision_artifact_id": "does_not_exist"})
    assert r2.status_code == 200
    assert r2.json().get("found") is False
