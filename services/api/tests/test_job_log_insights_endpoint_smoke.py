"""Smoke tests for Job Log Insights endpoint (wired to real job_int_log analysis)."""

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

def test_job_log_insights_list_endpoint_exists(client):
    """GET /api/cam/job_log/insights endpoint exists."""
    response = client.get("/api/cam/job_log/insights")
    assert response.status_code != 404


def test_job_log_insights_detail_endpoint_exists(client):
    """GET /api/cam/job_log/insights/{insight_id} endpoint exists."""
    response = client.get("/api/cam/job_log/insights/test-run-123")
    assert response.status_code != 404


# =============================================================================
# List Endpoint Response Structure
# =============================================================================

def test_job_log_insights_list_returns_200(client):
    """GET /api/cam/job_log/insights returns 200."""
    response = client.get("/api/cam/job_log/insights")
    assert response.status_code == 200


def test_job_log_insights_list_returns_insights_array(client):
    """GET /api/cam/job_log/insights returns insights array."""
    response = client.get("/api/cam/job_log/insights")
    data = response.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)


def test_job_log_insights_list_returns_total_jobs(client):
    """GET /api/cam/job_log/insights returns total_jobs count."""
    response = client.get("/api/cam/job_log/insights")
    data = response.json()
    assert "total_jobs" in data
    assert isinstance(data["total_jobs"], int)


def test_job_log_insights_list_accepts_limit_param(client):
    """GET /api/cam/job_log/insights accepts limit parameter."""
    response = client.get("/api/cam/job_log/insights?limit=10")
    assert response.status_code == 200


def test_job_log_insights_list_accepts_severity_filter(client):
    """GET /api/cam/job_log/insights accepts severity filter."""
    response = client.get("/api/cam/job_log/insights?severity=ok")
    assert response.status_code == 200


def test_job_log_insights_list_accepts_wood_filter(client):
    """GET /api/cam/job_log/insights accepts wood filter."""
    response = client.get("/api/cam/job_log/insights?wood=maple")
    assert response.status_code == 200


# =============================================================================
# Detail Endpoint Response Structure
# =============================================================================

def test_job_log_insights_detail_returns_200(client):
    """GET /api/cam/job_log/insights/{id} returns 200."""
    response = client.get("/api/cam/job_log/insights/test-run-123")
    assert response.status_code == 200


def test_job_log_insights_detail_returns_insight_structure(client):
    """GET /api/cam/job_log/insights/{id} returns expected structure."""
    response = client.get("/api/cam/job_log/insights/nonexistent-run")
    data = response.json()

    # Should return graceful fallback structure even for non-existent job
    assert "job_id" in data
    assert "job_name" in data
    assert "wood_type" in data
    assert "actual_time_s" in data
    assert "estimated_time_s" in data
    assert "time_diff_pct" in data
    assert "classification" in data
    assert "severity" in data
    assert "review_pct" in data
    assert "gate_pct" in data
    assert "recommendation" in data


def test_job_log_insights_detail_returns_valid_severity(client):
    """GET /api/cam/job_log/insights/{id} returns valid severity value."""
    response = client.get("/api/cam/job_log/insights/some-job-id")
    data = response.json()

    assert data["severity"] in ["ok", "warn", "error"]


def test_job_log_insights_detail_returns_valid_percentages(client):
    """GET /api/cam/job_log/insights/{id} returns valid percentage values."""
    response = client.get("/api/cam/job_log/insights/any-job")
    data = response.json()

    assert 0 <= data["review_pct"] <= 100
    assert 0 <= data["gate_pct"] <= 100


def test_job_log_insights_detail_returns_numeric_times(client):
    """GET /api/cam/job_log/insights/{id} returns numeric time values."""
    response = client.get("/api/cam/job_log/insights/test")
    data = response.json()

    assert isinstance(data["actual_time_s"], (int, float))
    assert isinstance(data["estimated_time_s"], (int, float))
    assert isinstance(data["time_diff_pct"], (int, float))


# =============================================================================
# Graceful Degradation
# =============================================================================

def test_job_log_insights_detail_handles_missing_job(client):
    """GET /api/cam/job_log/insights/{id} handles missing job gracefully."""
    response = client.get("/api/cam/job_log/insights/does-not-exist-12345")
    assert response.status_code == 200  # Not 404 - graceful degradation

    data = response.json()
    assert "recommendation" in data
    assert "No job log found" in data["recommendation"]
