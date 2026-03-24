"""Smoke tests for CAM Workspace router — /api/cam-workspace (neck pipeline wizard)."""

import pytest


# =============================================================================
# Endpoint reachability
# =============================================================================

def test_cam_workspace_neck_operations_exists(client):
    """GET /api/cam-workspace/neck/operations returns 200 and list of ops."""
    response = client.get("/api/cam-workspace/neck/operations")
    assert response.status_code == 200
    data = response.json()
    assert "operations" in data
    assert isinstance(data["operations"], list)
    assert "truss_rod" in data["operations"]
    assert "profile_rough" in data["operations"]


def test_cam_workspace_neck_evaluate_exists(client):
    """POST /api/cam-workspace/neck/evaluate accepts body and returns 200 or 503."""
    response = client.post(
        "/api/cam-workspace/neck/evaluate",
        json={
            "machine": {"machine_id": "bcam_2030a"},
            "neck": {"scale_length_mm": 628.65, "fret_count": 22},
        },
    )
    # 200 if pipeline available, 503 if not
    assert response.status_code in [200, 503]


def test_cam_workspace_neck_generate_op_exists(client):
    """POST /api/cam-workspace/neck/generate/{op} accepts body and returns 200, 409, 422, or 503."""
    response = client.post(
        "/api/cam-workspace/neck/generate/truss_rod",
        json={
            "machine": {"machine_id": "bcam_2030a"},
            "neck": {"scale_length_mm": 628.65, "fret_count": 22},
        },
    )
    # 422 if validation fails, 200/409 if pipeline available, 503 if not
    assert response.status_code in [200, 409, 422, 503]


def test_cam_workspace_status_exists(client):
    """GET /api/cam-workspace/status returns 200."""
    response = client.get("/api/cam-workspace/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
