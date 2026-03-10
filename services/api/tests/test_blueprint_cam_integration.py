"""
Blueprint → CAM Integration Tests (VEC-GAP-04)
===============================================

Tests the full pipeline from Phase 3 vectorization output to CAM-ready spec:
1. DXF with LWPOLYLINE → extract_loops_from_dxf() → Loop objects
2. PipelineResult dict → adapt_dict_to_cam() → CamReadySpec
3. API endpoint /cam/blueprint/pipeline-adapter/from-pipeline

Resolves: VEC-GAP-04 (Phase 3 → CAM bridge has no integration test)
"""

import io
import tempfile
import os
import pytest
from fastapi.testclient import TestClient

import ezdxf


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def minimal_dxf_bytes():
    """Create minimal DXF file with a closed LWPOLYLINE (100x100mm square)."""
    doc = ezdxf.new('R2000')  # R2000+ required for LWPOLYLINE
    msp = doc.modelspace()

    # Create a closed 100x100mm square on GEOMETRY layer
    # Simulates Phase 3 vectorizer output
    points = [
        (0, 0),
        (100, 0),
        (100, 100),
        (0, 100),
    ]
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'GEOMETRY'})

    # Write to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    return dxf_bytes


@pytest.fixture
def dxf_with_island_bytes():
    """Create DXF with outer boundary and interior island."""
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()

    # Outer boundary: 200x300mm rectangle
    outer = [
        (0, 0),
        (200, 0),
        (200, 300),
        (0, 300),
    ]
    msp.add_lwpolyline(outer, close=True, dxfattribs={'layer': 'GEOMETRY'})

    # Inner island: 50x50mm square (pocket cavity)
    inner = [
        (75, 125),
        (125, 125),
        (125, 175),
        (75, 175),
    ]
    msp.add_lwpolyline(inner, close=True, dxfattribs={'layer': 'GEOMETRY'})

    # Write to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    return dxf_bytes


@pytest.fixture
def mock_pipeline_result():
    """Simulate Phase 4 PipelineResult as dict."""
    return {
        "source_file": "test_blueprint.pdf",
        "extraction": {
            "dimensions_mm": [380.0, 480.0],  # Body width x height
            "entity_count": 42,
        },
        "linking": {
            "association_rate": 0.85,
            "linked_count": 12,
            "unlinked_count": 2,
        },
        "linked_dimensions": {
            "dimensions": [
                {
                    "target_feature": {"category": "pocket_depth"},
                    "text_region": {"value_mm": 18.5},
                },
                {
                    "target_feature": {"category": "control_depth"},
                    "text_region": {"value_mm": 25.0},
                },
            ]
        }
    }


# =============================================================================
# Unit Tests - extract_loops_from_dxf()
# =============================================================================

def test_extract_loops_from_minimal_dxf(minimal_dxf_bytes):
    """extract_loops_from_dxf returns single loop from square DXF."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

    loops, warnings = extract_loops_from_dxf(minimal_dxf_bytes)

    assert len(loops) == 1, f"Expected 1 loop, got {len(loops)}. Warnings: {warnings}"
    assert len(loops[0].pts) == 4, f"Expected 4 points, got {len(loops[0].pts)}"

    # Verify it's roughly a 100x100 square
    xs = [p[0] for p in loops[0].pts]
    ys = [p[1] for p in loops[0].pts]
    assert max(xs) - min(xs) == pytest.approx(100, abs=0.1)
    assert max(ys) - min(ys) == pytest.approx(100, abs=0.1)


def test_extract_loops_with_island(dxf_with_island_bytes):
    """extract_loops_from_dxf returns outer boundary + island."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

    loops, warnings = extract_loops_from_dxf(dxf_with_island_bytes)

    assert len(loops) == 2, f"Expected 2 loops (outer + island), got {len(loops)}. Warnings: {warnings}"


