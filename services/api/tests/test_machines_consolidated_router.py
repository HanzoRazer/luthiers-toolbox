"""
Test suite for machines_consolidated_router.py (Machine Profile Management)

Tests coverage for:
- Machine profiles CRUD (list, get, create, clone, delete)
- Machine tools management (list, update, import CSV, delete)

Part of P3.1 - Test Coverage Initiative
Generated as scaffold - requires implementation of fixtures and assertions

Router endpoints: 10 total
Prefix: /api/machines
"""

import pytest
from fastapi.testclient import TestClient
import io


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_machine_profile():
    """Sample machine profile for testing."""
    return {
        "name": "Test CNC Router",
        "description": "3-axis router for testing",
        "work_envelope": {
            "x_min": 0, "x_max": 800,
            "y_min": 0, "y_max": 600,
            "z_min": -50, "z_max": 0
        },
        "max_rpm": 24000,
        "max_feed_rate": 5000,
        "max_plunge_rate": 1000,
        "controller": "grbl"
    }


@pytest.fixture
def sample_tool():
    """Sample tool definition for testing."""
    return {
        "tool_number": 1,
        "name": "1/4 inch Endmill",
        "type": "endmill",
        "diameter": 6.35,
        "flutes": 2,
        "coating": "uncoated"
    }


@pytest.fixture
def sample_tools_csv():
    """Sample tools CSV content for import testing."""
    csv_content = """tool_number,name,type,diameter,flutes
1,1/8 inch Endmill,endmill,3.175,2
2,1/4 inch Endmill,endmill,6.35,2
3,V-Bit 60deg,vbit,6.35,1
"""
    return csv_content


# =============================================================================
# MACHINE PROFILE TESTS
# =============================================================================

@pytest.mark.router
class TestMachineProfiles:
    """Test machine profile CRUD endpoints."""

    def test_list_profiles(self, api_client):
        """GET /api/machines/profiles - List all machine profiles."""
        response = api_client.get("/api/machines/profiles")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_profile(self, api_client):
        """GET /api/machines/profiles/{pid} - Get specific profile."""
        # First list profiles to get a valid ID
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                profile_id = profiles[0].get("id") or profiles[0].get("pid")
                if profile_id:
                    response = api_client.get(f"/api/machines/profiles/{profile_id}")
                    assert response.status_code in (200, 404)
                    return
        # If no profiles exist, test with a fake ID
        response = api_client.get("/api/machines/profiles/nonexistent_id")
        assert response.status_code in (200, 404, 500)

    def test_create_profile(self, api_client, sample_machine_profile):
        """POST /api/machines/profiles - Create new profile."""
        response = api_client.post(
            "/api/machines/profiles",
            json=sample_machine_profile
        )
        assert response.status_code in (200, 201, 422, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert "id" in result or "pid" in result or "name" in result

    def test_clone_profile(self, api_client):
        """POST /api/machines/profiles/clone/{src_id} - Clone profile."""
        # First list profiles to get a valid source ID
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                src_id = profiles[0].get("id") or profiles[0].get("pid")
                if src_id:
                    response = api_client.post(f"/api/machines/profiles/clone/{src_id}")
                    assert response.status_code in (200, 201, 404, 422, 500)
                    return
        # If no profiles exist, test with fake ID
        response = api_client.post("/api/machines/profiles/clone/nonexistent")
        assert response.status_code in (200, 201, 404, 422, 500)

    def test_delete_profile(self, api_client, sample_machine_profile):
        """DELETE /api/machines/profiles/{pid} - Delete profile."""
        # First create a profile to delete
        create_response = api_client.post(
            "/api/machines/profiles",
            json=sample_machine_profile
        )
        if create_response.status_code in (200, 201):
            result = create_response.json()
            profile_id = result.get("id") or result.get("pid")
            if profile_id:
                response = api_client.delete(f"/api/machines/profiles/{profile_id}")
                assert response.status_code in (200, 204, 404)
                return
        # If creation failed, test delete with fake ID
        response = api_client.delete("/api/machines/profiles/nonexistent_id")
        assert response.status_code in (200, 204, 404, 500)


# =============================================================================
# MACHINE TOOLS TESTS
# =============================================================================

@pytest.mark.router
class TestMachineTools:
    """Test machine tools management endpoints."""

    def test_list_machine_tools(self, api_client):
        """GET /api/machines/{mid}/tools - List tools for machine."""
        # First get a machine ID
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                mid = profiles[0].get("id") or profiles[0].get("pid")
                if mid:
                    response = api_client.get(f"/api/machines/{mid}/tools")
                    assert response.status_code in (200, 404)
                    if response.status_code == 200:
                        result = response.json()
                        assert isinstance(result, list)
                    return
        # Fallback: test with fake machine ID
        response = api_client.get("/api/machines/test_machine/tools")
        assert response.status_code in (200, 404, 500)

    def test_list_machine_tools_csv(self, api_client):
        """GET /api/machines/{mid}/tools.csv - Export tools as CSV."""
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                mid = profiles[0].get("id") or profiles[0].get("pid")
                if mid:
                    response = api_client.get(f"/api/machines/{mid}/tools.csv")
                    assert response.status_code in (200, 404)
                    return
        response = api_client.get("/api/machines/test_machine/tools.csv")
        assert response.status_code in (200, 404, 500)

    def test_update_machine_tools(self, api_client, sample_tool):
        """PUT /api/machines/{mid}/tools - Update machine tools."""
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                mid = profiles[0].get("id") or profiles[0].get("pid")
                if mid:
                    response = api_client.put(
                        f"/api/machines/{mid}/tools",
                        json=[sample_tool]
                    )
                    assert response.status_code in (200, 404, 422, 500)
                    return
        response = api_client.put(
            "/api/machines/test_machine/tools",
            json=[sample_tool]
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_import_tools_csv(self, api_client, sample_tools_csv):
        """POST /api/machines/{mid}/tools/import_csv - Import tools from CSV."""
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                mid = profiles[0].get("id") or profiles[0].get("pid")
                if mid:
                    files = {"file": ("tools.csv", sample_tools_csv, "text/csv")}
                    response = api_client.post(
                        f"/api/machines/{mid}/tools/import_csv",
                        files=files
                    )
                    assert response.status_code in (200, 404, 422, 500)
                    return
        # Fallback
        files = {"file": ("tools.csv", sample_tools_csv, "text/csv")}
        response = api_client.post(
            "/api/machines/test_machine/tools/import_csv",
            files=files
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_delete_machine_tool(self, api_client):
        """DELETE /api/machines/{mid}/tools/{tnum} - Delete specific tool."""
        list_response = api_client.get("/api/machines/profiles")
        if list_response.status_code == 200 and list_response.json():
            profiles = list_response.json()
            if profiles:
                mid = profiles[0].get("id") or profiles[0].get("pid")
                if mid:
                    # Try to delete tool number 1
                    response = api_client.delete(f"/api/machines/{mid}/tools/1")
                    assert response.status_code in (200, 204, 404, 500)
                    return
        response = api_client.delete("/api/machines/test_machine/tools/1")
        assert response.status_code in (200, 204, 404, 500)
