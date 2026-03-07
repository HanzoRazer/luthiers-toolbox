"""Smoke tests for override token generator endpoint."""

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

def test_create_override_endpoint_exists(client):
    """POST /api/rmos/safety/create-override endpoint exists."""
    response = client.post("/api/rmos/safety/create-override", json={})
    assert response.status_code == 200


def test_create_override_returns_token_field(client):
    """POST /api/rmos/safety/create-override returns token field."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "start_job",
    })
    data = response.json()
    assert "token" in data
    assert data["token"] is not None
    assert len(data["token"]) == 8  # 4 bytes hex = 8 chars


def test_create_override_returns_action_field(client):
    """POST /api/rmos/safety/create-override returns action field."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "promote_preset",
    })
    data = response.json()
    assert data["action"] == "promote_preset"


def test_create_override_returns_created_by_field(client):
    """POST /api/rmos/safety/create-override returns created_by field."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "start_job",
        "created_by": "mentor_ross",
    })
    data = response.json()
    assert data["created_by"] == "mentor_ross"


def test_create_override_returns_expires_at_field(client):
    """POST /api/rmos/safety/create-override returns expires_at field."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "start_job",
    })
    data = response.json()
    assert "expires_at" in data
    assert data["expires_at"].endswith("Z")  # RFC3339 UTC


# =============================================================================
# Default Behavior
# =============================================================================

def test_create_override_empty_payload_uses_defaults(client):
    """POST /api/rmos/safety/create-override with empty payload uses defaults."""
    response = client.post("/api/rmos/safety/create-override", json={})
    data = response.json()
    assert data["action"] == "unknown_action"
    assert data["created_by"] == "anonymous"


def test_create_override_ttl_defaults_to_15(client):
    """POST /api/rmos/safety/create-override TTL defaults to 15 minutes."""
    import datetime

    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test",
    })
    data = response.json()

    # Parse expires_at
    expires = datetime.datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)

    # Should expire approximately 15 minutes from now
    delta = expires - now
    assert 14 * 60 <= delta.total_seconds() <= 16 * 60  # 14-16 minute window


def test_create_override_respects_custom_ttl(client):
    """POST /api/rmos/safety/create-override respects custom ttl_minutes."""
    import datetime

    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test",
        "ttl_minutes": 30,
    })
    data = response.json()

    # Parse expires_at
    expires = datetime.datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)

    # Should expire approximately 30 minutes from now
    delta = expires - now
    assert 29 * 60 <= delta.total_seconds() <= 31 * 60  # 29-31 minute window


# =============================================================================
# Token Uniqueness
# =============================================================================

def test_create_override_generates_unique_tokens(client):
    """POST /api/rmos/safety/create-override generates unique tokens."""
    tokens = set()
    for _ in range(10):
        response = client.post("/api/rmos/safety/create-override", json={
            "action": "test",
        })
        data = response.json()
        tokens.add(data["token"])

    # All 10 tokens should be unique
    assert len(tokens) == 10


# =============================================================================
# TTL Bounds
# =============================================================================

def test_create_override_clamps_ttl_minimum(client):
    """POST /api/rmos/safety/create-override clamps TTL to minimum 1 minute."""
    import datetime

    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test",
        "ttl_minutes": 0,  # Should be clamped to 1
    })
    data = response.json()

    expires = datetime.datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)

    delta = expires - now
    assert 0 <= delta.total_seconds() <= 2 * 60  # Within 0-2 minute window


def test_create_override_clamps_ttl_maximum(client):
    """POST /api/rmos/safety/create-override clamps TTL to maximum 120 minutes."""
    import datetime

    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test",
        "ttl_minutes": 999,  # Should be clamped to 120
    })
    data = response.json()

    expires = datetime.datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)

    delta = expires - now
    assert 119 * 60 <= delta.total_seconds() <= 121 * 60  # 119-121 minute window
