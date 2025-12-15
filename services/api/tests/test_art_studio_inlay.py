# tests/test_art_studio_inlay.py

"""
Tests for Art Studio Inlay Router and Calculator.

Tests cover:
- Fretboard inlay position calculation
- Pattern types (dot, diamond, block, parallelogram)
- DXF export with R12 compatibility
- Preset listing and retrieval
- 12-TET fret position formula
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for API."""
    from app.main import app
    return TestClient(app)


class TestInlayCalculator:
    """Tests for inlay calculator module."""

    def test_fret_position_formula(self):
        """Test 12-TET fret position calculation."""
        from app.calculators.inlay_calc import fret_position_mm
        
        scale_length = 648.0  # 25.5"
        
        # Fret 12 should be at half scale length
        fret_12_pos = fret_position_mm(12, scale_length)
        assert abs(fret_12_pos - scale_length / 2) < 0.1
        
        # Fret 0 is at nut (0)
        assert fret_position_mm(0, scale_length) == 0.0
        
        # Frets increase in distance from nut
        fret_5 = fret_position_mm(5, scale_length)
        fret_7 = fret_position_mm(7, scale_length)
        assert fret_7 > fret_5

    def test_fret_midpoint_calculation(self):
        """Test midpoint calculation for inlay placement."""
        from app.calculators.inlay_calc import fret_midpoint_mm, fret_position_mm
        
        scale_length = 648.0
        
        # Midpoint of fret 5 should be between frets 4 and 5
        mid_5 = fret_midpoint_mm(5, scale_length)
        pos_4 = fret_position_mm(4, scale_length)
        pos_5 = fret_position_mm(5, scale_length)
        
        assert pos_4 < mid_5 < pos_5

    def test_calculate_dot_inlays(self):
        """Test dot inlay generation."""
        from app.calculators.inlay_calc import (
            InlayCalcInput,
            InlayPatternType,
            calculate_fretboard_inlays,
        )
        
        input_data = InlayCalcInput(
            pattern_type=InlayPatternType.DOT,
            fret_positions=[3, 5, 7, 9, 12],
            double_at_12=True,
            marker_diameter_mm=6.0,
        )
        
        result = calculate_fretboard_inlays(input_data)
        
        # 4 single dots + 2 at fret 12 = 6 shapes
        assert result.total_shapes == 6
        assert result.pattern_type == InlayPatternType.DOT
        
        # All shapes should be dots
        for shape in result.shapes:
            assert shape.pattern_type == InlayPatternType.DOT
            assert shape.width_mm == 6.0

    def test_calculate_block_inlays(self):
        """Test block inlay generation."""
        from app.calculators.inlay_calc import (
            InlayCalcInput,
            InlayPatternType,
            calculate_fretboard_inlays,
        )
        
        input_data = InlayCalcInput(
            pattern_type=InlayPatternType.BLOCK,
            fret_positions=[1, 3, 5, 7, 9],
            double_at_12=False,
            block_width_mm=38.0,
            block_height_mm=9.0,
        )
        
        result = calculate_fretboard_inlays(input_data)
        
        assert result.total_shapes == 5
        assert result.pattern_type == InlayPatternType.BLOCK
        
        # Check shape dimensions
        for shape in result.shapes:
            assert shape.width_mm == 38.0
            assert shape.height_mm == 9.0
            assert shape.vertices is not None

    def test_calculate_diamond_inlays(self):
        """Test diamond inlay generation."""
        from app.calculators.inlay_calc import (
            InlayCalcInput,
            InlayPatternType,
            calculate_fretboard_inlays,
        )
        
        input_data = InlayCalcInput(
            pattern_type=InlayPatternType.DIAMOND,
            fret_positions=[3, 5, 7],
            double_at_12=False,
            marker_diameter_mm=8.0,
        )
        
        result = calculate_fretboard_inlays(input_data)
        
        assert result.total_shapes == 3
        assert result.pattern_type == InlayPatternType.DIAMOND
        
        # Diamonds should have 4 vertices
        for shape in result.shapes:
            assert shape.vertices is not None
            assert len(shape.vertices) == 4

    def test_presets_available(self):
        """Test that inlay presets are available."""
        from app.calculators.inlay_calc import list_presets, get_preset
        
        presets = list_presets()
        assert len(presets) >= 4
        assert "dot_standard" in presets
        assert "block_gibson" in presets
        
        # Get a specific preset
        preset = get_preset("dot_standard")
        assert preset is not None
        assert 12 in preset.fret_positions


