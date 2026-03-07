"""Smoke tests for CAM Risk Reports endpoints (wired to persistent JSONL storage)."""

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

def test_risk_report_submit_endpoint_exists(client):
    """POST /api/cam/jobs/risk_report endpoint exists."""
    payload = {
        "job_id": "test-job-123",
        "issues": [],
        "analytics": {
            "total_issues": 0,
            "severity_counts": {},
            "risk_score": 0.0,
            "total_extra_time_s": 0.0,
            "total_extra_time_human": "0s",
        },
    }
    response = client.post("/api/cam/jobs/risk_report", json=payload)
    assert response.status_code != 404


def test_recent_reports_endpoint_exists(client):
    """GET /api/cam/jobs/recent endpoint exists."""
    response = client.get("/api/cam/jobs/recent")
    assert response.status_code != 404


def test_job_risk_timeline_endpoint_exists(client):
    """GET /api/cam/jobs/{job_id}/risk_timeline endpoint exists."""
    response = client.get("/api/cam/jobs/test-job/risk_timeline")
    assert response.status_code != 404


def test_risk_reports_browse_endpoint_exists(client):
    """GET /api/cam/risk/reports endpoint exists."""
    response = client.get("/api/cam/risk/reports")
    assert response.status_code != 404


# =============================================================================
# Response Structure
# =============================================================================

def test_risk_report_submit_returns_200(client):
    """POST /api/cam/jobs/risk_report returns 200."""
    payload = {
        "job_id": "test-submit-200",
        "issues": [],
        "analytics": {
            "total_issues": 0,
            "severity_counts": {},
            "risk_score": 0.0,
            "total_extra_time_s": 0.0,
            "total_extra_time_human": "0s",
        },
    }
    response = client.post("/api/cam/jobs/risk_report", json=payload)
    assert response.status_code == 200


def test_risk_report_submit_returns_id(client):
    """POST /api/cam/jobs/risk_report returns report id."""
    payload = {
        "job_id": "test-returns-id",
        "issues": [],
        "analytics": {
            "total_issues": 0,
            "severity_counts": {},
            "risk_score": 0.0,
            "total_extra_time_s": 0.0,
            "total_extra_time_human": "0s",
        },
    }
    response = client.post("/api/cam/jobs/risk_report", json=payload)
    data = response.json()
    assert "id" in data
    assert data["id"] is not None
    assert len(data["id"]) > 0


def test_risk_report_submit_returns_created_at(client):
    """POST /api/cam/jobs/risk_report returns created_at timestamp."""
    payload = {
        "job_id": "test-created-at",
        "issues": [],
        "analytics": {
            "total_issues": 0,
            "severity_counts": {},
            "risk_score": 0.0,
            "total_extra_time_s": 0.0,
            "total_extra_time_human": "0s",
        },
    }
    response = client.post("/api/cam/jobs/risk_report", json=payload)
    data = response.json()
    assert "created_at" in data
    assert data["created_at"] is not None


def test_recent_reports_returns_200(client):
    """GET /api/cam/jobs/recent returns 200."""
    response = client.get("/api/cam/jobs/recent")
    assert response.status_code == 200


def test_recent_reports_returns_list(client):
    """GET /api/cam/jobs/recent returns a list."""
    response = client.get("/api/cam/jobs/recent")
    data = response.json()
    assert isinstance(data, list)


def test_recent_reports_accepts_limit(client):
    """GET /api/cam/jobs/recent accepts limit parameter."""
    response = client.get("/api/cam/jobs/recent?limit=10")
    assert response.status_code == 200


def test_job_risk_timeline_returns_200(client):
    """GET /api/cam/jobs/{job_id}/risk_timeline returns 200."""
    response = client.get("/api/cam/jobs/any-job/risk_timeline")
    assert response.status_code == 200


def test_job_risk_timeline_returns_list(client):
    """GET /api/cam/jobs/{job_id}/risk_timeline returns a list."""
    response = client.get("/api/cam/jobs/test-job/risk_timeline")
    data = response.json()
    assert isinstance(data, list)


def test_risk_reports_browse_returns_200(client):
    """GET /api/cam/risk/reports returns 200."""
    response = client.get("/api/cam/risk/reports")
    assert response.status_code == 200


def test_risk_reports_browse_accepts_filters(client):
    """GET /api/cam/risk/reports accepts filter parameters."""
    response = client.get("/api/cam/risk/reports?lane=default&preset=grbl&limit=50")
    assert response.status_code == 200


# =============================================================================
# Integration - Submit and Retrieve
# =============================================================================

def test_submit_and_retrieve_report(client):
    """Submit a report and verify it appears in recent reports."""
    # Submit a report with distinctive job_id
    unique_job_id = "integration-test-12345"
    payload = {
        "job_id": unique_job_id,
        "pipeline_id": "pipe-001",
        "op_id": "op-001",
        "machine_profile_id": "machine-001",
        "post_preset": "grbl",
        "issues": [
            {
                "index": 0,
                "type": "shallow_cut",
                "severity": "medium",
                "x": 10.0,
                "y": 20.0,
            }
        ],
        "analytics": {
            "total_issues": 1,
            "severity_counts": {"medium": 1},
            "risk_score": 0.3,
            "total_extra_time_s": 5.0,
            "total_extra_time_human": "5s",
        },
    }
    submit_response = client.post("/api/cam/jobs/risk_report", json=payload)
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    report_id = submitted["id"]

    # Retrieve recent reports
    recent_response = client.get("/api/cam/jobs/recent?limit=100")
    assert recent_response.status_code == 200
    recent = recent_response.json()

    # Verify our report appears
    found = False
    for r in recent:
        if r.get("id") == report_id:
            found = True
            assert r["job_id"] == unique_job_id
            assert r["total_issues"] == 1
            break

    assert found, f"Report {report_id} not found in recent reports"


def test_submit_and_retrieve_timeline(client):
    """Submit reports for a job and verify timeline."""
    job_id = "timeline-test-job"

    # Submit multiple reports for the same job
    for i in range(3):
        payload = {
            "job_id": job_id,
            "issues": [],
            "analytics": {
                "total_issues": i,
                "severity_counts": {},
                "risk_score": i * 0.1,
                "total_extra_time_s": 0.0,
                "total_extra_time_human": "0s",
            },
        }
        client.post("/api/cam/jobs/risk_report", json=payload)

    # Get timeline for the job
    timeline_response = client.get(f"/api/cam/jobs/{job_id}/risk_timeline")
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()

    # Should have at least 3 reports (may have more from previous test runs)
    job_reports = [r for r in timeline if r.get("job_id") == job_id]
    assert len(job_reports) >= 3
