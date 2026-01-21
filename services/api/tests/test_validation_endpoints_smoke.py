"""
Smoke tests for RMOS v1 Validation endpoints.

Tests:
- GET /api/rmos/validation/scenarios - list available scenarios
- POST /api/rmos/validation/run - run single scenario
- POST /api/rmos/validation/run-batch - run batch (tier filter)
- GET /api/rmos/validation/summary - get latest summary
- GET /api/rmos/validation/sessions - list sessions
- GET /api/rmos/validation/runs - list runs
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_get_scenarios_returns_30(client: TestClient):
    """GET /api/rmos/validation/scenarios returns all 30 scenarios."""
    resp = client.get("/api/rmos/validation/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert "scenarios" in data
    assert data["total"] == 30

    # Verify tier distribution
    tiers = [s["tier"] for s in data["scenarios"]]
    assert tiers.count("baseline") == 10
    assert tiers.count("edge_pressure") == 10
    assert tiers.count("adversarial") == 10


def test_get_scenarios_with_tier_filter(client: TestClient):
    """GET /api/rmos/validation/scenarios?tier=baseline returns only baseline."""
    resp = client.get("/api/rmos/validation/scenarios?tier=baseline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert all(s["tier"] == "baseline" for s in data["scenarios"])


def test_run_single_scenario(client: TestClient):
    """POST /api/rmos/validation/run executes single scenario."""
    resp = client.post(
        "/api/rmos/validation/run",
        json={"scenario_id": "baseline-01"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["scenario_id"] == "baseline-01"
    assert "passed" in data
    assert "actual_decision" in data


def test_run_nonexistent_scenario_404(client: TestClient):
    """POST /api/rmos/validation/run with bad ID returns 404."""
    resp = client.post(
        "/api/rmos/validation/run",
        json={"scenario_id": "nonexistent-99"}
    )
    assert resp.status_code == 404


def test_run_batch_baseline_tier(client: TestClient):
    """POST /api/rmos/validation/run-batch runs tier scenarios."""
    resp = client.post(
        "/api/rmos/validation/run-batch",
        json={"tier": "baseline"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["total"] == 10
    assert "passed" in data
    assert "failed" in data
    assert "run_ids" in data
    assert len(data["run_ids"]) == 10


def test_get_summary(client: TestClient):
    """GET /api/rmos/validation/summary returns summary structure."""
    resp = client.get("/api/rmos/validation/summary")
    assert resp.status_code == 200
    data = resp.json()
    # Summary may be empty if no sessions run yet
    assert "total" in data
    assert "passed" in data
    assert "release_authorized" in data


def test_list_sessions(client: TestClient):
    """GET /api/rmos/validation/sessions returns list."""
    resp = client.get("/api/rmos/validation/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_list_runs(client: TestClient):
    """GET /api/rmos/validation/runs returns list."""
    resp = client.get("/api/rmos/validation/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert isinstance(data["runs"], list)


def test_log_manual_result(client: TestClient):
    """POST /api/rmos/validation/log persists manual result."""
    resp = client.post(
        "/api/rmos/validation/log",
        json={
            "scenario_id": "manual-test-01",
            "scenario_name": "Manual Test",
            "tier": "baseline",
            "expected_decision": ["GREEN"],
            "actual_decision": "GREEN",
            "expected_export_allowed": True,
            "actual_export_allowed": True,
            "decision_match": True,
            "rules_match": True,
            "export_match": True,
            "passed": True,
            "notes": "Manual UI test"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["logged"] is True
