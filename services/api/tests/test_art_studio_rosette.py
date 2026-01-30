# tests/test_art_studio_rosette.py

"""
Tests for Art Studio Rosette Router and Calculator.

Tests cover:
- Rosette channel calculation (preview endpoint)
- DXF export with circles for soundhole/channel
- Preset listing and retrieval
- SVG preview generation

NOTE (January 2026 - Legacy Router Cleanup):
The rosette channel calculation HTTP API at /api/art-studio/rosette/* was removed.
The endpoints were consolidated to /api/art/rosette/* with a different schema:
- OLD: soundhole_diameter_mm, central_band_mm, inner_purfling, outer_purfling
- NEW: pattern_type, segments, inner_radius, outer_radius

The calculator facade (app.calculators.rosette_calc) still works and is tested
in TestRosetteCalculator. The HTTP endpoint tests in TestRosetteRouter are
skipped until a decision is made about exposing the channel calculation API.
"""

import pytest
from fastapi.testclient import TestClient

# Skip reason for router tests - API schema changed
_ROUTER_SKIP_REASON = (
    "Rosette channel calculation API removed in January 2026 consolidation. "
    "Endpoint moved to /api/art/rosette/* with different schema (pattern_type, "
    "segments, inner_radius, outer_radius). Calculator facade still available."
)


@pytest.fixture
def client():
    """Create test client for API."""
    from app.main import app
    return TestClient(app)


class TestRosetteCalculator:
    """Tests for rosette calculator façade."""

    def test_calculate_rosette_channel_basic(self):
        """Test basic rosette channel calculation."""
        from app.calculators.rosette_calc import (
            RosetteCalcInput,
            PurflingBand,
            calculate_rosette_channel,
        )
        
        input_data = RosetteCalcInput(
            soundhole_diameter_mm=100.0,
            central_band_mm=3.0,
            inner_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
            outer_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
            channel_depth_mm=1.5,
        )
        
        result = calculate_rosette_channel(input_data)
        
        assert result.soundhole_diameter_mm == 100.0
        assert result.soundhole_radius_mm == 50.0
        assert result.channel_width_mm > 0
        assert result.channel_depth_mm == 1.5
        assert result.channel_inner_radius_mm <= result.soundhole_radius_mm
        assert result.channel_outer_radius_mm > result.soundhole_radius_mm

    def test_calculate_rosette_with_multiple_purfling(self):
        """Test rosette with multiple purfling bands."""
        from app.calculators.rosette_calc import (
            RosetteCalcInput,
            PurflingBand,
            calculate_rosette_channel,
        )
        
        input_data = RosetteCalcInput(
            soundhole_diameter_mm=85.0,
            central_band_mm=12.0,
            inner_purfling=[
                PurflingBand(material="bwb", width_mm=1.5),
                PurflingBand(material="maple", width_mm=0.5),
            ],
            outer_purfling=[
                PurflingBand(material="maple", width_mm=0.5),
                PurflingBand(material="bwb", width_mm=1.5),
            ],
            channel_depth_mm=2.0,
        )
        
        result = calculate_rosette_channel(input_data)
        
        assert result.soundhole_diameter_mm == 85.0
        assert result.channel_width_mm > 12.0  # At least central band width
        assert result.stack.central_band_width_mm >= 0

    def test_presets_available(self):
        """Test that presets are available."""
        from app.calculators.rosette_calc import list_presets, get_preset
        
        presets = list_presets()
        assert len(presets) >= 3
        assert "classical_simple" in presets
        assert "steel_string_standard" in presets
        
        # Get a specific preset
        preset = get_preset("steel_string_standard")
        assert preset is not None
        assert preset.soundhole_diameter_mm == 100.0


