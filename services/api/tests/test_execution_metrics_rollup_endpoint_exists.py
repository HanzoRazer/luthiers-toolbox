from __future__ import annotations

from fastapi.testclient import TestClient


def test_execution_metrics_rollup_endpoint_is_mounted():
    from app.main import app

    c = TestClient(app)
    r = c.get("/api/_meta/routing-truth")
    assert r.status_code == 200
    paths = {
        x["path"]
        for x in r.json().get("routes", [])
        if isinstance(x, dict) and "path" in x
    }
    assert "/api/saw/batch/execution/metrics/rollup" in paths
