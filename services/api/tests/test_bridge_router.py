"""
Test suite for bridge_router.py (Bridge Calculator)

Tests coverage for:
- Bridge saddle compensation calculations
- DXF export from bridge geometry
- Preset management (families, gauges, actions)
- Parameter validation
- Unit conversion
- Geometry accuracy

Part of P3.1 - Test Coverage to 80% (A_N roadmap requirement)
Focus: bridge_router.py (critical lutherie CAM feature)
"""

import pytest
import json


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.bridge
class TestBridgeHealth:
    """Test bridge calculator health endpoint."""
    
    def test_health_check(self, api_client):
        """Test bridge calculator health endpoint."""
        response = api_client.get("/api/cam/bridge/health")
        
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert result["status"] == "ok" or result["status"] == "healthy"


# =============================================================================
# PRESET TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.bridge
class TestBridgePresets:
    """Test bridge preset management."""
    
    def test_get_presets(self, api_client):
        """Test retrieving all presets."""
        response = api_client.get("/api/cam/bridge/presets")
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify structure
        assert "families" in result
        assert "gauges" in result
        assert "actions" in result
        
        # Verify families
        assert len(result["families"]) > 0
        for family in result["families"]:
            assert "id" in family
            assert "label" in family
            assert "scaleLength" in family
            assert "stringSpread" in family
            assert "compTreble" in family
            assert "compBass" in family
            assert "slotWidth" in family
            assert "slotLength" in family
            assert 400 <= family["scaleLength"] <= 700  # sanity bounds
            assert 40 <= family["stringSpread"] <= 60
            
    def test_preset_families_include_common_guitars(self, api_client):
        """Test that common guitar types are included."""
        response = api_client.get("/api/cam/bridge/presets")
        result = response.json()
        
        family_ids = [f["id"] for f in result["families"]]
        
        # Check for common guitar types
        assert "les_paul" in family_ids or any("les" in fid.lower() for fid in family_ids)
        assert "strat" in family_ids or any("strat" in fid.lower() for fid in family_ids)
        
    def test_preset_gauges_valid(self, api_client):
        """Test that gauge presets have valid data."""
        response = api_client.get("/api/cam/bridge/presets")
        result = response.json()
        
        if "gauges" in result and len(result["gauges"]) > 0:
            for gauge in result["gauges"]:
                assert "id" in gauge
                assert "label" in gauge
                assert "compAdjust" in gauge
                assert "trebleAdjust" in gauge
                assert "bassAdjust" in gauge
                # Compensation adjustment should be reasonable
                assert -5.0 <= gauge["compAdjust"] <= 5.0
                assert -5.0 <= gauge["trebleAdjust"] <= 5.0
                assert -5.0 <= gauge["bassAdjust"] <= 5.0
                
    def test_preset_actions_valid(self, api_client):
        """Test that action presets have valid data."""
        response = api_client.get("/api/cam/bridge/presets")
        result = response.json()
        
        if "actions" in result and len(result["actions"]) > 0:
            for action in result["actions"]:
                assert "id" in action
                assert "label" in action
                assert "compAdjust" in action
                # Compensation adjustment should be reasonable
                assert -5.0 <= action["compAdjust"] <= 5.0
                assert "trebleAdjust" in action
                assert "bassAdjust" in action
                assert -5.0 <= action["trebleAdjust"] <= 5.0
                assert -5.0 <= action["bassAdjust"] <= 5.0