@pytest.mark.skip(reason=_ROUTER_SKIP_REASON)
class TestRosetteRouter:
    """Tests for rosette router endpoints."""

    def test_preview_endpoint(self, client):
        """Test POST /api/art-studio/rosette/preview."""
        response = client.post(
            "/api/art-studio/rosette/preview",
            json={
                "soundhole_diameter_mm": 100.0,
                "central_band_mm": 3.0,
                "inner_purfling": [{"material": "bwb", "width_mm": 1.5}],
                "outer_purfling": [{"material": "bwb", "width_mm": 1.5}],
                "channel_depth_mm": 1.5,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert data["result"]["soundhole_diameter_mm"] == 100.0
        assert data["result"]["channel_width_mm"] > 0
        assert "preview_svg" in data
        assert data["preview_svg"] is not None

    def test_preview_with_defaults(self, client):
        """Test preview with default values."""
        response = client.post(
            "/api/art-studio/rosette/preview",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["soundhole_diameter_mm"] == 100.0

    def test_export_dxf_endpoint(self, client):
        """Test POST /api/art-studio/rosette/export-dxf."""
        response = client.post(
            "/api/art-studio/rosette/export-dxf",
            json={
                "soundhole_diameter_mm": 100.0,
                "central_band_mm": 3.0,
                "inner_purfling": [{"material": "bwb", "width_mm": 1.5}],
                "outer_purfling": [{"material": "bwb", "width_mm": 1.5}],
                "channel_depth_mm": 1.5,
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        
        # Check DXF content
        content = response.content.decode("utf-8")
        assert "SECTION" in content
        assert "ENTITIES" in content
        assert "CIRCLE" in content  # Rosette uses circles

    def test_list_presets_endpoint(self, client):
        """Test GET /api/art-studio/rosette/presets."""
        response = client.get("/api/art-studio/rosette/presets")
        
        assert response.status_code == 200
        presets = response.json()
        
        assert isinstance(presets, list)
        assert len(presets) >= 3
        
        # Check preset structure
        preset_names = [p["name"] for p in presets]
        assert "classical_simple" in preset_names
        assert "steel_string_standard" in preset_names

    def test_get_preset_endpoint(self, client):
        """Test GET /api/art-studio/rosette/presets/{name}."""
        response = client.get("/api/art-studio/rosette/presets/steel_string_standard")
        
        assert response.status_code == 200
        preset = response.json()
        
        assert preset["soundhole_diameter_mm"] == 100.0
        assert preset["central_band_mm"] == 3.0

    def test_get_preset_not_found(self, client):
        """Test GET /api/art-studio/rosette/presets/{name} with invalid name."""
        response = client.get("/api/art-studio/rosette/presets/nonexistent")
        
        assert response.status_code == 404

    def test_preview_preset_endpoint(self, client):
        """Test POST /api/art-studio/rosette/preset/{name}/preview."""
        response = client.post("/api/art-studio/rosette/preset/classical_simple/preview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["result"]["soundhole_diameter_mm"] == 85.0  # Classical size
        assert "preview_svg" in data


@pytest.mark.skip(reason=_ROUTER_SKIP_REASON)
class TestRosetteDXFExport:
    """Tests for rosette DXF export functionality."""

    def test_dxf_contains_soundhole_layer(self, client):
        """Test that DXF export includes SOUNDHOLE layer."""
        response = client.post(
            "/api/art-studio/rosette/export-dxf",
            json={"soundhole_diameter_mm": 100.0}
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # Check for layer names in DXF
        assert "SOUNDHOLE" in content or "soundhole" in content.lower()

    def test_dxf_has_correct_geometry(self, client):
        """Test that DXF contains expected number of circles."""
        response = client.post(
            "/api/art-studio/rosette/export-dxf",
            json={
                "soundhole_diameter_mm": 100.0,
                "include_purfling_rings": True,
            }
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # Count CIRCLE entities (at least soundhole, inner channel, outer channel)
        circle_count = content.count("AcDbCircle") or content.count("CIRCLE")
        assert circle_count >= 3

    def test_dxf_filename_reflects_parameters(self, client):
        """Test that filename includes soundhole diameter."""
        response = client.post(
            "/api/art-studio/rosette/export-dxf",
            json={"soundhole_diameter_mm": 102.0}
        )
        
        assert response.status_code == 200
        
        content_disposition = response.headers.get("content-disposition", "")
        assert "102mm" in content_disposition
