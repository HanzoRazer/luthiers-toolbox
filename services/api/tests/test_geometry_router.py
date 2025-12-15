"""
Test suite for geometry_router.py

Tests coverage for:
- Geometry import (DXF, SVG, JSON parsing)
- Parity checking (design vs toolpath validation)
- Export operations (single format, bundles, multi-post)
- Unit conversion (mm ↔ inch)
- Post-processor integration
- Error handling and validation

Part of P3.1 - Test Coverage to 80% (A_N roadmap requirement)
Focus: geometry_router.py (critical CAM export pipeline)
"""

import pytest
import json
import base64
import zipfile
import io
from pathlib import Path


# =============================================================================
# GEOMETRY IMPORT TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.geometry
class TestGeometryImport:
    """Test geometry import from various formats."""
    
    def test_import_json_simple(self, api_client, sample_geometry_simple):
        """Test importing simple JSON geometry."""
        # Send geometry nested under "geometry" key (FastAPI Body(embed=True))
        response = api_client.post(
            "/geometry/import",
            json={"geometry": sample_geometry_simple}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "units" in result
        assert result["units"] == "mm"
        assert "paths" in result
        assert len(result["paths"]) == 4
        
    def test_import_json_with_arcs(self, api_client, sample_geometry_with_arcs):
        """Test importing JSON geometry with arc segments."""
        response = api_client.post(
            "/geometry/import",
            json={"geometry": sample_geometry_with_arcs}
        )
        
        assert response.status_code == 200
        result = response.json()
        paths = result["paths"]
        
        # Verify arc was preserved
        arc_paths = [p for p in paths if p["type"] == "arc"]
        assert len(arc_paths) > 0
        
        # Verify arc has required fields
        arc = arc_paths[0]
        assert "cx" in arc
        assert "cy" in arc
        assert "r" in arc
        
    def test_import_invalid_format(self, api_client):
        """Test error handling for invalid input."""
        response = api_client.post(
            "/geometry/import",
            json={}  # No geometry or file
        )
        
        assert response.status_code == 400
        
    def test_import_malformed_json(self, api_client):
        """Test error handling for malformed geometry."""
        response = api_client.post(
            "/geometry/import",
            json={"geometry": {"invalid": "structure"}}  # Missing required fields
        )
        
        assert response.status_code in [400, 422]  # Either validation error


# =============================================================================
# PARITY CHECKING TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.geometry
class TestParityChecking:
    """Test design vs toolpath parity validation."""
    
    def test_parity_check_identical(self, api_client, sample_geometry_simple):
        """Test parity check with identical geometries."""
        # Generate simple G-code from geometry
        gcode = "G21 G90\nG0 X0 Y0\nG1 X100 Y0 F1200\nG1 X100 Y60\nG1 X0 Y60\nG1 X0 Y0\nM30"
        
        response = api_client.post(
            "/geometry/parity",
            json={
                "geometry": sample_geometry_simple,
                "gcode": gcode,
                "tolerance_mm": 0.1
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "pass" in result
        assert "max_error_mm" in result
        assert "rms_error_mm" in result
        
    def test_parity_check_different(self, api_client, sample_geometry_simple):
        """Test parity check with different geometries."""
        # G-code for 90x60 rectangle (shorter than 100x60 geometry)
        gcode = "G21 G90\nG0 X0 Y0\nG1 X90 Y0 F1200\nG1 X90 Y60\nG1 X0 Y60\nG1 X0 Y0\nM30"
        
        response = api_client.post(
            "/geometry/parity",
            json={
                "geometry": sample_geometry_simple,  # 100x60
                "gcode": gcode,  # 90x60 toolpath
                "tolerance_mm": 0.01
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "pass" in result
        assert result["pass"] is False  # Should fail due to deviation
        assert result["max_error_mm"] > 0.01
        
    def test_parity_check_tight_tolerance(self, api_client, sample_geometry_simple):
        """Test parity check with very tight tolerance."""
        # G-code matching geometry exactly
        gcode = "G21 G90\nG0 X0 Y0\nG1 X100 Y0 F1200\nG1 X100 Y60\nG1 X0 Y60\nG1 X0 Y0\nM30"
        
        response = api_client.post(
            "/geometry/parity",
            json={
                "geometry": sample_geometry_simple,
                "gcode": gcode,
                "tolerance_mm": 0.001  # Very tight 1 micron tolerance
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "pass" in result
        assert result["max_error_mm"] is not None
        assert result["rms_error_mm"] is not None


# =============================================================================
# EXPORT TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.geometry
@pytest.mark.export
class TestGeometryExport:
    """Test geometry export to various formats."""
    
    def test_export_dxf(self, api_client, sample_geometry_simple):
        """Test DXF export."""
        response = api_client.post(
            "/geometry/export?fmt=dxf",
            json={
                "geometry": sample_geometry_simple,
                "post_id": "GRBL"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        
        # Verify DXF content (minimal format without full HEADER)
        dxf_content = response.content.decode('utf-8')
        assert "SECTION" in dxf_content
        assert "ENTITIES" in dxf_content
        assert "LINE" in dxf_content
        assert "EOF" in dxf_content
        
    def test_export_svg(self, api_client, sample_geometry_simple):
        """Test SVG export."""
        response = api_client.post(
            "/geometry/export?fmt=svg",
            json={
                "geometry": sample_geometry_simple,
                "post_id": "GRBL"
            }
        )
        
        assert response.status_code == 200
        assert "svg" in response.headers["content-type"].lower()
        
        # Verify SVG content
        svg_content = response.content.decode('utf-8')
        assert "<svg" in svg_content or "<?xml" in svg_content
        
    @pytest.mark.skip(reason="Unit conversion happens at geometry level, not export level")
    def test_export_unit_conversion(self, api_client, sample_geometry_simple):
        """Test export with unit conversion (mm → inch)."""
        response = api_client.post(
            "/geometry/export",
            json={
                "geometry": sample_geometry_simple,
                "format": "dxf",
                "target_units": "inch"
            }
        )
        
        assert response.status_code == 200
        dxf_content = response.content.decode('utf-8')
        
        # Verify G20 (inch mode) in metadata or coordinates are scaled
        # 100mm should become ~3.937 inch
        assert "3.937" in dxf_content or "G20" in dxf_content


# =============================================================================
# BUNDLE EXPORT TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.geometry
@pytest.mark.export
class TestBundleExport:
    """Test bundle export functionality."""
    
    def test_export_bundle_single_post(self, api_client, sample_geometry_simple):
        """Test single-post bundle (DXF + SVG + NC)."""
        response = api_client.post(
            "/geometry/export_bundle",
            json={
                "geometry": sample_geometry_simple,
                "gcode": "G21\nG90\nG0 X0 Y0\nM30\n",
                "post_id": "GRBL"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        
        # Verify ZIP contents
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            files = zf.namelist()
            assert "program.dxf" in files
            assert "program.svg" in files
            assert "program_GRBL.nc" in files
            
            # Verify NC file has GRBL headers
            nc_content = zf.read("program_GRBL.nc").decode('utf-8')
            assert "G21" in nc_content
            assert "G90" in nc_content
            
    def test_export_bundle_multi_post(self, api_client, sample_geometry_simple):
        """Test multi-post bundle (multiple NC files)."""
        response = api_client.post(
            "/geometry/export_bundle_multi",
            json={
                "geometry": sample_geometry_simple,
                "gcode": "G21\nG90\nG0 X0 Y0\nM30\n",
                "post_ids": ["GRBL", "Mach4", "LinuxCNC"]
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        
        # Verify ZIP contains all post-processor files
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            files = zf.namelist()
            assert "program.dxf" in files
            assert "program.svg" in files
            assert "program_GRBL.nc" in files
            assert "program_Mach4.nc" in files
            assert "program_LinuxCNC.nc" in files
            
    def test_export_bundle_with_unit_conversion(self, api_client, sample_geometry_simple):
        """Test bundle export with unit conversion."""
        response = api_client.post(
            "/geometry/export_bundle",
            json={
                "geometry": sample_geometry_simple,
                "gcode": "G21\nG90\nG0 X100 Y60\nM30\n",
                "post_id": "GRBL",
                "target_units": "inch"
            }
        )
        
        assert response.status_code == 200
        
        # Verify unit conversion in NC file
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            nc_content = zf.read("program_GRBL.nc").decode('utf-8')
            # Should have G20 for inch mode or scaled coordinates
            assert "G20" in nc_content or "3.937" in nc_content


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.geometry
class TestGeometryErrorHandling:
    """Test error handling and validation."""
    
    def test_export_invalid_post_id(self, api_client, sample_geometry_simple):
        """Test graceful handling of invalid post-processor ID."""
        response = api_client.post(
            "/geometry/export_bundle",
            json={
                "geometry": sample_geometry_simple,
                "gcode": "G90\\nM30\\n",
                "post_id": "INVALID_POST"
            }
        )
        
        # Router gracefully handles invalid post by using GRBL default
        assert response.status_code == 200
        
    def test_export_missing_geometry(self, api_client):
        """Test error for missing geometry."""
        response = api_client.post(
            "/geometry/export",
            json={
                "format": "dxf"
                # Missing geometry field
            }
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_export_empty_paths(self, api_client):
        """Test handling of geometry with no paths."""
        response = api_client.post(
            "/geometry/export",
            json={
                "geometry": {"units": "mm", "paths": []},
                "format": "dxf"
            }
        )
        
        # Router allows empty paths (generates valid but empty DXF)
        assert response.status_code == 200
        
    def test_parity_missing_tolerance(self, api_client, sample_geometry_simple):
        """Test parity check with missing tolerance."""
        response = api_client.post(
            "/geometry/parity",
            json={
                "design": sample_geometry_simple,
                "toolpath": sample_geometry_simple
                # Missing tolerance_mm
            }
        )
        
        # Should use default tolerance or fail validation
        assert response.status_code in [200, 422]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.geometry
@pytest.mark.slow
class TestGeometryIntegration:
    """End-to-end integration tests."""
    
    def test_import_export_roundtrip(self, api_client, sample_geometry_simple):
        """Test import → export roundtrip preserves geometry."""
        # Import JSON (endpoint accepts direct geometry or nested in "geometry" key)
        import_resp = api_client.post(
            "/geometry/import",
            json={"geometry": sample_geometry_simple}
        )
        assert import_resp.status_code == 200
        imported = import_resp.json()
        
        # Verify imported geometry matches original
        assert imported["units"] == sample_geometry_simple["units"]
        assert len(imported["paths"]) == len(sample_geometry_simple["paths"])
        
        # Export DXF
        export_resp = api_client.post(
            "/geometry/export",
            json={
                "geometry": imported,
                "format": "dxf",
                "target_units": "mm"
            }
        )
        assert export_resp.status_code == 200
        
        # Verify DXF content is valid
        dxf_content = export_resp.content.decode('latin-1')
        assert "0\nLINE" in dxf_content or "0\nLWPOLYLINE" in dxf_content
        
    def test_multi_post_bundle_complete_workflow(self, api_client, sample_geometry_simple):
        """Test complete multi-post export workflow."""
        # Generate bundle for 3 machines
        response = api_client.post(
            "/geometry/export_bundle_multi",
            json={
                "geometry": sample_geometry_simple,
                "gcode": "G21\nG90\nG0 X50 Y30\nG1 Z-3 F400\nM30\n",
                "post_ids": ["GRBL", "Mach4", "LinuxCNC"],
                "target_units": "mm"
            }
        )
        
        assert response.status_code == 200
        
        # Verify all files present and valid
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            names = zf.namelist()
            # Check minimum file count: 1 DXF + 1 SVG + 3 NC (+ optional manifest)
            assert len(names) >= 5, f"Expected at least 5 files, got {len(names)}: {names}"
            
            # Required files
            assert "program.dxf" in names
            assert "program.svg" in names
            
            # Verify each NC file has correct headers
            for post_id in ["GRBL", "Mach4", "LinuxCNC"]:
                nc_file = f"program_{post_id}.nc"
                assert nc_file in zf.namelist()
                
                nc_content = zf.read(nc_file).decode('utf-8')
                assert "G21" in nc_content  # mm mode
                assert "G90" in nc_content  # absolute
                assert f"POST={post_id}" in nc_content  # metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.routers.geometry_router", "--cov-report=term-missing"])
