"""Smoke tests for RMOS Router endpoints."""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Production Bug Markers
# =============================================================================
# Mark tests that expose known production bugs with xfail
# These help document issues without blocking CI

list_runs_filtered_bug = pytest.mark.xfail(
    reason="Production bug: list_runs_filtered() may have unexpected keyword arguments",
    raises=TypeError,
    strict=False
)

# =============================================================================
# RMOS Core Routes (/api/rmos/*)
# =============================================================================

@pytest.fixture
def minimal_rosette_design():
    """Minimal rosette design for testing."""
    return {
        "outer_diameter_mm": 100.0,
        "inner_diameter_mm": 20.0,
        "ring_count": 3,
        "pattern_type": "herringbone"
    }


def test_feasibility_endpoint_exists(client, minimal_rosette_design):
    """POST /api/rmos/feasibility endpoint exists."""
    response = client.post("/api/rmos/feasibility", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_bom_endpoint_exists(client, minimal_rosette_design):
    """POST /api/rmos/bom endpoint exists."""
    response = client.post("/api/rmos/bom", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_toolpaths_endpoint_exists(client, minimal_rosette_design):
    """POST /api/rmos/toolpaths endpoint exists."""
    response = client.post("/api/rmos/toolpaths", json={
        "design": minimal_rosette_design
    })
    assert response.status_code != 404


def test_feasibility_returns_response(client, minimal_rosette_design):
    """Feasibility endpoint returns valid response."""
    response = client.post("/api/rmos/feasibility", json={
        "design": minimal_rosette_design
    })
    # 422 for schema validation errors is acceptable
    assert response.status_code in [200, 400, 422, 500]


def test_bom_returns_response(client, minimal_rosette_design):
    """BOM endpoint returns valid response."""
    response = client.post("/api/rmos/bom", json={
        "design": minimal_rosette_design
    })
    # 422 for schema validation errors is acceptable
    assert response.status_code in [200, 400, 422, 500]


def test_toolpaths_returns_response(client, minimal_rosette_design):
    """Toolpaths endpoint returns valid response."""
    response = client.post("/api/rmos/toolpaths", json={
        "design": minimal_rosette_design
    })
    # 422 for schema validation errors is acceptable
    assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# Analytics Router (/api/rmos/analytics/*)
# =============================================================================

def test_analytics_summary_endpoint_exists(client):
    """GET /api/rmos/analytics/summary endpoint exists."""
    response = client.get("/api/rmos/analytics/summary")
    assert response.status_code != 404


def test_analytics_summary_returns_200(client):
    """Analytics summary returns 200."""
    response = client.get("/api/rmos/analytics/summary")
    assert response.status_code == 200


def test_analytics_summary_has_total_runs(client):
    """Analytics summary has total_runs field."""
    response = client.get("/api/rmos/analytics/summary")
    data = response.json()
    assert "total_runs" in data


def test_analytics_lane_analytics_endpoint_exists(client):
    """GET /api/rmos/analytics/lane-analytics endpoint exists."""
    response = client.get("/api/rmos/analytics/lane-analytics")
    assert response.status_code != 404


def test_analytics_lane_analytics_returns_200(client):
    """Lane analytics returns 200."""
    response = client.get("/api/rmos/analytics/lane-analytics")
    assert response.status_code == 200


def test_analytics_risk_timeline_endpoint_exists(client):
    """GET /api/rmos/analytics/risk-timeline endpoint exists."""
    response = client.get("/api/rmos/analytics/risk-timeline")
    assert response.status_code != 404


def test_analytics_risk_timeline_returns_200(client):
    """Risk timeline returns 200."""
    response = client.get("/api/rmos/analytics/risk-timeline")
    assert response.status_code == 200


def test_analytics_risk_timeline_by_preset_endpoint_exists(client):
    """GET /api/rmos/analytics/risk-timeline/{preset_id} endpoint exists."""
    response = client.get("/api/rmos/analytics/risk-timeline/test-preset")
    assert response.status_code != 404


def test_analytics_trends_endpoint_exists(client):
    """GET /api/rmos/analytics/trends endpoint exists."""
    response = client.get("/api/rmos/analytics/trends")
    assert response.status_code != 404


def test_analytics_trends_returns_200(client):
    """Trends endpoint returns 200."""
    response = client.get("/api/rmos/analytics/trends")
    assert response.status_code == 200


def test_analytics_export_endpoint_exists(client):
    """GET /api/rmos/analytics/export endpoint exists."""
    response = client.get("/api/rmos/analytics/export")
    assert response.status_code != 404


def test_analytics_export_returns_200(client):
    """Export endpoint returns 200."""
    response = client.get("/api/rmos/analytics/export")
    assert response.status_code == 200


def test_analytics_export_returns_json(client):
    """Export endpoint returns JSON."""
    response = client.get("/api/rmos/analytics/export")
    data = response.json()
    assert "export_format" in data


def test_analytics_with_days_param(client):
    """Analytics endpoints accept days parameter."""
    response = client.get("/api/rmos/analytics/summary?days=7")
    assert response.status_code == 200


# =============================================================================
# Logs Router (/api/rmos/logs/*)
# =============================================================================

def test_logs_recent_endpoint_exists(client):
    """GET /api/rmos/logs/recent endpoint exists."""
    response = client.get("/api/rmos/logs/recent")
    assert response.status_code != 404


def test_logs_recent_returns_200(client):
    """Logs recent returns 200."""
    response = client.get("/api/rmos/logs/recent")
    assert response.status_code == 200


def test_logs_recent_has_entries(client):
    """Logs recent has entries field."""
    response = client.get("/api/rmos/logs/recent")
    data = response.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_logs_recent_v2_endpoint_exists(client):
    """GET /api/rmos/logs/recent/v2 endpoint exists."""
    response = client.get("/api/rmos/logs/recent/v2")
    assert response.status_code != 404


def test_logs_recent_v2_returns_200(client):
    """Logs recent v2 returns 200."""
    response = client.get("/api/rmos/logs/recent/v2")
    assert response.status_code == 200


def test_logs_recent_v2_has_cursor(client):
    """Logs recent v2 supports cursor pagination."""
    response = client.get("/api/rmos/logs/recent/v2")
    data = response.json()
    assert "entries" in data
    assert "has_more" in data


def test_logs_get_run_endpoint_exists(client):
    """GET /api/rmos/logs/{run_id} endpoint exists."""
    response = client.get("/api/rmos/logs/nonexistent-run-id")
    # 404 is valid for "run not found"
    assert response.status_code in [200, 404]


def test_logs_with_filters(client):
    """Logs endpoint accepts filter parameters."""
    response = client.get("/api/rmos/logs/recent?mode=art_studio&limit=10")
    assert response.status_code == 200


# =============================================================================
# Runs v2 Router (/api/rmos/runs/*)
# Note: prefix is /api/rmos + router prefix /runs = /api/rmos/runs
# =============================================================================

@pytest.fixture
def minimal_run_create_request():
    """Minimal run create request."""
    return {
        "mode": "test",
        "tool_id": "test_tool",
        "status": "OK",
        "event_type": "test_event",
        "request_summary": {},
        "feasibility": {"score": 0.9, "risk_level": "GREEN"},
    }


def test_runs_v2_create_endpoint_exists(client, minimal_run_create_request):
    """POST /api/rmos/runs endpoint exists."""
    response = client.post("/api/rmos/runs", json=minimal_run_create_request)
    assert response.status_code != 404


def test_runs_v2_list_endpoint_exists(client):
    """GET /api/rmos/runs endpoint exists."""
    response = client.get("/api/rmos/runs")
    assert response.status_code != 404


def test_runs_v2_list_returns_200(client):
    """Runs v2 list returns 200."""
    response = client.get("/api/rmos/runs")
    assert response.status_code == 200


def test_runs_v2_list_has_items(client):
    """Runs v2 list has items field."""
    response = client.get("/api/rmos/runs")
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_runs_v2_diff_endpoint_exists(client):
    """GET /api/rmos/runs/diff endpoint exists."""
    response = client.get("/api/rmos/runs/diff?left_id=a&right_id=b")
    # 404 is valid for "run not found"
    assert response.status_code in [200, 404, 422]


def test_runs_v2_get_run_endpoint_exists(client):
    """GET /api/rmos/runs/{run_id} endpoint exists."""
    response = client.get("/api/rmos/runs/nonexistent-run")
    # 404 is valid for "run not found"
    assert response.status_code in [200, 404]


def test_runs_v2_query_recent_endpoint_exists(client):
    """GET /api/rmos/runs/query/recent endpoint exists."""
    response = client.get("/api/rmos/runs/query/recent")
    assert response.status_code != 404


def test_runs_v2_query_recent_returns_200(client):
    """Query recent returns 200."""
    response = client.get("/api/rmos/runs/query/recent")
    assert response.status_code == 200


def test_runs_v2_query_recent_with_cursor(client):
    """Query recent supports cursor parameter."""
    response = client.get("/api/rmos/runs/query/recent?limit=10")
    data = response.json()
    assert "items" in data or "next_cursor" in data or isinstance(data.get("items"), list) or "entries" in data


def test_runs_v2_advisory_blobs_endpoint_exists(client):
    """GET /api/rmos/runs/{run_id}/advisory/blobs endpoint exists."""
    response = client.get("/api/rmos/runs/nonexistent-run/advisory/blobs")
    # 404 is valid for "run not found"
    assert response.status_code in [200, 404]


def test_runs_v2_delete_requires_reason(client):
    """DELETE /api/rmos/runs/{run_id} requires reason."""
    response = client.delete("/api/rmos/runs/nonexistent-run")
    # Should return 422 for missing reason param
    assert response.status_code in [404, 422]


def test_runs_v2_delete_with_reason(client):
    """DELETE with reason parameter."""
    response = client.delete("/api/rmos/runs/nonexistent-run?reason=test_deletion_reason")
    # 404 for not found, 403 for policy blocked
    assert response.status_code in [404, 403, 429]


def test_runs_v2_list_with_filters(client):
    """Runs v2 list accepts filter parameters."""
    response = client.get("/api/rmos/runs?mode=test&limit=10")
    assert response.status_code == 200


# =============================================================================
# Stub Routes (/api/rmos/*)
# =============================================================================

def test_rosette_segment_ring_endpoint_exists(client):
    """POST /api/rmos/rosette/segment-ring endpoint exists."""
    response = client.post("/api/rmos/rosette/segment-ring", json={})
    assert response.status_code != 404


def test_rosette_segment_ring_returns_response(client):
    """Rosette segment-ring returns valid response."""
    response = client.post("/api/rmos/rosette/segment-ring", json={
        "ring": {
            "ring_id": 0,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3
        }
    })
    assert response.status_code in [200, 400, 500]


def test_rosette_generate_slices_endpoint_exists(client):
    """POST /api/rmos/rosette/generate-slices endpoint exists."""
    response = client.post("/api/rmos/rosette/generate-slices", json={})
    assert response.status_code != 404


def test_rosette_preview_endpoint_exists(client):
    """POST /api/rmos/rosette/preview endpoint exists."""
    response = client.post("/api/rmos/rosette/preview", json={})
    assert response.status_code != 404


def test_rosette_export_cnc_endpoint_exists(client):
    """POST /api/rmos/rosette/export-cnc endpoint exists."""
    response = client.post("/api/rmos/rosette/export-cnc", json={})
    assert response.status_code != 404


def test_rosette_cnc_history_endpoint_exists(client):
    """GET /api/rmos/rosette/cnc-history endpoint exists."""
    response = client.get("/api/rmos/rosette/cnc-history")
    assert response.status_code != 404


def test_rosette_cnc_history_returns_200(client):
    """CNC history returns 200."""
    response = client.get("/api/rmos/rosette/cnc-history")
    assert response.status_code == 200


def test_rosette_cnc_job_endpoint_exists(client):
    """GET /api/rmos/rosette/cnc-job/{job_id} endpoint exists."""
    response = client.get("/api/rmos/rosette/cnc-job/test-job-id")
    # 404 is valid for "job not found"
    assert response.status_code in [200, 404]


def test_live_monitor_drilldown_endpoint_exists(client):
    """GET /api/rmos/live-monitor/{job_id}/drilldown endpoint exists."""
    response = client.get("/api/rmos/live-monitor/test-job-id/drilldown")
    assert response.status_code != 404


def test_live_monitor_drilldown_returns_response(client):
    """Live monitor drilldown returns valid response."""
    response = client.get("/api/rmos/live-monitor/test-job-id/drilldown")
    data = response.json()
    assert "job_id" in data


def test_safety_evaluate_endpoint_exists(client):
    """POST /api/rmos/safety/evaluate endpoint exists."""
    response = client.post("/api/rmos/safety/evaluate", json={})
    assert response.status_code != 404


def test_safety_evaluate_returns_response(client):
    """Safety evaluate returns valid response."""
    response = client.post("/api/rmos/safety/evaluate", json={
        "tool_diameter_mm": 6.0,
        "depth_of_cut_mm": 3.0,
        "stepover_percent": 40,
        "feed_xy_mm_min": 1000
    })
    data = response.json()
    assert "ok" in data


def test_safety_mode_endpoint_exists(client):
    """GET /api/rmos/safety/mode endpoint exists."""
    response = client.get("/api/rmos/safety/mode")
    assert response.status_code != 404


def test_safety_mode_returns_200(client):
    """Safety mode returns 200."""
    response = client.get("/api/rmos/safety/mode")
    assert response.status_code == 200


def test_safety_mode_has_mode_field(client):
    """Safety mode response has mode field."""
    response = client.get("/api/rmos/safety/mode")
    data = response.json()
    assert "mode" in data


def test_safety_create_override_endpoint_exists(client):
    """POST /api/rmos/safety/create-override endpoint exists."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test_action"
    })
    assert response.status_code != 404


def test_safety_create_override_returns_token(client):
    """Safety create-override returns token."""
    response = client.post("/api/rmos/safety/create-override", json={
        "action": "test_action",
        "created_by": "test_user"
    })
    data = response.json()
    assert "token" in data
    assert "expires_at" in data


# =============================================================================
# Validation Router (/api/rmos/validation/*)
# =============================================================================

def test_validation_scenarios_endpoint_exists(client):
    """GET /api/rmos/validation/scenarios endpoint exists."""
    response = client.get("/api/rmos/validation/scenarios")
    assert response.status_code != 404


def test_validation_scenarios_returns_200(client):
    """Validation scenarios returns 200."""
    response = client.get("/api/rmos/validation/scenarios")
    assert response.status_code == 200


def test_validation_scenarios_has_total(client):
    """Validation scenarios has total field."""
    response = client.get("/api/rmos/validation/scenarios")
    data = response.json()
    assert "total" in data


def test_validation_run_endpoint_exists(client):
    """POST /api/rmos/validation/run endpoint exists."""
    response = client.post("/api/rmos/validation/run", json={
        "scenario_id": "nonexistent-scenario"
    })
    # 404 for scenario not found
    assert response.status_code in [200, 404, 422]


def test_validation_run_batch_endpoint_exists(client):
    """POST /api/rmos/validation/run-batch endpoint exists."""
    response = client.post("/api/rmos/validation/run-batch", json={})
    # 400 for no scenarios match
    assert response.status_code in [200, 400, 422]


def test_validation_log_endpoint_exists(client):
    """POST /api/rmos/validation/log endpoint exists."""
    response = client.post("/api/rmos/validation/log", json={
        "scenario_id": "test",
        "scenario_name": "Test Scenario",
        "tier": "baseline",
        "expected_decision": ["GREEN"],
        "actual_decision": "GREEN",
        "expected_export_allowed": True,
        "actual_export_allowed": True,
        "decision_match": True,
        "rules_match": True,
        "export_match": True,
        "passed": True
    })
    assert response.status_code != 404


def test_validation_summary_endpoint_exists(client):
    """GET /api/rmos/validation/summary endpoint exists."""
    response = client.get("/api/rmos/validation/summary")
    assert response.status_code != 404


def test_validation_summary_returns_200(client):
    """Validation summary returns 200."""
    response = client.get("/api/rmos/validation/summary")
    assert response.status_code == 200


def test_validation_sessions_endpoint_exists(client):
    """GET /api/rmos/validation/sessions endpoint exists."""
    response = client.get("/api/rmos/validation/sessions")
    assert response.status_code != 404


def test_validation_sessions_returns_200(client):
    """Validation sessions returns 200."""
    response = client.get("/api/rmos/validation/sessions")
    assert response.status_code == 200


def test_validation_session_by_id_endpoint_exists(client):
    """GET /api/rmos/validation/sessions/{session_id} endpoint exists."""
    response = client.get("/api/rmos/validation/sessions/nonexistent-session")
    # 404 is valid for "session not found"
    assert response.status_code in [200, 404]


def test_validation_runs_endpoint_exists(client):
    """GET /api/rmos/validation/runs endpoint exists."""
    response = client.get("/api/rmos/validation/runs")
    assert response.status_code != 404


def test_validation_runs_returns_200(client):
    """Validation runs returns 200."""
    response = client.get("/api/rmos/validation/runs")
    assert response.status_code == 200


def test_validation_run_by_id_endpoint_exists(client):
    """GET /api/rmos/validation/runs/{run_id} endpoint exists."""
    response = client.get("/api/rmos/validation/runs/nonexistent-run")
    # 404 is valid for "run not found"
    assert response.status_code in [200, 404]


# =============================================================================
# Acoustics Router (/api/rmos/acoustics/*)
# =============================================================================

@pytest.fixture
def minimal_zip_bytes():
    """Create minimal ZIP file bytes for testing."""
    import zipfile
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", '{"schema_version": "1.0.0", "bundle_id": "test"}')
        zf.writestr("validation_report.json", '{"passed": true, "errors": [], "warnings": []}')
        zf.writestr("attachments/test.txt", "test content")
    return buffer.getvalue()


def test_acoustics_import_zip_endpoint_exists(client, minimal_zip_bytes):
    """POST /api/rmos/acoustics/import-zip endpoint exists."""
    files = {"file": ("test.zip", io.BytesIO(minimal_zip_bytes), "application/zip")}
    response = client.post("/api/rmos/acoustics/import-zip", files=files)
    assert response.status_code != 404






# =============================================================================
# Integration Tests
# =============================================================================

def test_all_rmos_core_endpoints_exist(client, minimal_rosette_design):
    """All RMOS core endpoints exist (not 404)."""
    # POST endpoints
    post_endpoints = [
        ("/api/rmos/feasibility", {"design": minimal_rosette_design}),
        ("/api/rmos/bom", {"design": minimal_rosette_design}),
        ("/api/rmos/toolpaths", {"design": minimal_rosette_design}),
    ]
    for path, body in post_endpoints:
        response = client.post(path, json=body)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_analytics_endpoints_exist(client):
    """All analytics endpoints exist (not 404)."""
    get_endpoints = [
        "/api/rmos/analytics/summary",
        "/api/rmos/analytics/lane-analytics",
        "/api/rmos/analytics/risk-timeline",
        "/api/rmos/analytics/trends",
        "/api/rmos/analytics/export",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_logs_endpoints_exist(client):
    """All logs endpoints exist (not 404)."""
    get_endpoints = [
        "/api/rmos/logs/recent",
        "/api/rmos/logs/recent/v2",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_stub_endpoints_exist(client):
    """All stub endpoints exist (not 404)."""
    # POST endpoints
    post_endpoints = [
        ("/api/rmos/rosette/segment-ring", {}),
        ("/api/rmos/rosette/generate-slices", {}),
        ("/api/rmos/rosette/preview", {}),
        ("/api/rmos/rosette/export-cnc", {}),
        ("/api/rmos/safety/evaluate", {}),
        ("/api/rmos/safety/create-override", {"action": "test"}),
    ]
    for path, body in post_endpoints:
        response = client.post(path, json=body)
        assert response.status_code != 404, f"{path} returned 404"

    # GET endpoints
    get_endpoints = [
        "/api/rmos/rosette/cnc-history",
        "/api/rmos/safety/mode",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_validation_endpoints_exist(client):
    """All validation endpoints exist (not 404)."""
    get_endpoints = [
        "/api/rmos/validation/scenarios",
        "/api/rmos/validation/summary",
        "/api/rmos/validation/sessions",
        "/api/rmos/validation/runs",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


