"""Smoke tests for GEN-4 body_gcode_router.py endpoints.

Verifies:
- /api/cam/guitar/status endpoint exists and returns expected structure
- /stratocaster/body/gcode, /les_paul/body/gcode, /flying_v/body/gcode require auth
- /{model_id}/neck/gcode requires auth
- Auth is validated before query params (401 before 422)
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Get test client."""
    from app.main import app
    return TestClient(app)


def test_body_gcode_status_endpoint_exists(client):
    """Test GET /api/cam/guitar/status returns GEN-4 info."""
    response = client.get("/api/cam/guitar/status")
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is True
    assert "gen4_endpoints" in data
    assert "stratocaster" in data["gen4_endpoints"]
    assert "les_paul" in data["gen4_endpoints"]
    assert "flying_v" in data["gen4_endpoints"]
    assert "neck" in data["gen4_endpoints"]

    # Verify structure
    strat = data["gen4_endpoints"]["stratocaster"]
    assert strat["endpoint"] == "/stratocaster/body/gcode"
    assert strat["cam_ready"] is True


def test_stratocaster_body_gcode_requires_auth(client):
    """Test POST /stratocaster/body/gcode without auth returns 401.

    Auth is validated before query params, so unauthenticated requests
    return 401 even if project_id is missing.
    """
    response = client.post("/api/cam/guitar/stratocaster/body/gcode")
    assert response.status_code == 401  # Auth required


def test_stratocaster_body_gcode_invalid_uuid_requires_auth(client):
    """Test POST /stratocaster/body/gcode with invalid UUID still requires auth."""
    response = client.post("/api/cam/guitar/stratocaster/body/gcode?project_id=invalid")
    assert response.status_code == 401  # Auth checked before UUID validation


def test_les_paul_body_gcode_requires_auth(client):
    """Test POST /les_paul/body/gcode requires auth."""
    response = client.post("/api/cam/guitar/les_paul/body/gcode")
    assert response.status_code == 401


def test_flying_v_body_gcode_requires_auth(client):
    """Test POST /flying_v/body/gcode requires auth."""
    response = client.post("/api/cam/guitar/flying_v/body/gcode")
    assert response.status_code == 401


def test_neck_gcode_requires_auth(client):
    """Test POST /{model_id}/neck/gcode requires auth."""
    response = client.post("/api/cam/guitar/stratocaster/neck/gcode")
    assert response.status_code == 401


def test_neck_gcode_invalid_uuid_requires_auth(client):
    """Test POST /{model_id}/neck/gcode with invalid UUID still requires auth."""
    response = client.post("/api/cam/guitar/stratocaster/neck/gcode?project_id=not-a-uuid")
    assert response.status_code == 401


def test_registry_cam_ready_models(client):
    """Test GET /api/cam/guitar/ shows CAM_READY_MODELS."""
    response = client.get("/api/cam/guitar/")
    assert response.status_code == 200
    data = response.json()

    # Find stratocaster in the list
    models_by_id = {m["model_id"]: m for m in data.get("models", [])}

    # Check CAM_READY_MODELS have cam_ready=True
    if "stratocaster" in models_by_id:
        assert models_by_id["stratocaster"]["cam_ready"] is True
