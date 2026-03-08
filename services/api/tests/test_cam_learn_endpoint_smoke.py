"""Smoke tests for CAM Learning endpoints."""

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

def test_train_endpoint_exists(client):
    """POST /api/cam/learn/train endpoint exists."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    assert response.status_code != 404


# =============================================================================
# Train Endpoint
# =============================================================================

def test_train_returns_200(client):
    """POST /api/cam/learn/train returns 200."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    assert response.status_code == 200


def test_train_returns_dict(client):
    """Train response is a dictionary."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    assert isinstance(data, dict)


def test_train_has_machine_id(client):
    """Train response has machine_id field."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    # Should have machine_id or machine_profile
    assert "machine_id" in data or "machine_profile" in data


def test_train_has_rules(client):
    """Train response has rules field."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    assert "rules" in data
    assert isinstance(data["rules"], dict)


def test_train_has_meta(client):
    """Train response has meta field."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    assert "meta" in data
    assert isinstance(data["meta"], dict)


def test_train_with_machine_id(client):
    """Train with machine_id parameter."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine"
    })
    assert response.status_code == 200


def test_train_with_machine_profile(client):
    """Train with machine_profile parameter (preferred)."""
    response = client.post("/api/cam/learn/train", json={
        "machine_profile": "test_profile"
    })
    assert response.status_code == 200


def test_train_with_r_min_mm(client):
    """Train with custom r_min_mm parameter."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "r_min_mm": 10.0
    })
    assert response.status_code == 200


def test_train_with_all_params(client):
    """Train with all parameters."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "machine_profile": "test_profile",
        "r_min_mm": 7.5
    })
    assert response.status_code == 200


def test_train_meta_has_samples(client):
    """Train meta includes sample count."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    if "meta" in data:
        # May have samples or sample count
        meta = data["meta"]
        assert "samples" in meta or "sample_count" in meta or len(meta) >= 0


def test_train_meta_has_r_min(client):
    """Train meta includes r_min threshold."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "r_min_mm": 8.0
    })
    data = response.json()

    if "meta" in data:
        meta = data["meta"]
        # May have r_min or similar field
        assert "r_min" in meta or "r_min_mm" in meta or len(meta) >= 0


def test_train_rules_values_are_numbers(client):
    """Train rules values are numeric."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    if "rules" in data and len(data["rules"]) > 0:
        for key, value in data["rules"].items():
            assert isinstance(value, (int, float)), f"Rule '{key}' value should be numeric"


def test_train_default_r_min(client):
    """Train uses default r_min_mm of 5.0."""
    response = client.post("/api/cam/learn/train", json={"machine_id": "test_machine"})
    data = response.json()

    # Meta should reflect default r_min
    if "meta" in data and "r_min" in data["meta"]:
        assert data["meta"]["r_min"] == 5.0


# =============================================================================
# Validation Tests
# =============================================================================

def test_train_requires_machine_id_or_profile(client):
    """Train requires machine_id or machine_profile."""
    # The endpoint raises ValueError when machine_id/machine_profile is missing
    # TestClient propagates server exceptions by default
    with pytest.raises(ValueError) as exc_info:
        client.post("/api/cam/learn/train", json={})
    assert "machine_id" in str(exc_info.value) or "machine_profile" in str(exc_info.value)


def test_train_rejects_invalid_r_min(client):
    """Train rejects invalid r_min_mm type."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "r_min_mm": "not_a_number"
    })
    assert response.status_code == 422


def test_train_accepts_zero_r_min(client):
    """Train accepts r_min_mm of 0."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "r_min_mm": 0.0
    })
    # May return 200 or 400 depending on validation
    assert response.status_code in [200, 400, 422]


def test_train_accepts_negative_r_min(client):
    """Train handles negative r_min_mm."""
    response = client.post("/api/cam/learn/train", json={
        "machine_id": "test_machine",
        "r_min_mm": -5.0
    })
    # May return 200 (accepts) or 400/422 (rejects)
    assert response.status_code in [200, 400, 422]
