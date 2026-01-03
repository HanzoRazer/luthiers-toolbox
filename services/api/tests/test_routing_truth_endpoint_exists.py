from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_meta_routing_truth_endpoint(client: TestClient):
    """Verify the routing truth endpoint exists and returns expected structure."""
    r = client.get("/api/_meta/routing-truth")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "count" in body and "routes" in body
    assert isinstance(body["routes"], list)
    # Must contain itself
    paths = {it.get("path") for it in body["routes"] if isinstance(it, dict)}
    assert "/api/_meta/routing-truth" in paths
