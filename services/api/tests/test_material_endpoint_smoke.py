"""Smoke tests for Material Database endpoints (M.3 Energy & Heat Model)."""

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

def test_list_materials_endpoint_exists(client):
    """GET /api/material/list endpoint exists."""
    response = client.get("/api/material/list")
    assert response.status_code != 404


def test_get_material_endpoint_exists(client):
    """GET /api/material/get/{mid} endpoint exists."""
    response = client.get("/api/material/get/test-material")
    assert response.status_code in (200, 404)


def test_upsert_material_endpoint_exists(client):
    """POST /api/material/upsert endpoint exists."""
    response = client.post("/api/material/upsert", json={"id": "test"})
    assert response.status_code != 404


# =============================================================================
# List Materials
# =============================================================================

def test_list_materials_returns_200(client):
    """GET /api/material/list returns 200."""
    response = client.get("/api/material/list")
    assert response.status_code == 200


def test_list_materials_returns_list(client):
    """GET /api/material/list returns a list."""
    response = client.get("/api/material/list")
    data = response.json()
    assert isinstance(data, list)


def test_list_materials_has_items(client):
    """GET /api/material/list returns at least one material."""
    response = client.get("/api/material/list")
    data = response.json()
    assert len(data) > 0


def test_material_has_required_fields(client):
    """Material objects have required fields."""
    response = client.get("/api/material/list")
    data = response.json()

    assert len(data) > 0
    material = data[0]

    assert "id" in material
    assert "title" in material
    assert "sce_j_per_mm3" in material
    assert "heat_partition" in material


def test_material_sce_is_numeric(client):
    """Material sce_j_per_mm3 is numeric."""
    response = client.get("/api/material/list")
    data = response.json()

    assert len(data) > 0
    material = data[0]
    assert isinstance(material["sce_j_per_mm3"], (int, float))


def test_material_heat_partition_has_components(client):
    """Material heat_partition has chip/tool/work components."""
    response = client.get("/api/material/list")
    data = response.json()

    assert len(data) > 0
    hp = data[0]["heat_partition"]

    assert "chip" in hp
    assert "tool" in hp
    assert "work" in hp


def test_material_heat_partition_values_are_numeric(client):
    """Heat partition values are numeric."""
    response = client.get("/api/material/list")
    data = response.json()

    assert len(data) > 0
    hp = data[0]["heat_partition"]

    assert isinstance(hp["chip"], (int, float))
    assert isinstance(hp["tool"], (int, float))
    assert isinstance(hp["work"], (int, float))


# =============================================================================
# Get Material by ID
# =============================================================================

def test_get_known_material(client):
    """GET /api/material/get/{mid} returns known material."""
    # First get the list to find a valid ID
    list_response = client.get("/api/material/list")
    materials = list_response.json()

    if len(materials) > 0:
        mid = materials[0]["id"]
        response = client.get(f"/api/material/get/{mid}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == mid


def test_get_maple_hard(client):
    """GET /api/material/get/maple_hard returns maple material."""
    response = client.get("/api/material/get/maple_hard")
    # May not exist in all configurations, but endpoint should work
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "maple_hard"
        assert "Maple" in data["title"] or "maple" in data["title"].lower()


def test_get_unknown_material_returns_404(client):
    """GET /api/material/get/{unknown} returns 404."""
    response = client.get("/api/material/get/nonexistent-material-xyz-123")
    assert response.status_code == 404


def test_get_unknown_material_has_detail(client):
    """404 response has detail message."""
    response = client.get("/api/material/get/nonexistent-material-xyz-123")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data


# =============================================================================
# Upsert Material
# =============================================================================

def test_upsert_requires_id(client):
    """POST /api/material/upsert requires id field."""
    response = client.post("/api/material/upsert", json={
        "title": "Test Material",
        "sce_j_per_mm3": 0.5
    })
    assert response.status_code == 400


def test_upsert_creates_material(client):
    """POST /api/material/upsert creates new material."""
    test_id = "test_smoke_material_create"

    # Clean up if exists from previous test
    client.get(f"/api/material/get/{test_id}")

    response = client.post("/api/material/upsert", json={
        "id": test_id,
        "title": "Test Smoke Material",
        "sce_j_per_mm3": 0.42,
        "heat_partition": {"chip": 0.6, "tool": 0.25, "work": 0.15}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_id
    assert data["status"] in ("created", "updated")


def test_upsert_updates_material(client):
    """POST /api/material/upsert updates existing material."""
    test_id = "test_smoke_material_update"

    # Create first
    client.post("/api/material/upsert", json={
        "id": test_id,
        "title": "Original Title",
        "sce_j_per_mm3": 0.5,
        "heat_partition": {"chip": 0.7, "tool": 0.2, "work": 0.1}
    })

    # Update
    response = client.post("/api/material/upsert", json={
        "id": test_id,
        "title": "Updated Title",
        "sce_j_per_mm3": 0.55,
        "heat_partition": {"chip": 0.65, "tool": 0.25, "work": 0.1}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"

    # Verify update
    get_response = client.get(f"/api/material/get/{test_id}")
    if get_response.status_code == 200:
        updated = get_response.json()
        assert updated["title"] == "Updated Title"
        assert updated["sce_j_per_mm3"] == 0.55


def test_upsert_returns_id(client):
    """POST /api/material/upsert returns the material id."""
    test_id = "test_smoke_material_id"

    response = client.post("/api/material/upsert", json={
        "id": test_id,
        "title": "ID Test",
        "sce_j_per_mm3": 0.4,
        "heat_partition": {"chip": 0.7, "tool": 0.2, "work": 0.1}
    })

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == test_id


# =============================================================================
# Data Integrity
# =============================================================================

def test_heat_partition_sums_to_one(client):
    """Heat partition values should sum close to 1.0 for real materials."""
    response = client.get("/api/material/list")
    data = response.json()

    for material in data:
        # Skip test materials created by other tests
        if material.get("id", "").startswith("test"):
            continue
        hp = material.get("heat_partition", {})
        if hp:
            total = hp.get("chip", 0) + hp.get("tool", 0) + hp.get("work", 0)
            # Allow small floating point tolerance
            assert 0.99 <= total <= 1.01, f"{material['id']} heat partition sums to {total}"


def test_sce_values_are_positive(client):
    """SCE (specific cutting energy) values should be positive for real materials."""
    response = client.get("/api/material/list")
    data = response.json()

    for material in data:
        # Skip test materials created by other tests
        if material.get("id", "").startswith("test"):
            continue
        sce = material.get("sce_j_per_mm3", 0)
        assert sce > 0, f"{material['id']} has non-positive SCE: {sce}"
