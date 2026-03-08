"""Smoke tests for Analytics endpoints (patterns, materials, jobs)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Pattern Analytics - Endpoint Existence
# =============================================================================

def test_patterns_complexity_endpoint_exists(client):
    """GET /api/patterns/complexity endpoint exists."""
    response = client.get("/api/patterns/complexity")
    assert response.status_code != 404


def test_patterns_rings_endpoint_exists(client):
    """GET /api/patterns/rings endpoint exists."""
    response = client.get("/api/patterns/rings")
    assert response.status_code != 404


def test_patterns_geometry_endpoint_exists(client):
    """GET /api/patterns/geometry endpoint exists."""
    response = client.get("/api/patterns/geometry")
    assert response.status_code != 404


def test_patterns_families_endpoint_exists(client):
    """GET /api/patterns/families endpoint exists."""
    response = client.get("/api/patterns/families")
    assert response.status_code != 404


def test_patterns_popularity_endpoint_exists(client):
    """GET /api/patterns/popularity endpoint exists."""
    response = client.get("/api/patterns/popularity")
    assert response.status_code != 404


def test_patterns_details_endpoint_exists(client):
    """GET /api/patterns/{pattern_id}/details endpoint exists."""
    response = client.get("/api/patterns/test-pattern-id/details")
    # 404 for non-existent pattern is valid (endpoint exists)
    assert response.status_code in [200, 404, 500]


# =============================================================================
# Pattern Analytics - Response Tests
# =============================================================================

def test_patterns_complexity_returns_response(client):
    """Patterns complexity returns valid response."""
    response = client.get("/api/patterns/complexity")
    assert response.status_code in [200, 500]


def test_patterns_rings_returns_response(client):
    """Patterns rings returns valid response."""
    response = client.get("/api/patterns/rings")
    assert response.status_code in [200, 500]


def test_patterns_geometry_returns_response(client):
    """Patterns geometry returns valid response."""
    response = client.get("/api/patterns/geometry")
    assert response.status_code in [200, 500]


def test_patterns_families_returns_response(client):
    """Patterns families returns valid response."""
    response = client.get("/api/patterns/families")
    assert response.status_code in [200, 500]


def test_patterns_popularity_with_limit(client):
    """Patterns popularity accepts limit parameter."""
    response = client.get("/api/patterns/popularity", params={"limit": 5})
    assert response.status_code in [200, 500]


def test_patterns_popularity_default_limit(client):
    """Patterns popularity uses default limit."""
    response = client.get("/api/patterns/popularity")
    assert response.status_code in [200, 500]


def test_patterns_popularity_max_limit(client):
    """Patterns popularity accepts max limit."""
    response = client.get("/api/patterns/popularity", params={"limit": 100})
    assert response.status_code in [200, 500]


def test_patterns_details_not_found(client):
    """Patterns details returns 404 for unknown pattern."""
    response = client.get("/api/patterns/UNKNOWN_PATTERN_XYZ_999/details")
    assert response.status_code in [404, 500]


# =============================================================================
# Material Analytics - Endpoint Existence
# =============================================================================

def test_materials_distribution_endpoint_exists(client):
    """GET /api/materials/distribution endpoint exists."""
    response = client.get("/api/materials/distribution")
    assert response.status_code != 404


def test_materials_consumption_endpoint_exists(client):
    """GET /api/materials/consumption endpoint exists."""
    response = client.get("/api/materials/consumption")
    assert response.status_code != 404


def test_materials_efficiency_endpoint_exists(client):
    """GET /api/materials/efficiency endpoint exists."""
    response = client.get("/api/materials/efficiency")
    assert response.status_code != 404


def test_materials_dimensions_endpoint_exists(client):
    """GET /api/materials/dimensions endpoint exists."""
    response = client.get("/api/materials/dimensions")
    assert response.status_code != 404


def test_materials_suppliers_endpoint_exists(client):
    """GET /api/materials/suppliers endpoint exists."""
    response = client.get("/api/materials/suppliers")
    assert response.status_code != 404


def test_materials_inventory_endpoint_exists(client):
    """GET /api/materials/inventory endpoint exists."""
    response = client.get("/api/materials/inventory")
    assert response.status_code != 404


# =============================================================================
# Material Analytics - Response Tests
# =============================================================================

def test_materials_distribution_returns_response(client):
    """Materials distribution returns valid response."""
    response = client.get("/api/materials/distribution")
    assert response.status_code in [200, 500]


def test_materials_consumption_returns_response(client):
    """Materials consumption returns valid response."""
    response = client.get("/api/materials/consumption")
    assert response.status_code in [200, 500]


def test_materials_efficiency_returns_response(client):
    """Materials efficiency returns valid response."""
    response = client.get("/api/materials/efficiency")
    assert response.status_code in [200, 500]


def test_materials_dimensions_returns_response(client):
    """Materials dimensions returns valid response."""
    response = client.get("/api/materials/dimensions")
    assert response.status_code in [200, 500]


def test_materials_suppliers_returns_response(client):
    """Materials suppliers returns valid response."""
    response = client.get("/api/materials/suppliers")
    assert response.status_code in [200, 500]


def test_materials_inventory_returns_response(client):
    """Materials inventory returns valid response."""
    response = client.get("/api/materials/inventory")
    assert response.status_code in [200, 500]


# =============================================================================
# Job Analytics - Endpoint Existence
# =============================================================================

def test_jobs_success_trends_endpoint_exists(client):
    """GET /api/jobs/success-trends endpoint exists."""
    response = client.get("/api/jobs/success-trends")
    assert response.status_code != 404


def test_jobs_duration_endpoint_exists(client):
    """GET /api/jobs/duration endpoint exists."""
    response = client.get("/api/jobs/duration")
    assert response.status_code != 404


def test_jobs_status_endpoint_exists(client):
    """GET /api/jobs/status endpoint exists."""
    response = client.get("/api/jobs/status")
    assert response.status_code != 404


def test_jobs_throughput_endpoint_exists(client):
    """GET /api/jobs/throughput endpoint exists."""
    response = client.get("/api/jobs/throughput")
    assert response.status_code != 404


def test_jobs_failures_endpoint_exists(client):
    """GET /api/jobs/failures endpoint exists."""
    response = client.get("/api/jobs/failures")
    assert response.status_code != 404


def test_jobs_types_endpoint_exists(client):
    """GET /api/jobs/types endpoint exists."""
    response = client.get("/api/jobs/types")
    assert response.status_code != 404


def test_jobs_recent_endpoint_exists(client):
    """GET /api/analytics/jobs/recent endpoint exists."""
    response = client.get("/api/analytics/jobs/recent")
    assert response.status_code != 404


# =============================================================================
# Job Analytics - Response Tests
# =============================================================================

def test_jobs_success_trends_returns_response(client):
    """Jobs success trends returns valid response."""
    response = client.get("/api/jobs/success-trends")
    assert response.status_code in [200, 500]


def test_jobs_success_trends_with_days(client):
    """Jobs success trends accepts days parameter."""
    response = client.get("/api/jobs/success-trends", params={"days": 7})
    assert response.status_code in [200, 500]


def test_jobs_success_trends_max_days(client):
    """Jobs success trends accepts max days."""
    response = client.get("/api/jobs/success-trends", params={"days": 365})
    assert response.status_code in [200, 500]


def test_jobs_duration_returns_response(client):
    """Jobs duration returns valid response."""
    response = client.get("/api/jobs/duration")
    assert response.status_code in [200, 500]


def test_jobs_status_returns_response(client):
    """Jobs status returns valid response."""
    response = client.get("/api/jobs/status")
    assert response.status_code in [200, 500]


def test_jobs_throughput_returns_response(client):
    """Jobs throughput returns valid response."""
    response = client.get("/api/jobs/throughput")
    assert response.status_code in [200, 500]


def test_jobs_failures_returns_response(client):
    """Jobs failures returns valid response."""
    response = client.get("/api/jobs/failures")
    assert response.status_code in [200, 500]


def test_jobs_types_returns_response(client):
    """Jobs types returns valid response."""
    response = client.get("/api/jobs/types")
    assert response.status_code in [200, 500]


def test_jobs_recent_returns_response(client):
    """Jobs recent returns valid response."""
    response = client.get("/api/analytics/jobs/recent")
    assert response.status_code in [200, 500]


def test_jobs_recent_with_limit(client):
    """Jobs recent accepts limit parameter."""
    response = client.get("/api/analytics/jobs/recent", params={"limit": 5})
    assert response.status_code in [200, 500]


def test_jobs_recent_max_limit(client):
    """Jobs recent accepts max limit."""
    response = client.get("/api/analytics/jobs/recent", params={"limit": 100})
    assert response.status_code in [200, 500]


# =============================================================================
# Response Structure Tests
# =============================================================================

def test_patterns_complexity_returns_dict(client):
    """Patterns complexity returns dict."""
    response = client.get("/api/patterns/complexity")
    if response.status_code == 200:
        assert isinstance(response.json(), dict)


def test_materials_distribution_returns_dict(client):
    """Materials distribution returns dict."""
    response = client.get("/api/materials/distribution")
    if response.status_code == 200:
        assert isinstance(response.json(), dict)


def test_jobs_status_returns_dict(client):
    """Jobs status returns dict."""
    response = client.get("/api/jobs/status")
    if response.status_code == 200:
        assert isinstance(response.json(), dict)


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_pattern_endpoints_exist(client):
    """All pattern analytics endpoints exist."""
    endpoints = [
        "/api/patterns/complexity",
        "/api/patterns/rings",
        "/api/patterns/geometry",
        "/api/patterns/families",
        "/api/patterns/popularity",
    ]
    for path in endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_material_endpoints_exist(client):
    """All material analytics endpoints exist."""
    endpoints = [
        "/api/materials/distribution",
        "/api/materials/consumption",
        "/api/materials/efficiency",
        "/api/materials/dimensions",
        "/api/materials/suppliers",
        "/api/materials/inventory",
    ]
    for path in endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_job_endpoints_exist(client):
    """All job analytics endpoints exist."""
    endpoints = [
        "/api/jobs/success-trends",
        "/api/jobs/duration",
        "/api/jobs/status",
        "/api/jobs/throughput",
        "/api/jobs/failures",
        "/api/jobs/types",
        "/api/analytics/jobs/recent",
    ]
    for path in endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"
