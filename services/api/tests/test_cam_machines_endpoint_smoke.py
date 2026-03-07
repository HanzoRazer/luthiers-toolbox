"""Smoke tests for CAM Machines endpoints (wired to machine_profiles.json)."""

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

def test_list_machines_endpoint_exists(client):
    """GET /api/cam/machines endpoint exists."""
    response = client.get("/api/cam/machines")
    assert response.status_code != 404


def test_get_machine_endpoint_exists(client):
    """GET /api/cam/machines/{machine_id} endpoint exists."""
    response = client.get("/api/cam/machines/test-machine-id")
    # May be 404 if machine doesn't exist, but endpoint should be registered
    assert response.status_code in (200, 404)


# =============================================================================
# Response Structure
# =============================================================================

def test_list_machines_returns_200(client):
    """GET /api/cam/machines returns 200."""
    response = client.get("/api/cam/machines")
    assert response.status_code == 200


def test_list_machines_returns_list(client):
    """GET /api/cam/machines returns a list."""
    response = client.get("/api/cam/machines")
    data = response.json()
    assert isinstance(data, list)


def test_list_machines_returns_profiles_from_json(client):
    """GET /api/cam/machines returns profiles from machine_profiles.json."""
    response = client.get("/api/cam/machines")
    data = response.json()
    # Should have at least the 3 profiles from machine_profiles.json
    assert len(data) >= 3


def test_machine_profile_has_required_fields(client):
    """Machine profiles have all required fields."""
    response = client.get("/api/cam/machines")
    data = response.json()

    assert len(data) > 0
    profile = data[0]

    assert "id" in profile
    assert "name" in profile
    assert "max_feed_xy" in profile
    assert "rapid" in profile
    assert "accel" in profile
    assert "jerk" in profile
    assert "safe_z_default" in profile


def test_machine_profile_values_are_numeric(client):
    """Machine profile kinematic values are numeric."""
    response = client.get("/api/cam/machines")
    data = response.json()

    assert len(data) > 0
    profile = data[0]

    # These should be numbers or None
    if profile["max_feed_xy"] is not None:
        assert isinstance(profile["max_feed_xy"], (int, float))
    if profile["rapid"] is not None:
        assert isinstance(profile["rapid"], (int, float))
    if profile["accel"] is not None:
        assert isinstance(profile["accel"], (int, float))
    if profile["jerk"] is not None:
        assert isinstance(profile["jerk"], (int, float))
    if profile["safe_z_default"] is not None:
        assert isinstance(profile["safe_z_default"], (int, float))


# =============================================================================
# Known Profiles
# =============================================================================

def test_grbl_3018_profile_exists(client):
    """GRBL_3018_Default profile exists and is accessible."""
    response = client.get("/api/cam/machines/GRBL_3018_Default")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "GRBL_3018_Default"
    assert "GRBL" in data["name"] or "3018" in data["name"]


def test_mach4_router_profile_exists(client):
    """Mach4_Router_4x8 profile exists and is accessible."""
    response = client.get("/api/cam/machines/Mach4_Router_4x8")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "Mach4_Router_4x8"


def test_linuxcnc_kneemill_profile_exists(client):
    """LinuxCNC_KneeMill profile exists and is accessible."""
    response = client.get("/api/cam/machines/LinuxCNC_KneeMill")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "LinuxCNC_KneeMill"


# =============================================================================
# Missing Machine Handling
# =============================================================================

def test_missing_machine_returns_404(client):
    """GET /api/cam/machines/{unknown_id} returns 404."""
    response = client.get("/api/cam/machines/nonexistent-machine-xyz")
    assert response.status_code == 404


def test_missing_machine_has_detail(client):
    """404 response has detail field."""
    response = client.get("/api/cam/machines/nonexistent-machine-xyz")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data


# =============================================================================
# Data Conversion
# =============================================================================

def test_profile_name_from_title(client):
    """Profile name field is derived from title in JSON."""
    response = client.get("/api/cam/machines/GRBL_3018_Default")
    data = response.json()

    # Should have "hobby" or similar from the title "GRBL 3018 (hobby)"
    assert "GRBL" in data["name"] or "hobby" in data["name"]


def test_profile_limits_converted(client):
    """Profile limits are properly converted from nested JSON."""
    response = client.get("/api/cam/machines/GRBL_3018_Default")
    data = response.json()

    # GRBL 3018 has feed_xy: 1200 in JSON
    assert data["max_feed_xy"] == 1200
    # rapid: 3000
    assert data["rapid"] == 3000
    # accel: 600
    assert data["accel"] == 600
    # jerk: 1500
    assert data["jerk"] == 1500


def test_safe_z_default_calculated(client):
    """safe_z_default is calculated from Z travel."""
    response = client.get("/api/cam/machines/GRBL_3018_Default")
    data = response.json()

    # GRBL 3018 has Z travel of 45mm, so safe_z = min(4.5, 5.0) = 4.5
    assert data["safe_z_default"] is not None
    assert data["safe_z_default"] <= 5.0
    assert data["safe_z_default"] > 0
