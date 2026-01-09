from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Uses your real app factory; assumes existing conftest isolates env roots.
    from app.main import app

    return TestClient(app)


def test_decision_intel_endpoints_exist(client: TestClient):
    # Just confirm routes are mounted (won't assume data exists).
    r = client.get("/api/_meta/routing-truth")
    assert r.status_code == 200
    paths = {x["path"] for x in r.json().get("routes", []) if isinstance(x, dict) and "path" in x}
    assert "/api/saw/batch/decision-intel/suggestions" in paths
    assert "/api/saw/batch/decision-intel/approve" in paths
