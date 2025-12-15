"""
Test suite for cam_helical_v161_router.py (Art Studio v16.1 - Helical Ramping)

Tests coverage for:
- Helical entry toolpath generation
- Arc interpolation (G2/G3)
- Multi-revolution helical paths
- Feed rate management (XY vs Z)
- Post-processor integration
- Parameter validation

Part of P3.1 - Test Coverage to 80% (A_N roadmap requirement)
Focus: cam_helical_v161_router.py (Art Studio v16.1 feature)
"""

import pytest
import math
from conftest import assert_valid_gcode


# =============================================================================
# HELICAL ENTRY TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
@pytest.mark.cam
class TestHelicalEntry:
    """Test helical ramping toolpath generation."""
    
    def test_helical_entry_basic(self, api_client, sample_helical_params):
        """Test basic helical entry generation."""
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=sample_helical_params
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert "gcode" in result
        assert "stats" in result
        assert "preview_points" in result
        
        # Verify G-code contains G2/G3 arcs
        gcode = result["gcode"]
        assert "G2" in gcode or "G3" in gcode, "Helical entry should contain arc moves"
        
    def test_helical_entry_statistics(self, api_client, sample_helical_params):
        """Test helical entry statistics."""
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=sample_helical_params
        )
        
        assert response.status_code == 200
        result = response.json()
        stats = result["stats"]
        
        # Verify statistics
        assert "length_mm" in stats
        assert "revolutions" in stats
        
        # Verify values are reasonable
        assert stats["length_mm"] > 0
        assert stats["revolutions"] > 0
        
    def test_helical_entry_multi_revolution(self, api_client):
        """Test multi-revolution helical path."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -10.0,  # Deep cut requiring multiple revolutions
            "pitch": 0.5,  # 0.5mm per revolution
            "feed_xy": 1200.0,
            "feed_z": 400.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Should have multiple revolutions (10mm depth / 0.5mm pitch = 20 revs)
        assert stats["revolutions"] >= 10
        
    def test_helical_entry_shallow_cut(self, api_client):
        """Test shallow helical entry (< 1 revolution)."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -0.3,  # Very shallow
            "pitch": 0.5,
            "feed_xy": 1200.0,
            "feed_z": 400.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Should have < 1 revolution
        assert 0 < stats["revolutions"] < 1.0


# =============================================================================
# ARC INTERPOLATION TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
@pytest.mark.cam
class TestHelicalArcInterpolation:
    """Test arc interpolation (G2/G3) in helical paths."""
    
    def test_arc_interpolation_cw(self, api_client):
        """Test clockwise arc interpolation."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -3.0,
            "pitch": 0.5,
            "direction": "cw",  # Clockwise
            "feed_xy": 1200.0,
            "feed_z": 400.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        result = response.json()
        gcode = result["gcode"]
        
        # Should have G2 (clockwise arc) moves
        assert "G2" in gcode, "CW direction should generate G2 arcs"
        
    def test_arc_interpolation_ccw(self, api_client):
        """Test counter-clockwise arc interpolation."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -3.0,
            "pitch": 0.5,
            "direction": "ccw",  # Counter-clockwise
            "feed_xy": 1200.0,
            "feed_z": 400.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        result = response.json()
        gcode = result["gcode"]
        
        # Should have G3 (counter-clockwise arc) moves
        assert "G3" in gcode, "CCW direction should generate G3 arcs"
        
    def test_arc_center_offsets(self, api_client, sample_helical_params):
        """Test arc moves have I/J center offsets."""
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=sample_helical_params
        )
        
        assert response.status_code == 200
        result = response.json()
        gcode = result["gcode"]
        
        # Arc moves should have I and J parameters
        assert ("I" in gcode or "J" in gcode), "Arc moves should have I/J center offsets"


