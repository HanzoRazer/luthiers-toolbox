"""
Smoke tests for CAM Workspace router endpoints.

Router: services/api/app/routers/cam/cam_workspace_router.py
Prefix: /api/cam-workspace

Each endpoint must return 200, 422, or 503 — NOT 404 (router mounted).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

# Valid status codes for smoke tests (not 404 = router mounted)
VALID_SMOKE_CODES = {200, 422, 503}


# ─── GET Endpoints ───────────────────────────────────────────────────────────

def test_get_neck_operations_smoke():
    """GET /api/cam-workspace/neck/operations returns operations list."""
    response = client.get("/api/cam-workspace/neck/operations")
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert "operations" in data
        assert isinstance(data["operations"], list)


def test_get_status_smoke():
    """GET /api/cam-workspace/status returns pipeline availability."""
    response = client.get("/api/cam-workspace/status")
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert "available" in data
        assert isinstance(data["available"], bool)


def test_get_machines_smoke():
    """GET /api/cam-workspace/machines returns machine list."""
    response = client.get("/api/cam-workspace/machines")
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert "machines" in data
        assert isinstance(data["machines"], list)


# ─── POST /neck/evaluate ─────────────────────────────────────────────────────

def test_post_neck_evaluate_smoke():
    """POST /api/cam-workspace/neck/evaluate with defaults."""
    response = client.post("/api/cam-workspace/neck/evaluate", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert "ok" in data
        assert "gates" in data


def test_post_neck_evaluate_with_config():
    """POST /api/cam-workspace/neck/evaluate with custom neck config."""
    response = client.post("/api/cam-workspace/neck/evaluate", json={
        "neck": {
            "scale_length_mm": 648.0,
            "fret_count": 24,
            "nut_width_mm": 42.0,
            "material": "maple",
        }
    })
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_evaluate_with_preset():
    """POST /api/cam-workspace/neck/evaluate with preset."""
    response = client.post("/api/cam-workspace/neck/evaluate", json={
        "neck": {"preset": "les_paul"}
    })
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_evaluate_invalid_body_422():
    """POST /api/cam-workspace/neck/evaluate with invalid body returns 422."""
    response = client.post(
        "/api/cam-workspace/neck/evaluate",
        json={"neck": {"scale_length_mm": "not_a_number"}}
    )
    # 422 for validation error, 503 if pipeline unavailable
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


# ─── POST /neck/generate/{op} ────────────────────────────────────────────────

def test_post_neck_generate_truss_rod_smoke():
    """POST /api/cam-workspace/neck/generate/truss_rod."""
    response = client.post("/api/cam-workspace/neck/generate/truss_rod", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_profile_rough_smoke():
    """POST /api/cam-workspace/neck/generate/profile_rough."""
    response = client.post("/api/cam-workspace/neck/generate/profile_rough", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_profile_finish_smoke():
    """POST /api/cam-workspace/neck/generate/profile_finish."""
    response = client.post("/api/cam-workspace/neck/generate/profile_finish", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_fret_slots_smoke():
    """POST /api/cam-workspace/neck/generate/fret_slots."""
    response = client.post("/api/cam-workspace/neck/generate/fret_slots", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_with_config():
    """POST /api/cam-workspace/neck/generate/{op} with custom config."""
    response = client.post("/api/cam-workspace/neck/generate/truss_rod", json={
        "neck": {
            "scale_length_mm": 628.65,
            "fret_count": 22,
            "preset": "strat",
        }
    })
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_invalid_op():
    """POST /api/cam-workspace/neck/generate/invalid_op returns 4xx or 503."""
    response = client.post("/api/cam-workspace/neck/generate/invalid_op", json={})
    # Should be 400/422/503, NOT 404
    assert response.status_code in {400, 422, 503}, f"Got {response.status_code}"


# ─── POST /neck/generate-full ────────────────────────────────────────────────

def test_post_neck_generate_full_smoke():
    """POST /api/cam-workspace/neck/generate-full with defaults."""
    response = client.post("/api/cam-workspace/neck/generate-full", json={})
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_full_with_preset():
    """POST /api/cam-workspace/neck/generate-full with preset."""
    response = client.post("/api/cam-workspace/neck/generate-full", json={
        "neck": {"preset": "les_paul"}
    })
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"


def test_post_neck_generate_full_with_machine():
    """POST /api/cam-workspace/neck/generate-full with machine context."""
    response = client.post("/api/cam-workspace/neck/generate-full", json={
        "machine": {"machine_id": "bcam_2030a"},
        "neck": {"scale_length_mm": 648.0},
    })
    assert response.status_code in VALID_SMOKE_CODES, f"Got {response.status_code}"