class TestInlayRouter:
    """Tests for inlay router endpoints."""

    def test_preview_endpoint(self, client):
        """Test POST /api/art-studio/inlay/preview."""
        response = client.post(
            "/api/art-studio/inlay/preview",
            json={
                "pattern_type": "dot",
                "fret_positions": [3, 5, 7, 9, 12],
                "double_at_12": True,
                "marker_diameter_mm": 6.0,
                "scale_length_mm": 648.0,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert data["result"]["total_shapes"] == 6
        assert data["result"]["pattern_type"] == "dot"
        assert "preview_svg" in data

    def test_preview_with_defaults(self, client):
        """Test preview with default values."""
        response = client.post(
            "/api/art-studio/inlay/preview",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["pattern_type"] == "dot"

    def test_export_dxf_endpoint(self, client):
        """Test POST /api/art-studio/inlay/export-dxf."""
        response = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={
                "pattern_type": "dot",
                "fret_positions": [3, 5, 7],
                "marker_diameter_mm": 6.0,
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        
        # Check DXF content
        content = response.content.decode("utf-8")
        assert "SECTION" in content
        assert "ENTITIES" in content
        assert "CIRCLE" in content  # Dots are circles

    def test_export_dxf_r12_format(self, client):
        """Test that DXF export defaults to R12."""
        response = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={
                "pattern_type": "dot",
                "fret_positions": [3, 5, 7],
            }
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # R12 format marker
        assert "AC1009" in content

    def test_export_dxf_block_uses_lines(self, client):
        """Test that block inlays use LINE segments in R12."""
        response = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={
                "pattern_type": "block",
                "fret_positions": [1, 3, 5],
                "block_width_mm": 38.0,
                "dxf_version": "R12",
            }
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # R12 uses LINE, not LWPOLYLINE
        assert "LINE" in content

    def test_list_presets_endpoint(self, client):
        """Test GET /api/art-studio/inlay/presets."""
        response = client.get("/api/art-studio/inlay/presets")
        
        assert response.status_code == 200
        presets = response.json()
        
        assert isinstance(presets, list)
        assert len(presets) >= 4
        
        # Check preset structure
        preset_names = [p["name"] for p in presets]
        assert "dot_standard" in preset_names
        assert "block_gibson" in preset_names

    def test_get_preset_endpoint(self, client):
        """Test GET /api/art-studio/inlay/presets/{name}."""
        response = client.get("/api/art-studio/inlay/presets/dot_standard")
        
        assert response.status_code == 200
        preset = response.json()
        
        assert preset["pattern_type"] == "dot"
        assert 12 in preset["fret_positions"]

    def test_get_preset_not_found(self, client):
        """Test GET /api/art-studio/inlay/presets/{name} with invalid name."""
        response = client.get("/api/art-studio/inlay/presets/nonexistent")
        
        assert response.status_code == 404

    def test_preview_preset_endpoint(self, client):
        """Test POST /api/art-studio/inlay/preset/{name}/preview."""
        response = client.post("/api/art-studio/inlay/preset/block_gibson/preview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["result"]["pattern_type"] == "block"

    def test_pattern_types_endpoint(self, client):
        """Test GET /api/art-studio/inlay/pattern-types."""
        response = client.get("/api/art-studio/inlay/pattern-types")
        
        assert response.status_code == 200
        types = response.json()
        
        assert "dot" in types
        assert "diamond" in types
        assert "block" in types
        assert "parallelogram" in types

    def test_dxf_versions_endpoint(self, client):
        """Test GET /api/art-studio/inlay/dxf-versions."""
        response = client.get("/api/art-studio/inlay/dxf-versions")
        
        assert response.status_code == 200
        versions = response.json()
        
        assert "R12" in versions

    def test_fret_positions_endpoint(self, client):
        """Test GET /api/art-studio/inlay/fret-positions."""
        response = client.get(
            "/api/art-studio/inlay/fret-positions",
            params={"scale_length_mm": 648.0, "max_fret": 24}
        )
        
        assert response.status_code == 200
        positions = response.json()
        
        assert len(positions) == 24
        
        # Check fret 12 is at half scale length
        fret_12 = next(p for p in positions if p["fret_number"] == 12)
        assert abs(fret_12["distance_from_nut_mm"] - 324.0) < 1.0


class TestInlayDXFExport:
    """Tests for inlay DXF export functionality."""

    def test_dxf_contains_inlay_layer(self, client):
        """Test that DXF export includes INLAY_OUTLINE layer."""
        response = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={"fret_positions": [3, 5, 7]}
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        assert "INLAY_OUTLINE" in content

    def test_dxf_filename_reflects_pattern(self, client):
        """Test that filename includes pattern type and fret count."""
        response = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={
                "pattern_type": "diamond",
                "fret_positions": [3, 5, 7, 9, 12],
            }
        )
        
        assert response.status_code == 200
        
        content_disposition = response.headers.get("content-disposition", "")
        assert "diamond" in content_disposition
        assert "5frets" in content_disposition

    def test_dxf_version_selection(self, client):
        """Test different DXF version exports."""
        # R12
        response_r12 = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={"fret_positions": [3], "dxf_version": "R12"}
        )
        assert response_r12.status_code == 200
        assert "AC1009" in response_r12.content.decode("utf-8")
        
        # R2000 (if available)
        response_r2000 = client.post(
            "/api/art-studio/inlay/export-dxf",
            json={"fret_positions": [3], "dxf_version": "R2000"}
        )
        # May succeed or return 400 if not supported
        assert response_r2000.status_code in [200, 400]