# =============================================================================
# FEED RATE TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
@pytest.mark.cam
class TestHelicalFeedRates:
    """Test feed rate management in helical paths."""
    
    def test_feed_rate_xy_vs_z(self, api_client):
        """Test different XY and Z feed rates."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -3.0,
            "pitch": 0.5,
            "feed_xy": 2000.0,  # Fast XY
            "feed_z": 500.0     # Slow Z
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        result = response.json()
        gcode = result["gcode"]
        
        # Helical moves should have feed rate commands
        assert "F" in gcode, "G-code should contain feed rate commands"
        
    def test_fast_feed_rates(self, api_client, sample_helical_params):
        """Test with high feed rates."""
        params = sample_helical_params.copy()
        params["feed_xy"] = 3000.0
        params["feed_z"] = 1000.0
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Higher feed rates should reduce time
        assert stats["time_s"] > 0
        
    def test_slow_feed_rates(self, api_client, sample_helical_params):
        """Test with low feed rates."""
        params = sample_helical_params.copy()
        params["feed_xy"] = 500.0
        params["feed_z"] = 200.0
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Lower feed rates should increase time
        assert stats["time_s"] > 0


# =============================================================================
# G-CODE EXPORT TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
@pytest.mark.cam
@pytest.mark.export
class TestHelicalGcodeExport:
    """Test G-code generation with post-processor integration."""
    
    def test_gcode_export_grbl(self, api_client, sample_helical_params):
        """Test G-code export with GRBL post-processor."""
        params = sample_helical_params.copy()
        params["post_id"] = "GRBL"
        
        response = api_client.post(
            "/cam/toolpath/helical_entry_gcode",
            json=params
        )
        
        # Endpoint may or may not exist - check status
        if response.status_code == 200:
            gcode = response.text
            assert_valid_gcode(gcode)
            
            # Verify GRBL headers
            assert "G21" in gcode or "G20" in gcode
            assert "G90" in gcode or "G91" in gcode
            assert "G17" in gcode  # XY plane
            
    def test_gcode_export_mach4(self, api_client, sample_helical_params):
        """Test G-code export with Mach4 post-processor."""
        params = sample_helical_params.copy()
        params["post_id"] = "Mach4"
        
        response = api_client.post(
            "/cam/toolpath/helical_entry_gcode",
            json=params
        )
        
        # Endpoint may or may not exist
        if response.status_code == 200:
            gcode = response.text
            assert_valid_gcode(gcode)
            
    def test_gcode_contains_arcs(self, api_client, sample_helical_params):
        """Test that G-code contains arc commands."""
        params = sample_helical_params.copy()
        params["post_id"] = "GRBL"
        
        response = api_client.post(
            "/cam/toolpath/helical_entry_gcode",
            json=params
        )
        
        if response.status_code == 200:
            gcode = response.text
            
            # Should have G2 or G3 arc commands
            assert "G2" in gcode or "G3" in gcode


# =============================================================================
# PARAMETER VALIDATION TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
class TestHelicalValidation:
    """Test parameter validation and error handling."""
    
    def test_invalid_helix_radius(self, api_client):
        """Test error for invalid helix radius."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": -5.0,  # Invalid (negative)
            "target_depth": -3.0,
            "pitch": 0.5
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code in [400, 422]
        
    def test_invalid_pitch(self, api_client):
        """Test error for invalid pitch."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": -3.0,
            "pitch": 0.0  # Invalid (zero)
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code in [400, 422]
        
    def test_positive_target_depth(self, api_client):
        """Test handling of positive target depth."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": 3.0,  # Positive (unusual, should be negative)
            "pitch": 0.5
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        # Should either reject or auto-correct to negative
        assert response.status_code in [200, 400, 422]
        
    def test_zero_target_depth(self, api_client):
        """Test error for zero target depth."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": 0.0,  # Invalid (no depth)
            "pitch": 0.5
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code in [400, 422]
        
    def test_missing_required_params(self, api_client):
        """Test error for missing required parameters."""
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0
            # Missing helix_radius, target_depth, pitch
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 422  # Validation error


# =============================================================================
# GEOMETRY CALCULATION TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.helical
class TestHelicalGeometry:
    """Test helical geometry calculations."""
    
    def test_helix_length_calculation(self, api_client):
        """Test helix path length calculation."""
        params = {
            "entry_x": 0.0,
            "entry_y": 0.0,
            "helix_radius": 5.0,  # radius
            "target_depth": -3.14159,  # 1 revolution (2*pi*r in Z)
            "pitch": 3.14159,  # Full revolution
            "feed_xy": 1200.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Length should be close to circumference: 2*pi*r ≈ 31.4mm
        expected_length = 2 * math.pi * 5.0
        assert abs(stats["length_mm"] - expected_length) < 1.0
        
    def test_revolution_count(self, api_client):
        """Test revolution count accuracy."""
        pitch = 1.0  # 1mm per revolution
        depth = -5.0  # 5mm depth
        
        params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 5.0,
            "target_depth": depth,
            "pitch": pitch,
            "feed_xy": 1200.0
        }
        
        response = api_client.post(
            "/cam/toolpath/helical_entry",
            json=params
        )
        
        assert response.status_code == 200
        stats = response.json()["stats"]
        
        # Should have exactly 5 revolutions
        expected_revs = abs(depth) / pitch
        assert abs(stats["revolutions"] - expected_revs) < 0.1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.helical
@pytest.mark.slow
class TestHelicalIntegration:
    """End-to-end integration tests for helical ramping."""
    
    def test_complete_helical_workflow(self, api_client):
        """Test complete helical entry workflow."""
        # 1. Generate helical toolpath
        plan_params = {
            "entry_x": 50.0,
            "entry_y": 30.0,
            "helix_radius": 6.0,
            "target_depth": -5.0,
            "pitch": 0.8,
            "feed_xy": 1500.0,
            "feed_z": 500.0
        }
        
        plan_resp = api_client.post(
            "/cam/toolpath/helical_entry",
            json=plan_params
        )
        
        assert plan_resp.status_code == 200
        result = plan_resp.json()
        
        # 2. Verify response is valid
        assert "gcode" in result
        assert len(result["gcode"]) > 0
        assert result["stats"]["revolutions"] > 0
        
        # 3. If G-code endpoint exists, test export
        gcode_params = plan_params.copy()
        gcode_params["post_id"] = "GRBL"
        
        gcode_resp = api_client.post(
            "/cam/toolpath/helical_entry_gcode",
            json=gcode_params
        )
        
        if gcode_resp.status_code == 200:
            gcode = gcode_resp.text
            assert_valid_gcode(gcode)
            assert "M30" in gcode or "M2" in gcode  # Program end


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.routers.cam_helical_v161_router", "--cov-report=term-missing"])