def test_extract_loops_empty_dxf():
    """extract_loops_from_dxf handles empty DXF gracefully."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

    # Create minimal empty DXF
    doc = ezdxf.new('R2000')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            empty_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    loops, warnings = extract_loops_from_dxf(empty_bytes)

    assert len(loops) == 0
    assert len(warnings) > 0  # Should have warning about no loops


def test_extract_loops_invalid_bytes():
    """extract_loops_from_dxf handles invalid bytes gracefully."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

    loops, warnings = extract_loops_from_dxf(b"not a valid dxf file")

    assert len(loops) == 0
    assert len(warnings) > 0


def test_extract_loops_wrong_layer(minimal_dxf_bytes):
    """extract_loops_from_dxf falls back when requested layer not found."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

    loops, warnings = extract_loops_from_dxf(minimal_dxf_bytes, layer_name="NONEXISTENT")

    # Should fall back to any LWPOLYLINE and warn
    assert len(loops) >= 1  # Falls back to GEOMETRY layer
    assert any("NONEXISTENT" in w or "other layers" in w for w in warnings)


# =============================================================================
# Unit Tests - adapt_dict_to_cam()
# =============================================================================

def test_adapt_dict_extracts_dimensions(mock_pipeline_result):
    """adapt_dict_to_cam extracts body dimensions."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    spec = adapt_dict_to_cam(mock_pipeline_result)

    assert spec.body_width_mm == 380.0
    assert spec.body_height_mm == 480.0


def test_adapt_dict_extracts_association_rate(mock_pipeline_result):
    """adapt_dict_to_cam extracts association rate."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    spec = adapt_dict_to_cam(mock_pipeline_result)

    assert spec.association_rate == 0.85


def test_adapt_dict_suggests_tool_params(mock_pipeline_result):
    """adapt_dict_to_cam suggests reasonable CAM parameters."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    spec = adapt_dict_to_cam(mock_pipeline_result)

    # 380mm body width -> should suggest 6.35mm tool
    assert spec.suggested_tool_d_mm == 6.35
    assert spec.suggested_stepdown_mm > 0
    assert spec.suggested_feed_xy > 0


def test_adapt_dict_handles_empty():
    """adapt_dict_to_cam handles empty dict gracefully."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    spec = adapt_dict_to_cam({})

    assert spec.body_width_mm == 0.0
    assert spec.body_height_mm == 0.0
    assert spec.suggested_tool_d_mm > 0  # Should still have defaults


def test_adapt_dict_handles_small_body():
    """adapt_dict_to_cam suggests smaller tool for small bodies."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    small_result = {
        "extraction": {
            "dimensions_mm": [150.0, 200.0],  # Small body
        },
        "linking": {"association_rate": 0.9},
    }

    spec = adapt_dict_to_cam(small_result)

    # 150mm body -> should suggest 3.175mm (1/8") tool
    assert spec.suggested_tool_d_mm == 3.175


def test_adapt_dict_to_dict_serialization(mock_pipeline_result):
    """CamReadySpec.to_dict() produces valid structure."""
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    spec = adapt_dict_to_cam(mock_pipeline_result)
    result = spec.to_dict()

    assert "geometry" in result
    assert "dimensions" in result
    assert "suggested_params" in result
    assert "metadata" in result
    assert "warnings" in result

    assert result["dimensions"]["body_width_mm"] == 380.0
    assert result["suggested_params"]["tool_d_mm"] == 6.35


# =============================================================================
# API Endpoint Tests - /cam/blueprint/pipeline-adapter/*
# =============================================================================

def test_pipeline_adapter_info_endpoint(client):
    """GET /cam/blueprint/pipeline-adapter/info returns module info."""
    response = client.get("/api/cam/blueprint/pipeline-adapter/info")

    assert response.status_code == 200
    data = response.json()
    assert "module" in data
    assert "resolves" in data
    assert "VEC-GAP-03" in data["resolves"]


