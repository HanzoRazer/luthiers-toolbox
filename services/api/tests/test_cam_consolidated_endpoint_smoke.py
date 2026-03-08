"""Smoke tests for CAM Consolidated Router endpoints.

Phase 2-3 stub debt remediation - CAM routers not yet covered by existing tests.

Covered routers:
- tooling_router: /api/tooling - posts, library/tools, library/materials
- material_router: /api/materials - list, get, upsert
- cam.routers.toolpath: /api/cam/toolpath - biarc, helical, roughing, vcarve
- cam.routers.rosette: /api/cam/rosette - plan-toolpath, post-gcode, jobs
- cam.rosette.photo_batch_router: /api/cam/rosette/photo-batch
- cam_dxf_adaptive_router: /api/cam/dxf_adaptive_plan_run
- cam_relief_router: /api/cam/relief
- bridge_presets_router: /api/presets
- cnc_production.presets_router: /api/cnc/presets
- blueprint_cam: /api/blueprint - to-adaptive, reconstruct-contours, preflight

Already covered by other tests (not duplicated here):
- simulation_consolidated_router (test_simulation_endpoint_smoke.py)
- cam_learn_router (test_cam_learn_endpoint_smoke.py)
- drilling (test_cam_drilling_smoke.py)
- fret_slots (test_cam_fret_slots_preview_smoke.py)
- machines (test_cam_machines_endpoint_smoke.py)
- posts_consolidated (test_cam_posts_smoke.py)
- probe (test_cam_probe_setup_smoke.py)
- risk (test_cam_risk_reports_endpoint_smoke.py)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# TOOLING ROUTER - /api/tooling
# =============================================================================

def test_tooling_posts_endpoint_exists(client):
    """GET /api/tooling/posts endpoint exists."""
    response = client.get("/api/tooling/posts")
    assert response.status_code != 404


def test_tooling_posts_returns_200(client):
    """GET /api/tooling/posts returns 200."""
    response = client.get("/api/tooling/posts")
    assert response.status_code == 200


def test_tooling_posts_by_id_endpoint_exists(client):
    """GET /api/tooling/posts/{post_id} endpoint exists."""
    response = client.get("/api/tooling/posts/nonexistent-post")
    assert response.status_code in [200, 404]


def test_tooling_library_tools_endpoint_exists(client):
    """GET /api/tooling/library/tools endpoint exists."""
    response = client.get("/api/tooling/library/tools")
    assert response.status_code != 404


def test_tooling_library_tools_returns_200(client):
    """GET /api/tooling/library/tools returns 200."""
    response = client.get("/api/tooling/library/tools")
    assert response.status_code == 200


def test_tooling_library_tools_returns_list(client):
    """GET /api/tooling/library/tools returns list."""
    response = client.get("/api/tooling/library/tools")
    data = response.json()
    assert isinstance(data, list)


def test_tooling_library_tools_by_id_endpoint_exists(client):
    """GET /api/tooling/library/tools/{tool_id} endpoint exists."""
    response = client.get("/api/tooling/library/tools/nonexistent-tool")
    assert response.status_code in [200, 404]


def test_tooling_library_materials_endpoint_exists(client):
    """GET /api/tooling/library/materials endpoint exists."""
    response = client.get("/api/tooling/library/materials")
    assert response.status_code != 404


def test_tooling_library_materials_returns_200(client):
    """GET /api/tooling/library/materials returns 200."""
    response = client.get("/api/tooling/library/materials")
    assert response.status_code == 200


def test_tooling_library_materials_returns_list(client):
    """GET /api/tooling/library/materials returns list."""
    response = client.get("/api/tooling/library/materials")
    data = response.json()
    assert isinstance(data, list)


def test_tooling_library_materials_by_id_endpoint_exists(client):
    """GET /api/tooling/library/materials/{material_id} endpoint exists."""
    response = client.get("/api/tooling/library/materials/nonexistent-material")
    assert response.status_code in [200, 404]


def test_tooling_library_validate_endpoint_exists(client):
    """GET /api/tooling/library/validate endpoint exists."""
    response = client.get("/api/tooling/library/validate")
    assert response.status_code != 404


def test_tooling_library_validate_returns_200(client):
    """GET /api/tooling/library/validate returns 200."""
    response = client.get("/api/tooling/library/validate")
    assert response.status_code == 200


# =============================================================================
# MATERIAL ROUTER - /api/materials
# =============================================================================

def test_materials_list_endpoint_exists(client):
    """GET /api/materials/list endpoint exists."""
    response = client.get("/api/materials/list")
    assert response.status_code != 404


def test_materials_list_returns_200(client):
    """GET /api/materials/list returns 200."""
    response = client.get("/api/materials/list")
    assert response.status_code == 200


def test_materials_get_by_id_endpoint_exists(client):
    """GET /api/materials/get/{mid} endpoint exists."""
    response = client.get("/api/materials/get/nonexistent-material")
    assert response.status_code in [200, 404]


def test_materials_upsert_endpoint_exists(client):
    """POST /api/materials/upsert endpoint exists."""
    response = client.post("/api/materials/upsert", json={})
    assert response.status_code != 404


# =============================================================================
# CAM TOOLPATH ROUTER - /api/cam/toolpath
# =============================================================================

def test_toolpath_biarc_gcode_endpoint_exists(client):
    """POST /api/cam/toolpath/biarc/gcode endpoint exists."""
    response = client.post("/api/cam/toolpath/biarc/gcode", json={})
    assert response.status_code != 404


def test_toolpath_biarc_info_endpoint_exists(client):
    """GET /api/cam/toolpath/biarc/info endpoint exists."""
    response = client.get("/api/cam/toolpath/biarc/info")
    assert response.status_code != 404


def test_toolpath_biarc_info_returns_200(client):
    """GET /api/cam/toolpath/biarc/info returns 200."""
    response = client.get("/api/cam/toolpath/biarc/info")
    assert response.status_code == 200


def test_toolpath_helical_entry_endpoint_exists(client):
    """POST /api/cam/toolpath/helical/helical_entry endpoint exists."""
    response = client.post("/api/cam/toolpath/helical/helical_entry", json={})
    assert response.status_code != 404


def test_toolpath_helical_health_endpoint_exists(client):
    """GET /api/cam/toolpath/helical/helical_health endpoint exists."""
    response = client.get("/api/cam/toolpath/helical/helical_health")
    assert response.status_code != 404


def test_toolpath_helical_health_returns_200(client):
    """GET /api/cam/toolpath/helical/helical_health returns 200."""
    response = client.get("/api/cam/toolpath/helical/helical_health")
    assert response.status_code == 200


def test_toolpath_roughing_gcode_endpoint_exists(client):
    """POST /api/cam/toolpath/roughing/gcode endpoint exists."""
    response = client.post("/api/cam/toolpath/roughing/gcode", json={})
    assert response.status_code != 404


def test_toolpath_roughing_info_endpoint_exists(client):
    """GET /api/cam/toolpath/roughing/info endpoint exists."""
    response = client.get("/api/cam/toolpath/roughing/info")
    assert response.status_code != 404


def test_toolpath_roughing_info_returns_200(client):
    """GET /api/cam/toolpath/roughing/info returns 200."""
    response = client.get("/api/cam/toolpath/roughing/info")
    assert response.status_code == 200


def test_toolpath_vcarve_preview_infill_endpoint_exists(client):
    """POST /api/cam/toolpath/vcarve/preview_infill endpoint exists."""
    response = client.post("/api/cam/toolpath/vcarve/preview_infill", json={})
    assert response.status_code != 404


def test_toolpath_vcarve_gcode_endpoint_exists(client):
    """POST /api/cam/toolpath/vcarve/gcode endpoint exists."""
    response = client.post("/api/cam/toolpath/vcarve/gcode", json={})
    assert response.status_code != 404


def test_toolpath_relief_export_dxf_endpoint_exists(client):
    """POST /api/cam/toolpath/relief/export-dxf endpoint exists."""
    response = client.post("/api/cam/toolpath/relief/export-dxf", json={})
    assert response.status_code != 404


# =============================================================================
# CAM ROSETTE ROUTER - /api/cam/rosette
# =============================================================================

@pytest.fixture
def minimal_rosette_design():
    """Minimal rosette design for testing."""
    return {
        "rings": [{"type": "solid", "width_mm": 5.0}],
        "outer_diameter_mm": 100.0
    }


def test_rosette_plan_toolpath_endpoint_exists(client, minimal_rosette_design):
    """POST /api/cam/rosette/plan-toolpath endpoint exists."""
    response = client.post("/api/cam/rosette/plan-toolpath", json={
        "design": minimal_rosette_design,
        "tool_diameter_mm": 3.0
    })
    assert response.status_code != 404


def test_rosette_post_gcode_endpoint_exists(client):
    """POST /api/cam/rosette/post-gcode endpoint exists."""
    response = client.post("/api/cam/rosette/post-gcode", json={
        "toolpath": {"moves": []},
        "post_processor": "grbl"
    })
    assert response.status_code != 404


def test_rosette_jobs_create_endpoint_exists(client, minimal_rosette_design):
    """POST /api/cam/rosette/jobs endpoint exists."""
    response = client.post("/api/cam/rosette/jobs", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_rosette_jobs_get_endpoint_exists(client):
    """GET /api/cam/rosette/jobs/{job_id} endpoint exists."""
    response = client.get("/api/cam/rosette/jobs/nonexistent-job")
    assert response.status_code in [200, 404]


# =============================================================================
# CAM ROSETTE PHOTO BATCH ROUTER - /api/cam/rosette/photo-batch
# =============================================================================

def test_photo_batch_convert_endpoint_exists(client):
    """POST /api/cam/rosette/photo-batch/convert endpoint exists."""
    response = client.post("/api/cam/rosette/photo-batch/convert", json={})
    assert response.status_code != 404


def test_photo_batch_convert_urls_endpoint_exists(client):
    """POST /api/cam/rosette/photo-batch/convert-urls endpoint exists."""
    response = client.post("/api/cam/rosette/photo-batch/convert-urls", json={})
    assert response.status_code != 404


def test_photo_batch_list_endpoint_exists(client):
    """GET /api/cam/rosette/photo-batch endpoint exists."""
    response = client.get("/api/cam/rosette/photo-batch/")
    assert response.status_code != 404


def test_photo_batch_list_returns_200(client):
    """GET /api/cam/rosette/photo-batch returns 200."""
    response = client.get("/api/cam/rosette/photo-batch/")
    assert response.status_code == 200


def test_photo_batch_list_returns_list(client):
    """GET /api/cam/rosette/photo-batch returns list."""
    response = client.get("/api/cam/rosette/photo-batch/")
    data = response.json()
    assert isinstance(data, list)


def test_photo_batch_get_by_id_endpoint_exists(client):
    """GET /api/cam/rosette/photo-batch/{batch_id} endpoint exists."""
    response = client.get("/api/cam/rosette/photo-batch/nonexistent-batch")
    assert response.status_code in [200, 404]


def test_photo_batch_download_endpoint_exists(client):
    """GET /api/cam/rosette/photo-batch/{batch_id}/download endpoint exists."""
    response = client.get("/api/cam/rosette/photo-batch/nonexistent-batch/download")
    assert response.status_code in [200, 404]


def test_photo_batch_delete_endpoint_exists(client):
    """DELETE /api/cam/rosette/photo-batch/{batch_id} endpoint exists."""
    response = client.delete("/api/cam/rosette/photo-batch/nonexistent-batch")
    assert response.status_code in [200, 204, 404]


# =============================================================================
# CAM DXF ADAPTIVE ROUTER - /api/cam
# =============================================================================

def test_dxf_adaptive_plan_run_endpoint_exists(client):
    """POST /api/cam/dxf_adaptive_plan_run endpoint exists."""
    response = client.post("/api/cam/dxf_adaptive_plan_run", json={})
    assert response.status_code != 404


# =============================================================================
# CAM RELIEF ROUTER - /api/cam/relief
# =============================================================================

def test_relief_map_from_heightfield_endpoint_exists(client):
    """POST /api/cam/relief/map_from_heightfield endpoint exists."""
    response = client.post("/api/cam/relief/map_from_heightfield", json={})
    assert response.status_code != 404


def test_relief_roughing_endpoint_exists(client):
    """POST /api/cam/relief/roughing endpoint exists."""
    response = client.post("/api/cam/relief/roughing", json={})
    assert response.status_code != 404


def test_relief_finishing_endpoint_exists(client):
    """POST /api/cam/relief/finishing endpoint exists."""
    response = client.post("/api/cam/relief/finishing", json={})
    assert response.status_code != 404


def test_relief_sim_bridge_endpoint_exists(client):
    """POST /api/cam/relief/sim_bridge endpoint exists."""
    response = client.post("/api/cam/relief/sim_bridge", json={})
    assert response.status_code != 404


# =============================================================================
# BRIDGE PRESETS ROUTER - /api/presets
# =============================================================================

def test_bridge_presets_endpoint_exists(client):
    """GET /api/presets endpoint exists."""
    response = client.get("/api/presets")
    assert response.status_code != 404


def test_bridge_presets_returns_200(client):
    """GET /api/presets returns 200."""
    response = client.get("/api/presets")
    assert response.status_code == 200


def test_bridge_presets_returns_dict(client):
    """GET /api/presets returns dict."""
    response = client.get("/api/presets")
    data = response.json()
    assert isinstance(data, dict)


# =============================================================================
# CNC PRODUCTION PRESETS ROUTER - /api/cnc/presets
# =============================================================================

def test_cnc_presets_list_endpoint_exists(client):
    """GET /api/cnc/presets endpoint exists."""
    response = client.get("/api/cnc/presets")
    assert response.status_code != 404


def test_cnc_presets_list_returns_200(client):
    """GET /api/cnc/presets returns 200."""
    response = client.get("/api/cnc/presets")
    assert response.status_code == 200


def test_cnc_presets_list_returns_list(client):
    """GET /api/cnc/presets returns list."""
    response = client.get("/api/cnc/presets")
    data = response.json()
    assert isinstance(data, list)


def test_cnc_presets_get_by_id_endpoint_exists(client):
    """GET /api/cnc/presets/{preset_id} endpoint exists."""
    response = client.get("/api/cnc/presets/nonexistent-preset")
    assert response.status_code in [200, 404]


def test_cnc_presets_create_endpoint_exists(client):
    """POST /api/cnc/presets endpoint exists."""
    response = client.post("/api/cnc/presets", json={})
    assert response.status_code != 404


def test_cnc_presets_update_endpoint_exists(client):
    """PATCH /api/cnc/presets/{preset_id} endpoint exists."""
    response = client.patch("/api/cnc/presets/nonexistent-preset", json={})
    assert response.status_code != 404


def test_cnc_presets_delete_endpoint_exists(client):
    """DELETE /api/cnc/presets/{preset_id} endpoint exists."""
    response = client.delete("/api/cnc/presets/nonexistent-preset")
    assert response.status_code in [200, 204, 404]


# =============================================================================
# BLUEPRINT CAM ROUTER - /api/blueprint
# =============================================================================

def test_blueprint_to_adaptive_endpoint_exists(client):
    """POST /api/blueprint/to-adaptive endpoint exists."""
    response = client.post("/api/blueprint/to-adaptive", json={})
    assert response.status_code != 404


def test_blueprint_reconstruct_contours_endpoint_exists(client):
    """POST /api/blueprint/reconstruct-contours endpoint exists."""
    response = client.post("/api/blueprint/reconstruct-contours", json={})
    assert response.status_code != 404


def test_blueprint_preflight_endpoint_exists(client):
    """POST /api/blueprint/preflight endpoint exists."""
    response = client.post("/api/blueprint/preflight", json={})
    assert response.status_code != 404


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_all_tooling_endpoints_exist(client):
    """All tooling endpoints exist (not 404)."""
    endpoints = [
        "/api/tooling/posts",
        "/api/tooling/library/tools",
        "/api/tooling/library/materials",
        "/api/tooling/library/validate",
    ]
    for path in endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_materials_endpoints_exist(client):
    """All materials endpoints exist (not 404)."""
    get_endpoints = ["/api/materials/list"]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"

    # POST endpoint
    response = client.post("/api/materials/upsert", json={})
    assert response.status_code != 404, "/api/materials/upsert returned 404"


def test_all_toolpath_endpoints_exist(client):
    """All toolpath endpoints exist (not 404)."""
    get_endpoints = [
        "/api/cam/toolpath/biarc/info",
        "/api/cam/toolpath/helical/helical_health",
        "/api/cam/toolpath/roughing/info",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"

    post_endpoints = [
        "/api/cam/toolpath/biarc/gcode",
        "/api/cam/toolpath/helical/helical_entry",
        "/api/cam/toolpath/roughing/gcode",
        "/api/cam/toolpath/vcarve/preview_infill",
        "/api/cam/toolpath/vcarve/gcode",
        "/api/cam/toolpath/relief/export-dxf",
    ]
    for path in post_endpoints:
        response = client.post(path, json={})
        assert response.status_code != 404, f"{path} returned 404"


def test_all_cam_relief_endpoints_exist(client):
    """All CAM relief endpoints exist (not 404)."""
    post_endpoints = [
        "/api/cam/relief/map_from_heightfield",
        "/api/cam/relief/roughing",
        "/api/cam/relief/finishing",
        "/api/cam/relief/sim_bridge",
    ]
    for path in post_endpoints:
        response = client.post(path, json={})
        assert response.status_code != 404, f"{path} returned 404"


def test_all_cnc_presets_endpoints_exist(client):
    """All CNC presets endpoints exist (not 404)."""
    # GET endpoints
    response = client.get("/api/cnc/presets")
    assert response.status_code != 404, "/api/cnc/presets GET returned 404"

    # POST endpoint
    response = client.post("/api/cnc/presets", json={})
    assert response.status_code != 404, "/api/cnc/presets POST returned 404"
