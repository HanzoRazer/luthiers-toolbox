"""Smoke tests for Live Monitor Drilldown endpoint (wired to runs_v2 store)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_live_monitor_drilldown_endpoint_exists(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown endpoint exists."""
    response = client.get("/api/rmos/live-monitor/test-job-123/drilldown")
    assert response.status_code != 404


# =============================================================================
# Response Structure
# =============================================================================

def test_live_monitor_drilldown_returns_200(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown returns 200."""
    response = client.get("/api/rmos/live-monitor/test-job-123/drilldown")
    assert response.status_code == 200


def test_live_monitor_drilldown_returns_job_id(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown returns job_id."""
    response = client.get("/api/rmos/live-monitor/test-job-abc/drilldown")
    data = response.json()
    assert "job_id" in data
    assert data["job_id"] == "test-job-abc"


def test_live_monitor_drilldown_returns_subjobs_array(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown returns subjobs array."""
    response = client.get("/api/rmos/live-monitor/test-job-xyz/drilldown")
    data = response.json()
    assert "subjobs" in data
    assert isinstance(data["subjobs"], list)


def test_live_monitor_drilldown_returns_status(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown returns status."""
    response = client.get("/api/rmos/live-monitor/test-job-123/drilldown")
    data = response.json()
    assert "status" in data


def test_live_monitor_drilldown_returns_message(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown returns message field."""
    response = client.get("/api/rmos/live-monitor/test-job-123/drilldown")
    data = response.json()
    assert "message" in data


# =============================================================================
# Graceful Degradation
# =============================================================================

def test_live_monitor_drilldown_handles_missing_job(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown handles missing job gracefully."""
    response = client.get("/api/rmos/live-monitor/nonexistent-job-12345/drilldown")
    assert response.status_code == 200  # Not 404 - graceful degradation

    data = response.json()
    assert data["job_id"] == "nonexistent-job-12345"
    assert data["subjobs"] == []
    assert data["status"] == "not_found"
    assert "No run found" in data["message"]


def test_live_monitor_drilldown_returns_empty_subjobs_for_missing(client):
    """Missing job returns empty subjobs array, not None."""
    response = client.get("/api/rmos/live-monitor/does-not-exist/drilldown")
    data = response.json()
    assert data["subjobs"] == []
    assert isinstance(data["subjobs"], list)


# =============================================================================
# Subjob Structure (with mocked run)
# =============================================================================

def test_live_monitor_drilldown_with_mock_run(client, monkeypatch):
    """Drilldown with mocked run returns synthesized subjobs."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    # Create a mock run artifact
    mock_run = MagicMock()
    mock_run.run_id = "mock-run-123"
    mock_run.created_at_utc = datetime.now(timezone.utc)
    mock_run.mode = "router"
    mock_run.request_summary = {
        "feed_xy": 1200,
        "spindle_rpm": 20000,
        "stepdown": 2.5,
        "tool_d": 6.0,
    }
    mock_run.decision = MagicMock()
    mock_run.decision.risk_level = "GREEN"
    mock_run.status = MagicMock()
    mock_run.status.value = "OK"

    # Patch the get_run_artifact function
    monkeypatch.setattr(
        "app.rmos.live_monitor_router.get_run_artifact",
        lambda job_id: mock_run if job_id == "mock-run-123" else None
    )

    response = client.get("/api/rmos/live-monitor/mock-run-123/drilldown")
    data = response.json()

    assert response.status_code == 200
    assert data["job_id"] == "mock-run-123"
    assert len(data["subjobs"]) > 0
    assert data["status"] == "ok"


def test_live_monitor_drilldown_subjob_has_required_fields(client, monkeypatch):
    """Synthesized subjobs have all required fields."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    mock_run = MagicMock()
    mock_run.run_id = "test-run"
    mock_run.created_at_utc = datetime.now(timezone.utc)
    mock_run.mode = "router"
    mock_run.request_summary = {"feed_xy": 1000, "stepdown": 3.0}
    mock_run.decision = MagicMock()
    mock_run.decision.risk_level = "YELLOW"
    mock_run.status = MagicMock()
    mock_run.status.value = "OK"

    monkeypatch.setattr(
        "app.rmos.live_monitor_router.get_run_artifact",
        lambda job_id: mock_run if job_id == "test-run" else None
    )

    response = client.get("/api/rmos/live-monitor/test-run/drilldown")
    data = response.json()

    for subjob in data["subjobs"]:
        assert "subjob_type" in subjob
        assert "started_at" in subjob
        assert "ended_at" in subjob
        assert "cam_events" in subjob
        assert isinstance(subjob["cam_events"], list)


def test_live_monitor_drilldown_cam_events_have_required_fields(client, monkeypatch):
    """CAM events in subjobs have all required fields."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    mock_run = MagicMock()
    mock_run.run_id = "event-test"
    mock_run.created_at_utc = datetime.now(timezone.utc)
    mock_run.mode = "saw"
    mock_run.request_summary = {"feed_xy": 800, "spindle_rpm": 15000, "stepdown": 4.0}
    mock_run.decision = MagicMock()
    mock_run.decision.risk_level = "GREEN"
    mock_run.status = MagicMock()
    mock_run.status.value = "OK"

    monkeypatch.setattr(
        "app.rmos.live_monitor_router.get_run_artifact",
        lambda job_id: mock_run if job_id == "event-test" else None
    )

    response = client.get("/api/rmos/live-monitor/event-test/drilldown")
    data = response.json()

    # Get first subjob with events
    subjobs_with_events = [s for s in data["subjobs"] if len(s["cam_events"]) > 0]
    assert len(subjobs_with_events) > 0

    event = subjobs_with_events[0]["cam_events"][0]
    assert "timestamp" in event
    assert "feedrate" in event
    assert "spindle_speed" in event
    assert "doc" in event
    assert "feed_state" in event
    assert "heuristic" in event


def test_live_monitor_drilldown_heuristic_reflects_risk_level(client, monkeypatch):
    """CAM event heuristic reflects run risk level."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    mock_run = MagicMock()
    mock_run.run_id = "red-risk-run"
    mock_run.created_at_utc = datetime.now(timezone.utc)
    mock_run.mode = "router"
    mock_run.request_summary = {}
    mock_run.decision = MagicMock()
    mock_run.decision.risk_level = "RED"
    mock_run.status = MagicMock()
    mock_run.status.value = "BLOCKED"

    monkeypatch.setattr(
        "app.rmos.live_monitor_router.get_run_artifact",
        lambda job_id: mock_run if job_id == "red-risk-run" else None
    )

    response = client.get("/api/rmos/live-monitor/red-risk-run/drilldown")
    data = response.json()

    # All events should have danger heuristic for RED risk
    for subjob in data["subjobs"]:
        for event in subjob["cam_events"]:
            assert event["heuristic"] == "danger"