def test_pipeline_adapter_from_pipeline_endpoint(client, mock_pipeline_result):
    """POST /cam/blueprint/pipeline-adapter/from-pipeline converts result."""
    response = client.post(
        "/api/cam/blueprint/pipeline-adapter/from-pipeline",
        json=mock_pipeline_result
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["dimensions"]["body_width_mm"] == 380.0
    assert data["dimensions"]["body_height_mm"] == 480.0
    assert data["suggested_params"]["tool_d_mm"] == 6.35


def test_pipeline_adapter_from_pipeline_raw_endpoint(client, mock_pipeline_result):
    """POST /cam/blueprint/pipeline-adapter/from-pipeline-raw accepts any dict."""
    response = client.post(
        "/api/cam/blueprint/pipeline-adapter/from-pipeline-raw",
        json=mock_pipeline_result
    )

    assert response.status_code == 200
    data = response.json()

    assert "geometry" in data
    assert "dimensions" in data
    assert "suggested_params" in data


def test_pipeline_adapter_handles_minimal_input(client):
    """Pipeline adapter handles minimal valid input."""
    response = client.post(
        "/api/cam/blueprint/pipeline-adapter/from-pipeline",
        json={
            "source_file": "",
            "extraction": {},
            "linking": {},
            "linked_dimensions": {}
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# =============================================================================
# End-to-End Integration Test
# =============================================================================

def test_full_pipeline_dxf_to_cam_spec(minimal_dxf_bytes, mock_pipeline_result, client):
    """Full integration: DXF → extract_loops → adapt_dict → CamReadySpec."""
    from app.routers.blueprint_cam.extraction import extract_loops_from_dxf
    from app.services.pipeline_cam_adapter import adapt_dict_to_cam

    # Step 1: Extract loops from DXF (simulates Phase 3 output)
    loops, warnings = extract_loops_from_dxf(minimal_dxf_bytes)
    assert len(loops) >= 1, f"No loops extracted. Warnings: {warnings}"

    # Step 2: Simulate Phase 4 result (would normally come from dimension linker)
    # Add extracted geometry info to pipeline result
    enriched_result = mock_pipeline_result.copy()
    enriched_result["extraction"]["loop_count"] = len(loops)

    # Step 3: Convert to CAM spec
    spec = adapt_dict_to_cam(enriched_result)

    # Step 4: Verify CAM spec is valid for toolpath generation
    assert spec.body_width_mm > 0
    assert spec.suggested_tool_d_mm > 0
    assert spec.suggested_stepdown_mm > 0
    assert spec.suggested_feed_xy > 0

    # Step 5: Serialize and verify structure
    cam_dict = spec.to_dict()
    assert cam_dict["suggested_params"]["tool_d_mm"] < cam_dict["dimensions"]["body_width_mm"]


def test_api_roundtrip_pipeline_to_cam(client, mock_pipeline_result):
    """API roundtrip: POST pipeline result → GET CAM spec."""
    # POST to convert
    response = client.post(
        "/api/cam/blueprint/pipeline-adapter/from-pipeline",
        json=mock_pipeline_result
    )

    assert response.status_code == 200
    cam_spec = response.json()

    # Verify CAM spec can feed into adaptive pocket endpoint (structure check)
    assert cam_spec["success"] is True
    assert "suggested_params" in cam_spec

    # The suggested params should be usable for adaptive pocketing
    params = cam_spec["suggested_params"]
    assert params["tool_d_mm"] > 0
    assert params["stepdown_mm"] > 0
    assert params["feed_xy"] > 0


# =============================================================================
# Blueprint CAM Bridge Endpoint Tests
# =============================================================================

def test_blueprint_cam_contour_endpoint_exists(client):
    """POST /cam/blueprint/reconstruct-contours endpoint exists."""
    # This tests the contour reconstruction endpoint is mounted
    response = client.post(
        "/api/cam/blueprint/reconstruct-contours",
        json={"entities": []}
    )
    assert response.status_code != 404


def test_blueprint_cam_preflight_endpoint_exists(client, minimal_dxf_bytes):
    """POST /cam/blueprint/preflight endpoint exists."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/dxf")}
    response = client.post("/api/cam/blueprint/preflight", files=files)
    assert response.status_code != 404


def test_blueprint_cam_to_adaptive_endpoint_exists(client, minimal_dxf_bytes):
    """POST /cam/blueprint/to-adaptive endpoint exists."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/dxf")}
    data = {"tool_d": 6.35}
    response = client.post("/api/cam/blueprint/to-adaptive", files=files, data=data)
    assert response.status_code != 404