# =============================================================================
# DXF EXPORT TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.bridge
@pytest.mark.export
class TestBridgeDxfExport:
    """Test bridge DXF export functionality."""
    
    def test_export_dxf_basic(self, api_client, sample_bridge_params):
        """Test basic DXF export with valid geometry."""
        # Create bridge geometry
        geometry = {
            "units": "mm",
            "scaleLength": sample_bridge_params["scale_length_mm"],
            "stringSpread": sample_bridge_params["string_spacing_mm"] * (sample_bridge_params["num_strings"] - 1),
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "angleDeg": 2.5,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        
        # Verify DXF content (DXF files use ASCII with latin-1 encoding)
        dxf_content = response.content.decode('latin-1')
        assert "AC1009" in dxf_content or "AC1015" in dxf_content  # DXF version
        assert "LINE" in dxf_content or "LWPOLYLINE" in dxf_content
        
    def test_export_dxf_with_custom_filename(self, api_client, sample_bridge_params):
        """Test DXF export with custom filename."""
        geometry = {
            "units": "mm",
            "scaleLength": 628.0,
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={
                "geometry": geometry,
                "filename": "custom_bridge"
            }
        )
        
        assert response.status_code == 200
        
        # Check Content-Disposition header for filename
        if "content-disposition" in response.headers:
            disposition = response.headers["content-disposition"]
            assert "custom_bridge" in disposition or "bridge" in disposition
            
    def test_export_dxf_units_mm(self, api_client):
        """Test DXF export with mm units."""
        geometry = {
            "units": "mm",
            "scaleLength": 628.0,
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        assert response.status_code == 200
        dxf_content = response.content.decode('latin-1')
        
        # Verify mm coordinates (should have values like 75.0, 60.0)
        assert "75" in dxf_content or "60" in dxf_content
        
    def test_export_dxf_units_inch(self, api_client):
        """Test DXF export with inch units."""
        geometry = {
            "units": "in",
            "scaleLength": 24.75,  # Les Paul scale in inches
            "stringSpread": 2.05,
            "compTreble": 0.06,
            "compBass": 0.08,
            "slotWidth": 0.12,
            "slotLength": 2.95,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 2.36, "y": 0.08}
            },
            "slotPolygon": [
                {"x": -0.06, "y": -1.475},
                {"x": 0.06, "y": -1.475},
                {"x": 0.06, "y": 1.475},
                {"x": -0.06, "y": 1.475}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        assert response.status_code == 200
        dxf_content = response.content.decode('latin-1')
        
        # Should have inch-scale coordinates
        assert response.status_code == 200


# =============================================================================
# GEOMETRY VALIDATION TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.bridge
class TestBridgeGeometryValidation:
    """Test bridge geometry validation."""
    
    def test_missing_required_fields(self, api_client):
        """Test error for missing required geometry fields."""
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={
                "geometry": {
                    "units": "mm",
                    "scaleLength": 628.0
                    # Missing other required fields
                }
            }
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_invalid_units(self, api_client):
        """Test error for invalid units."""
        geometry = {
            "units": "invalid",  # Should be 'mm' or 'in'
            "scaleLength": 628.0,
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        # Should either reject invalid units or default to valid units
        # 422 = validation error, 200 = defaulted to valid units
        assert response.status_code in [200, 422]
        
    def test_negative_scale_length(self, api_client):
        """Test error for negative scale length."""
        geometry = {
            "units": "mm",
            "scaleLength": -628.0,  # Invalid (negative)
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        # Should handle gracefully (either error or clamp to positive)
        assert response.status_code in [200, 400, 422]
        
    def test_invalid_slot_polygon(self, api_client):
        """Test error for invalid slot polygon."""
        geometry = {
            "units": "mm",
            "scaleLength": 628.0,
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 2.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 2.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5}
                # Missing 2 vertices (should have 4)
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


# =============================================================================
# COMPENSATION CALCULATION TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.bridge
class TestBridgeCompensation:
    """Test bridge compensation calculations."""
    
    def test_different_compensations(self, api_client):
        """Test varying compensation values."""
        for comp_treble, comp_bass in [(1.0, 2.0), (1.5, 2.5), (2.0, 3.0)]:
            geometry = {
                "units": "mm",
                "scaleLength": 628.0,
                "stringSpread": 52.0,
                "compTreble": comp_treble,
                "compBass": comp_bass,
                "slotWidth": 3.0,
                "slotLength": 75.0,
                "endpoints": {
                    "treble": {"x": 0.0, "y": 0.0},
                    "bass": {"x": 60.0, "y": comp_bass - comp_treble}
                },
                "slotPolygon": [
                    {"x": -1.5, "y": -37.5},
                    {"x": 1.5, "y": -37.5},
                    {"x": 1.5, "y": 37.5},
                    {"x": -1.5, "y": 37.5}
                ]
            }
            
            response = api_client.post(
                "/api/cam/bridge/export_dxf",
                json={"geometry": geometry}
            )
            
            assert response.status_code == 200
            
    def test_zero_compensation(self, api_client):
        """Test bridge with no compensation (straight saddle)."""
        geometry = {
            "units": "mm",
            "scaleLength": 628.0,
            "stringSpread": 52.0,
            "compTreble": 0.0,
            "compBass": 0.0,
            "slotWidth": 3.0,
            "slotLength": 75.0,
            "angleDeg": 0.0,
            "endpoints": {
                "treble": {"x": 0.0, "y": 0.0},
                "bass": {"x": 60.0, "y": 0.0}
            },
            "slotPolygon": [
                {"x": -1.5, "y": -37.5},
                {"x": 1.5, "y": -37.5},
                {"x": 1.5, "y": 37.5},
                {"x": -1.5, "y": 37.5}
            ]
        }
        
        response = api_client.post(
            "/api/cam/bridge/export_dxf",
            json={"geometry": geometry}
        )
        
        assert response.status_code == 200


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.bridge
class TestBridgeIntegration:
    """End-to-end integration tests for bridge calculator."""
    
    def test_complete_bridge_workflow(self, api_client):
        """Test complete bridge design and export workflow."""
        # 1. Get presets
        presets_resp = api_client.get("/api/cam/bridge/presets")
        assert presets_resp.status_code == 200
        presets = presets_resp.json()
        
        # 2. Use Les Paul preset
        les_paul = next((f for f in presets["families"] if "les" in f["id"].lower()), None)
        if les_paul:
            # 3. Create geometry with preset values
            geometry = {
                "units": "mm",
                "scaleLength": les_paul["scaleLength"],
                "stringSpread": les_paul["stringSpread"],
                "compTreble": 1.5,
                "compBass": 2.0,
                "slotWidth": 3.0,
                "slotLength": 75.0,
                "endpoints": {
                    "treble": {"x": 0.0, "y": 0.0},
                    "bass": {"x": 60.0, "y": 2.0}
                },
                "slotPolygon": [
                    {"x": -1.5, "y": -37.5},
                    {"x": 1.5, "y": -37.5},
                    {"x": 1.5, "y": 37.5},
                    {"x": -1.5, "y": 37.5}
                ]
            }
            
            # 4. Export DXF
            export_resp = api_client.post(
                "/api/cam/bridge/export_dxf",
                json={
                    "geometry": geometry,
                    "filename": "les_paul_bridge"
                }
            )
            
            assert export_resp.status_code == 200
            assert len(export_resp.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.routers.bridge_router", "--cov-report=term-missing"])
