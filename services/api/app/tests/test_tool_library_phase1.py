# services/api/app/tests/test_tool_library_phase1.py

"""
Phase 1 Tool Library Migration Tests

Tests for:
- Tool library list methods
- Material library list methods
- Validator functions
- Tooling router endpoints (tools, materials, validate)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.tool_library import (
    load_tool_library,
    get_tool_profile,
    get_material_profile,
    reset_cache,
)
from app.data.validate_tool_library import (
    validate_tool_profile,
    validate_material_profile,
    validate_library,
)


client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Tool Library Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestToolLibraryListMethods:
    """Test new list methods added in Phase 1."""

    def setup_method(self):
        """Reset cache before each test."""
        reset_cache()

    def test_list_tool_ids_returns_list(self):
        """list_tool_ids should return a list of strings."""
        lib = load_tool_library()
        tool_ids = lib.list_tool_ids()
        
        assert isinstance(tool_ids, list)
        assert len(tool_ids) > 0
        assert all(isinstance(tid, str) for tid in tool_ids)

    def test_list_material_ids_returns_list(self):
        """list_material_ids should return a list of strings."""
        lib = load_tool_library()
        mat_ids = lib.list_material_ids()
        
        assert isinstance(mat_ids, list)
        assert len(mat_ids) > 0
        assert all(isinstance(mid, str) for mid in mat_ids)

    def test_get_tool_alias_works(self):
        """get_tool should be alias for get_tool_profile."""
        lib = load_tool_library()
        tool_ids = lib.list_tool_ids()
        
        if tool_ids:
            tool_id = tool_ids[0]
            tool1 = lib.get_tool(tool_id)
            tool2 = lib.get_tool_profile(tool_id)
            
            assert tool1 is not None
            assert tool2 is not None
            assert tool1.tool_id == tool2.tool_id

    def test_get_material_alias_works(self):
        """get_material should be alias for get_material_profile."""
        lib = load_tool_library()
        mat_ids = lib.list_material_ids()
        
        if mat_ids:
            mat_id = mat_ids[0]
            mat1 = lib.get_material(mat_id)
            mat2 = lib.get_material_profile(mat_id)
            
            assert mat1 is not None
            assert mat2 is not None
            assert mat1.material_id == mat2.material_id


# ─────────────────────────────────────────────────────────────────────────────
# Validator Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestToolValidator:
    """Test tool profile validation."""

    def test_valid_tool_passes(self):
        """A valid tool should pass validation."""
        tool = get_tool_profile("flat_6.0")
        if tool:
            errors = validate_tool_profile(tool)
            # Allow some warnings but no critical errors
            assert all("diameter_mm must be" not in e for e in errors)

    def test_invalid_diameter_fails(self):
        """Tool with zero diameter should fail."""
        from app.data.tool_library import ToolProfile
        
        bad_tool = ToolProfile(
            tool_id="bad_tool",
            name="Bad Tool",
            flutes=2,
            chipload_min_mm=0.01,
            chipload_max_mm=0.03,
            diameter_mm=0,  # Invalid
            tool_type="flat",
        )
        
        errors = validate_tool_profile(bad_tool)
        assert len(errors) > 0
        assert any("diameter_mm" in e for e in errors)

    def test_chipload_range_inverted_fails(self):
        """Tool with min > max chipload should fail."""
        from app.data.tool_library import ToolProfile
        
        bad_tool = ToolProfile(
            tool_id="bad_chip",
            name="Bad Chipload",
            flutes=2,
            chipload_min_mm=0.05,  # min > max
            chipload_max_mm=0.01,
            diameter_mm=6.0,
            tool_type="flat",
        )
        
        errors = validate_tool_profile(bad_tool)
        assert len(errors) > 0
        assert any("chipload" in e.lower() for e in errors)


class TestMaterialValidator:
    """Test material profile validation."""

    def test_valid_material_passes(self):
        """A valid material should pass validation."""
        mat = get_material_profile("Ebony")
        if mat:
            errors = validate_material_profile(mat)
            assert len(errors) == 0

    def test_invalid_heat_sensitivity_fails(self):
        """Material with invalid heat_sensitivity should fail."""
        from app.data.tool_library import MaterialProfile
        
        bad_mat = MaterialProfile(
            material_id="bad_mat",
            name="Bad Material",
            heat_sensitivity="extreme",  # Invalid value
            hardness="medium",
            density_kg_m3=500,
        )
        
        errors = validate_material_profile(bad_mat)
        assert len(errors) > 0
        assert any("heat_sensitivity" in e for e in errors)


class TestLibraryValidator:
    """Test full library validation."""

    def setup_method(self):
        reset_cache()

    def test_validate_library_returns_list(self):
        """validate_library should return list of errors."""
        errors = validate_library()
        assert isinstance(errors, list)

    def test_current_library_validates(self):
        """Current tool_library.json should pass validation."""
        errors = validate_library()
        # May have some warnings, but should not have critical failures
        # that would break the system
        critical = [e for e in errors if "must be" in e]
        assert len(critical) == 0, f"Critical validation errors: {critical}"


# ─────────────────────────────────────────────────────────────────────────────
# Router Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestToolingRouterTools:
    """Test /tooling/library/tools endpoints."""

    def test_list_tools_returns_list(self):
        """GET /tooling/library/tools should return list of tools."""
        response = client.get("/tooling/library/tools")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_tools_has_required_fields(self):
        """Each tool in list should have required fields."""
        response = client.get("/tooling/library/tools")
        data = response.json()
        
        for tool in data:
            assert "tool_id" in tool
            assert "name" in tool
            assert "type" in tool
            assert "diameter_mm" in tool
            assert "flutes" in tool

    def test_get_tool_by_id(self):
        """GET /tooling/library/tools/{tool_id} should return tool details."""
        # First get a valid tool ID
        list_response = client.get("/tooling/library/tools")
        tools = list_response.json()
        
        if tools:
            tool_id = tools[0]["tool_id"]
            response = client.get(f"/tooling/library/tools/{tool_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["tool_id"] == tool_id
            assert "chipload_mm" in data

    def test_get_unknown_tool_returns_error_field(self):
        """GET /tooling/library/tools/unknown should return error field."""
        response = client.get("/tooling/library/tools/nonexistent_tool_xyz")
        assert response.status_code == 200  # Fail-safe design
        
        data = response.json()
        assert "error" in data


class TestToolingRouterMaterials:
    """Test /tooling/library/materials endpoints."""

    def test_list_materials_returns_list(self):
        """GET /tooling/library/materials should return list of materials."""
        response = client.get("/tooling/library/materials")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_materials_has_required_fields(self):
        """Each material in list should have required fields."""
        response = client.get("/tooling/library/materials")
        data = response.json()
        
        for mat in data:
            assert "material_id" in mat
            assert "name" in mat
            assert "heat_sensitivity" in mat
            assert "hardness" in mat

    def test_get_material_by_id(self):
        """GET /tooling/library/materials/{material_id} should return material details."""
        response = client.get("/tooling/library/materials/Ebony")
        
        assert response.status_code == 200
        data = response.json()
        assert data["material_id"] == "Ebony"
        assert "density_kg_m3" in data

    def test_get_unknown_material_returns_error_field(self):
        """GET /tooling/library/materials/unknown should return error field."""
        response = client.get("/tooling/library/materials/UnknownMaterial123")
        assert response.status_code == 200  # Fail-safe design
        
        data = response.json()
        assert "error" in data


class TestToolingRouterValidate:
    """Test /tooling/library/validate endpoint."""

    def test_validate_returns_status(self):
        """GET /tooling/library/validate should return validation status."""
        response = client.get("/tooling/library/validate")
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert "tool_count" in data
        assert "material_count" in data
        assert "errors" in data

    def test_validate_counts_match_lists(self):
        """Validate counts should match list endpoint counts."""
        validate_response = client.get("/tooling/library/validate")
        tools_response = client.get("/tooling/library/tools")
        materials_response = client.get("/tooling/library/materials")
        
        validate_data = validate_response.json()
        
        assert validate_data["tool_count"] == len(tools_response.json())
        assert validate_data["material_count"] == len(materials_response.json())
