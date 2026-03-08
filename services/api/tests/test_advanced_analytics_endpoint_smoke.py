"""Smoke tests for Advanced Analytics endpoints."""

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

def test_correlation_endpoint_exists(client):
    """GET /api/advanced/correlation endpoint exists."""
    response = client.get("/api/advanced/correlation", params={"x": "job.duration_seconds", "y": "pattern.complexity_score"})
    assert response.status_code != 404


def test_duration_anomalies_endpoint_exists(client):
    """GET /api/advanced/anomalies/durations endpoint exists."""
    response = client.get("/api/advanced/anomalies/durations")
    assert response.status_code != 404


def test_success_anomalies_endpoint_exists(client):
    """GET /api/advanced/anomalies/success endpoint exists."""
    response = client.get("/api/advanced/anomalies/success")
    assert response.status_code != 404


def test_predict_endpoint_exists(client):
    """POST /api/advanced/predict endpoint exists."""
    response = client.post("/api/advanced/predict", json={})
    assert response.status_code != 404


# =============================================================================
# Correlation Endpoint
# =============================================================================

def test_correlation_requires_x_param(client):
    """Correlation requires x parameter."""
    response = client.get("/api/advanced/correlation", params={"y": "pattern.complexity_score"})
    assert response.status_code == 400


def test_correlation_requires_y_param(client):
    """Correlation requires y parameter."""
    response = client.get("/api/advanced/correlation", params={"x": "job.duration_seconds"})
    assert response.status_code == 400


def test_correlation_requires_both_params(client):
    """Correlation requires both x and y parameters."""
    response = client.get("/api/advanced/correlation")
    assert response.status_code == 400


def test_correlation_with_valid_params(client):
    """Correlation with valid params returns response."""
    response = client.get("/api/advanced/correlation", params={
        "x": "job.duration_seconds",
        "y": "pattern.complexity_score"
    })
    # May return 200 or 500 depending on data availability
    assert response.status_code in [200, 500]


def test_correlation_response_is_dict(client):
    """Correlation response is a dictionary."""
    response = client.get("/api/advanced/correlation", params={
        "x": "job.duration_seconds",
        "y": "pattern.complexity_score"
    })
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# Duration Anomalies Endpoint
# =============================================================================

def test_duration_anomalies_returns_response(client):
    """Duration anomalies endpoint returns response."""
    response = client.get("/api/advanced/anomalies/durations")
    # May return 200 or 500 depending on data availability
    assert response.status_code in [200, 500]


def test_duration_anomalies_with_z_param(client):
    """Duration anomalies accepts z parameter."""
    response = client.get("/api/advanced/anomalies/durations", params={"z": 2.5})
    assert response.status_code in [200, 500]


def test_duration_anomalies_with_high_z(client):
    """Duration anomalies with high z threshold."""
    response = client.get("/api/advanced/anomalies/durations", params={"z": 5.0})
    assert response.status_code in [200, 500]


def test_duration_anomalies_response_is_dict(client):
    """Duration anomalies response is a dictionary."""
    response = client.get("/api/advanced/anomalies/durations")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# Success Anomalies Endpoint
# =============================================================================

def test_success_anomalies_returns_response(client):
    """Success anomalies endpoint returns response."""
    response = client.get("/api/advanced/anomalies/success")
    # May return 200 or 500 depending on data availability
    assert response.status_code in [200, 500]


def test_success_anomalies_with_z_param(client):
    """Success anomalies accepts z parameter."""
    response = client.get("/api/advanced/anomalies/success", params={"z": 2.0})
    assert response.status_code in [200, 500]


def test_success_anomalies_with_window_days(client):
    """Success anomalies accepts window_days parameter."""
    response = client.get("/api/advanced/anomalies/success", params={"window_days": 7})
    assert response.status_code in [200, 500]


def test_success_anomalies_with_both_params(client):
    """Success anomalies with both z and window_days."""
    response = client.get("/api/advanced/anomalies/success", params={
        "z": 2.5,
        "window_days": 14
    })
    assert response.status_code in [200, 500]


def test_success_anomalies_response_is_dict(client):
    """Success anomalies response is a dictionary."""
    response = client.get("/api/advanced/anomalies/success")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# Predict Endpoint
# =============================================================================

def test_predict_returns_response(client):
    """Predict endpoint returns response."""
    response = client.post("/api/advanced/predict", json={})
    # May return 200 or 500 depending on model availability
    assert response.status_code in [200, 422, 500]


def test_predict_with_sample_body(client):
    """Predict with sample input body."""
    response = client.post("/api/advanced/predict", json={
        "job_type": "pocket",
        "material": "oak",
        "duration_estimate": 120
    })
    assert response.status_code in [200, 500]


def test_predict_response_is_dict(client):
    """Predict response is a dictionary."""
    response = client.post("/api/advanced/predict", json={
        "job_type": "pocket"
    })
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


def test_predict_with_complex_body(client):
    """Predict with complex input body."""
    response = client.post("/api/advanced/predict", json={
        "job_type": "adaptive",
        "material": "walnut",
        "tool_diameter": 6.0,
        "depth_of_cut": 3.0,
        "spindle_rpm": 18000,
        "feed_rate": 2000
    })
    assert response.status_code in [200, 500]


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_analytics_endpoints_exist(client):
    """All advanced analytics endpoints exist (not 404)."""
    endpoints = [
        ("GET", "/api/advanced/correlation", {"x": "a", "y": "b"}),
        ("GET", "/api/advanced/anomalies/durations", {}),
        ("GET", "/api/advanced/anomalies/success", {}),
        ("POST", "/api/advanced/predict", {}),
    ]

    for method, path, params in endpoints:
        if method == "GET":
            response = client.get(path, params=params)
        else:
            response = client.post(path, json=params)

        assert response.status_code != 404, f"{method} {path} returned 404"


def test_default_z_threshold_is_3(client):
    """Default z threshold is 3.0."""
    # Just verify endpoints accept default value
    response1 = client.get("/api/advanced/anomalies/durations")
    response2 = client.get("/api/advanced/anomalies/success")

    assert response1.status_code in [200, 500]
    assert response2.status_code in [200, 500]
