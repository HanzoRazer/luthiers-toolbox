from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_latest_metrics_by_batch_returns_shape(client, monkeypatch):
    """
    Smoke test: GET /api/saw/batch/execution/metrics/latest-by-batch
    returns the expected response shape when service is stubbed.
    """
    fake_result = {
        "session_id": "sess-001",
        "batch_label": "batch-A",
        "tool_kind": "saw",
        "latest_approved_decision_artifact_id": "dec-001",
        "latest_execution_artifact_id": "ex-001",
        "latest_metrics_artifact_id": "met-001",
        "kpis": {"total_cut_time_s": 120.0},
    }
    with patch(
        "app.saw_lab.latest_batch_chain_service.resolve_latest_metrics_for_batch",
        return_value=fake_result,
    ):
        resp = client.get(
            "/api/saw/batch/execution/metrics/latest-by-batch",
            params={"session_id": "sess-001", "batch_label": "batch-A"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == "sess-001"
    assert body["batch_label"] == "batch-A"
    assert body["latest_approved_decision_artifact_id"] == "dec-001"
    assert body["kpis"]["total_cut_time_s"] == 120.0


def test_latest_metrics_by_batch_missing_params(client):
    """400 when required query params are missing."""
    resp = client.get("/api/saw/batch/execution/metrics/latest-by-batch")
    assert resp.status_code in (400, 422)
