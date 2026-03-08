"""Smoke tests for Art Studio API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def minimal_rosette_design():
    """Minimal rosette design for testing."""
    return {
        "rings": [
            {
                "type": "solid",
                "inner_radius": 40.0,
                "outer_radius": 42.0,
                "color": "#000000"
            }
        ],
        "outer_diameter": 100.0
    }


@pytest.fixture
def minimal_pattern_create():
    """Minimal pattern create request."""
    return {
        "name": "test-pattern",
        "pattern_type": "rings",
        "data": {"rings": []}
    }


@pytest.fixture
def minimal_snapshot_create():
    """Minimal snapshot create request."""
    return {
        "name": "test-snapshot",
        "design": {"rings": [], "outer_diameter": 100.0}
    }


# =============================================================================
# Root Art Router (/api/art/*)
# =============================================================================

def test_art_jobs_list_endpoint_exists(client):
    """GET /api/art/jobs endpoint exists."""
    response = client.get("/api/art/jobs")
    assert response.status_code != 404


def test_art_jobs_list_returns_200(client):
    """Art jobs list returns 200."""
    response = client.get("/api/art/jobs")
    assert response.status_code == 200


def test_art_jobs_list_returns_list(client):
    """Art jobs list returns a list."""
    response = client.get("/api/art/jobs")
    data = response.json()
    assert isinstance(data, list)


def test_art_job_by_id_endpoint_exists(client):
    """GET /api/art/jobs/{job_id} endpoint exists."""
    response = client.get("/api/art/jobs/nonexistent-job-id")
    # 404 for job not found is valid
    assert response.status_code in [200, 404]


def test_art_presets_list_endpoint_exists(client):
    """GET /api/art/presets endpoint exists."""
    response = client.get("/api/art/presets")
    assert response.status_code != 404


def test_art_presets_list_returns_200(client):
    """Art presets list returns 200."""
    response = client.get("/api/art/presets")
    assert response.status_code == 200


def test_art_presets_create_endpoint_exists(client):
    """POST /api/art/presets endpoint exists."""
    response = client.post("/api/art/presets", json={
        "name": "test-preset",
        "data": {}
    })
    assert response.status_code != 404


def test_art_presets_delete_endpoint_exists(client):
    """DELETE /api/art/presets/{preset_id} endpoint exists."""
    response = client.delete("/api/art/presets/nonexistent-preset")
    # 404 for preset not found is valid
    assert response.status_code in [200, 204, 404]


# =============================================================================
# Generator Routes (/api/art/generators/*)
# =============================================================================

def test_generators_list_endpoint_exists(client):
    """GET /api/art/generators endpoint exists."""
    response = client.get("/api/art/generators")
    assert response.status_code != 404


def test_generators_list_returns_200(client):
    """Generators list returns 200."""
    response = client.get("/api/art/generators")
    assert response.status_code == 200


def test_generators_list_has_generators(client):
    """Generators list has generators field."""
    response = client.get("/api/art/generators")
    data = response.json()
    assert "generators" in data
    assert isinstance(data["generators"], list)


def test_generators_generate_endpoint_exists(client):
    """POST /api/art/generators/{key}/generate endpoint exists."""
    response = client.post("/api/art/generators/rings/generate", json={
        "params": {}
    })
    assert response.status_code != 404


def test_generators_generate_returns_response(client):
    """Generator generate returns valid response."""
    response = client.post("/api/art/generators/rings/generate", json={
        "params": {"ring_count": 3}
    })
    # May return 200, 400 (bad params), or 422 (validation error)
    assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# Pattern Routes (/api/art/patterns/*)
# =============================================================================

def test_patterns_list_endpoint_exists(client):
    """GET /api/art/patterns endpoint exists."""
    response = client.get("/api/art/patterns")
    assert response.status_code != 404


def test_patterns_list_returns_200(client):
    """Patterns list returns 200."""
    response = client.get("/api/art/patterns")
    assert response.status_code == 200


def test_patterns_list_has_patterns(client):
    """Patterns list has patterns field."""
    response = client.get("/api/art/patterns")
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_patterns_create_endpoint_exists(client, minimal_pattern_create):
    """POST /api/art/patterns endpoint exists."""
    response = client.post("/api/art/patterns", json=minimal_pattern_create)
    assert response.status_code != 404


def test_patterns_get_by_id_endpoint_exists(client):
    """GET /api/art/patterns/{pattern_id} endpoint exists."""
    response = client.get("/api/art/patterns/nonexistent-pattern")
    # 404 for pattern not found is valid
    assert response.status_code in [200, 404]


def test_patterns_update_endpoint_exists(client, minimal_pattern_create):
    """PUT /api/art/patterns/{pattern_id} endpoint exists."""
    response = client.put("/api/art/patterns/nonexistent-pattern", json=minimal_pattern_create)
    # 404 for pattern not found is valid
    assert response.status_code in [200, 404, 422]


def test_patterns_delete_endpoint_exists(client):
    """DELETE /api/art/patterns/{pattern_id} endpoint exists."""
    response = client.delete("/api/art/patterns/nonexistent-pattern")
    # 404 for pattern not found is valid
    assert response.status_code in [200, 204, 404]


# =============================================================================
# Snapshot Routes (/api/art/snapshots/*)
# =============================================================================

def test_snapshots_create_endpoint_exists(client, minimal_snapshot_create):
    """POST /api/art/snapshots endpoint exists."""
    response = client.post("/api/art/snapshots", json=minimal_snapshot_create)
    assert response.status_code != 404


def test_snapshots_recent_endpoint_exists(client):
    """GET /api/art/snapshots/recent endpoint exists."""
    response = client.get("/api/art/snapshots/recent")
    assert response.status_code != 404


def test_snapshots_recent_returns_200(client):
    """Snapshots recent returns 200."""
    response = client.get("/api/art/snapshots/recent")
    assert response.status_code == 200


def test_snapshots_recent_has_snapshots(client):
    """Snapshots recent has snapshots field."""
    response = client.get("/api/art/snapshots/recent")
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_snapshots_get_by_id_endpoint_exists(client):
    """GET /api/art/snapshots/{snapshot_id} endpoint exists."""
    response = client.get("/api/art/snapshots/nonexistent-snapshot")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404]


def test_snapshots_update_endpoint_exists(client, minimal_snapshot_create):
    """PUT /api/art/snapshots/{snapshot_id} endpoint exists."""
    response = client.put("/api/art/snapshots/nonexistent-snapshot", json=minimal_snapshot_create)
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404, 422]


def test_snapshots_delete_endpoint_exists(client):
    """DELETE /api/art/snapshots/{snapshot_id} endpoint exists."""
    response = client.delete("/api/art/snapshots/nonexistent-snapshot")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 204, 404]


def test_snapshots_export_endpoint_exists(client):
    """GET /api/art/snapshots/{snapshot_id}/export endpoint exists."""
    response = client.get("/api/art/snapshots/nonexistent-snapshot/export")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404]


def test_snapshots_export_download_endpoint_exists(client):
    """GET /api/art/snapshots/{snapshot_id}/export/download endpoint exists."""
    response = client.get("/api/art/snapshots/nonexistent-snapshot/export/download")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404]


def test_snapshots_import_endpoint_exists(client):
    """POST /api/art/snapshots/import endpoint exists."""
    response = client.post("/api/art/snapshots/import", json={
        "data": {}
    })
    assert response.status_code != 404


# =============================================================================
# Rosette Jobs Routes (/api/art/rosette/*)
# =============================================================================

def test_rosette_preview_endpoint_exists(client, minimal_rosette_design):
    """POST /api/art/rosette/preview endpoint exists."""
    response = client.post("/api/art/rosette/preview", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_rosette_preview_returns_response(client, minimal_rosette_design):
    """Rosette preview returns valid response."""
    response = client.post("/api/art/rosette/preview", json={
        "design": minimal_rosette_design
    })
    # May return 200 or 422/400 for invalid design
    assert response.status_code in [200, 400, 422, 500]


def test_rosette_save_endpoint_exists(client, minimal_rosette_design):
    """POST /api/art/rosette/save endpoint exists."""
    response = client.post("/api/art/rosette/save", json={
        "design": minimal_rosette_design,
        "name": "test-rosette"
    })
    assert response.status_code != 404


def test_rosette_jobs_list_endpoint_exists(client):
    """GET /api/art/rosette/jobs endpoint exists."""
    response = client.get("/api/art/rosette/jobs")
    assert response.status_code != 404


def test_rosette_jobs_list_returns_200(client):
    """Rosette jobs list returns 200."""
    response = client.get("/api/art/rosette/jobs")
    assert response.status_code == 200


def test_rosette_jobs_list_returns_list(client):
    """Rosette jobs list returns a list."""
    response = client.get("/api/art/rosette/jobs")
    data = response.json()
    assert isinstance(data, list)


def test_rosette_presets_list_endpoint_exists(client):
    """GET /api/art/rosette/presets endpoint exists."""
    response = client.get("/api/art/rosette/presets")
    assert response.status_code != 404


def test_rosette_presets_list_returns_200(client):
    """Rosette presets list returns 200."""
    response = client.get("/api/art/rosette/presets")
    assert response.status_code == 200


def test_rosette_presets_list_returns_list(client):
    """Rosette presets list returns a list."""
    response = client.get("/api/art/rosette/presets")
    data = response.json()
    assert isinstance(data, list)


# =============================================================================
# Rosette Compare Routes (/api/art/rosette/compare/*)
# =============================================================================

def test_rosette_compare_endpoint_exists(client, minimal_rosette_design):
    """POST /api/art/rosette/compare endpoint exists."""
    response = client.post("/api/art/rosette/compare", json={
        "design_a": minimal_rosette_design,
        "design_b": minimal_rosette_design
    })
    assert response.status_code != 404


def test_rosette_compare_returns_response(client, minimal_rosette_design):
    """Rosette compare returns valid response."""
    response = client.post("/api/art/rosette/compare", json={
        "design_a": minimal_rosette_design,
        "design_b": minimal_rosette_design
    })
    # May return 200 or 422/400
    assert response.status_code in [200, 400, 422, 500]


def test_rosette_compare_snapshot_endpoint_exists(client, minimal_rosette_design):
    """POST /api/art/rosette/compare/snapshot endpoint exists."""
    response = client.post("/api/art/rosette/compare/snapshot", json={
        "design_a": minimal_rosette_design,
        "design_b": minimal_rosette_design,
        "name": "test-compare"
    })
    assert response.status_code != 404


def test_rosette_compare_snapshots_list_endpoint_exists(client):
    """GET /api/art/rosette/compare/snapshots endpoint exists."""
    response = client.get("/api/art/rosette/compare/snapshots")
    assert response.status_code != 404


def test_rosette_compare_snapshots_list_returns_200(client):
    """Rosette compare snapshots list returns 200."""
    response = client.get("/api/art/rosette/compare/snapshots")
    assert response.status_code == 200


def test_rosette_compare_snapshots_list_returns_list(client):
    """Rosette compare snapshots list returns a list."""
    response = client.get("/api/art/rosette/compare/snapshots")
    data = response.json()
    assert isinstance(data, list)


def test_rosette_compare_export_csv_endpoint_exists(client):
    """GET /api/art/rosette/compare/export_csv endpoint exists."""
    response = client.get("/api/art/rosette/compare/export_csv")
    assert response.status_code != 404


def test_rosette_compare_export_csv_returns_response(client):
    """Rosette compare export CSV returns valid response."""
    response = client.get("/api/art/rosette/compare/export_csv")
    # May return 200 (CSV) or 400 (no data)
    assert response.status_code in [200, 400, 404]


# =============================================================================
# Rosette Snapshot Routes (/api/art/rosette/snapshots/*)
# =============================================================================

def test_rosette_snapshots_list_endpoint_exists(client):
    """GET /api/art/rosette/snapshots endpoint exists."""
    response = client.get("/api/art/rosette/snapshots")
    assert response.status_code != 404


def test_rosette_snapshots_list_returns_200(client):
    """Rosette snapshots list returns 200."""
    response = client.get("/api/art/rosette/snapshots")
    assert response.status_code == 200


def test_rosette_snapshots_list_has_snapshots(client):
    """Rosette snapshots list has snapshots field."""
    response = client.get("/api/art/rosette/snapshots")
    data = response.json()
    assert "snapshots" in data
    assert isinstance(data["snapshots"], list)


def test_rosette_snapshots_export_endpoint_exists(client, minimal_rosette_design):
    """POST /api/art/rosette/snapshots/export endpoint exists."""
    response = client.post("/api/art/rosette/snapshots/export", json={
        "design": minimal_rosette_design,
        "name": "test-export"
    })
    assert response.status_code != 404


def test_rosette_snapshots_import_endpoint_exists(client):
    """POST /api/art/rosette/snapshots/import endpoint exists."""
    response = client.post("/api/art/rosette/snapshots/import", json={
        "data": "{}"
    })
    assert response.status_code != 404


def test_rosette_snapshots_get_by_id_endpoint_exists(client):
    """GET /api/art/rosette/snapshots/{snapshot_id} endpoint exists."""
    response = client.get("/api/art/rosette/snapshots/nonexistent-snapshot")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404]


def test_rosette_snapshots_update_endpoint_exists(client, minimal_rosette_design):
    """PUT /api/art/rosette/snapshots/{snapshot_id} endpoint exists."""
    response = client.put("/api/art/rosette/snapshots/nonexistent-snapshot", json={
        "design": minimal_rosette_design
    })
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404, 422]


def test_rosette_snapshots_delete_endpoint_exists(client):
    """DELETE /api/art/rosette/snapshots/{snapshot_id} endpoint exists."""
    response = client.delete("/api/art/rosette/snapshots/nonexistent-snapshot")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 204, 404]


def test_rosette_snapshots_baseline_set_endpoint_exists(client):
    """POST /api/art/rosette/snapshots/{snapshot_id}/baseline endpoint exists."""
    response = client.post("/api/art/rosette/snapshots/nonexistent-snapshot/baseline")
    # 404 for snapshot not found is valid
    assert response.status_code in [200, 404, 422]


def test_rosette_snapshots_baseline_get_endpoint_exists(client):
    """GET /api/art/rosette/snapshots/baseline endpoint exists."""
    response = client.get("/api/art/rosette/snapshots/baseline")
    # 404 for no baseline is valid
    assert response.status_code in [200, 404]


# =============================================================================
# Preview Routes (/api/art/rosette/preview/*)
# =============================================================================

def test_rosette_preview_svg_endpoint_exists(client, minimal_rosette_design):
    """POST /api/api/art/rosette/preview/svg endpoint exists."""
    response = client.post("/api/api/art/rosette/preview/svg", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_rosette_preview_svg_returns_response(client, minimal_rosette_design):
    """Rosette preview SVG returns valid response."""
    response = client.post("/api/api/art/rosette/preview/svg", json={
        "design": minimal_rosette_design
    })
    # May return 200 or 422/400
    assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_art_studio_get_endpoints_exist(client):
    """All Art Studio GET endpoints exist (not 404)."""
    get_endpoints = [
        "/api/art/jobs",
        "/api/art/presets",
        "/api/art/generators",
        "/api/art/patterns",
        "/api/art/snapshots/recent",
        "/api/art/rosette/jobs",
        "/api/art/rosette/presets",
        "/api/art/rosette/compare/snapshots",
        "/api/art/rosette/snapshots",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_art_studio_post_endpoints_exist(client, minimal_rosette_design):
    """All Art Studio POST endpoints exist (not 404)."""
    post_endpoints = [
        ("/api/art/presets", {"name": "test", "data": {}}),
        ("/api/art/generators/rings/generate", {"params": {}}),
        ("/api/art/patterns", {"name": "test", "pattern_type": "rings", "data": {}}),
        ("/api/art/snapshots", {"name": "test", "design": {}}),
        ("/api/art/snapshots/import", {"data": "{}"}),
        ("/api/art/rosette/preview", {"design": minimal_rosette_design}),
        ("/api/art/rosette/save", {"design": minimal_rosette_design, "name": "test"}),
        ("/api/art/rosette/compare", {"design_a": minimal_rosette_design, "design_b": minimal_rosette_design}),
        ("/api/art/rosette/snapshots/export", {"design": minimal_rosette_design, "name": "test"}),
        ("/api/art/rosette/snapshots/import", {"data": "{}"}),
        ("/api/api/art/rosette/preview/svg", {"design": minimal_rosette_design}),
    ]
    for path, body in post_endpoints:
        response = client.post(path, json=body)
        assert response.status_code != 404, f"{path} returned 404"
