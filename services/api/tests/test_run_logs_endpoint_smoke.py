"""
Smoke tests for RMOS Run Log endpoints.

Tests:
- GET /api/rmos/run-logs/latest
- GET /api/rmos/run-logs/export.csv
- GET /api/rmos/run-logs/export.json
- GET /api/rmos/run-logs/summary
- GET /api/rmos/run-logs/overrides
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_get_latest_returns_list(client: TestClient):
    """GET /api/rmos/run-logs/latest returns entries list."""
    resp = client.get("/api/rmos/run-logs/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "count" in data
    assert "limit" in data
    assert isinstance(data["entries"], list)


def test_get_latest_with_limit(client: TestClient):
    """GET /api/rmos/run-logs/latest?limit=5 respects limit."""
    resp = client.get("/api/rmos/run-logs/latest?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 5


def test_get_latest_with_risk_filter(client: TestClient):
    """GET /api/rmos/run-logs/latest?risk_level=GREEN filters by risk."""
    resp = client.get("/api/rmos/run-logs/latest?risk_level=GREEN")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["entries"], list)


def test_export_csv_returns_csv(client: TestClient):
    """GET /api/rmos/run-logs/export.csv returns CSV content."""
    resp = client.get("/api/rmos/run-logs/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in resp.headers
    # CSV should have header row at minimum
    assert "run_id" in resp.text


def test_export_json_returns_jsonl(client: TestClient):
    """GET /api/rmos/run-logs/export.json returns JSONL content."""
    resp = client.get("/api/rmos/run-logs/export.json")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers["content-type"] or "json" in resp.headers["content-type"]


def test_get_summary_returns_stats(client: TestClient):
    """GET /api/rmos/run-logs/summary returns aggregate stats."""
    resp = client.get("/api/rmos/run-logs/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "by_risk_level" in data
    assert "override_count" in data


def test_get_overrides_returns_list(client: TestClient):
    """GET /api/rmos/run-logs/overrides returns override entries."""
    resp = client.get("/api/rmos/run-logs/overrides")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)
