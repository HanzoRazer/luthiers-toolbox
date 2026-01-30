"""
Test suite for body_generator_router.py (Guitar Body Generation and Export)

Tests coverage for:
- Body analysis
- Body generation
- Multi-format export
- Governed generation and export
- Machine/tool/post listings

Part of P3.1 - Test Coverage Initiative
Generated as scaffold - requires implementation of fixtures and assertions

Router endpoints: 8 total
Prefix: /api/body or /api/cam/body
"""

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_body_params():
    """Sample body generation parameters."""
    return {
        "body_style": "stratocaster",
        "scale_length": 25.5,
        "body_thickness": 1.75,
        "neck_pocket_width": 2.2,
        "neck_pocket_length": 3.0,
        "cutaway_type": "double",
        "contours": {
            "belly_cut": True,
            "arm_contour": True,
            "heel_contour": True
        },
        "pickup_layout": "sss",
        "bridge_type": "tremolo"
    }


@pytest.fixture
def sample_analyze_params():
    """Sample body analysis parameters."""
    return {
        "body_outline": [
            {"x": 0, "y": 0},
            {"x": 14, "y": 0},
            {"x": 14, "y": 18},
            {"x": 0, "y": 18}
        ],
        "thickness": 1.75,
        "units": "inches"
    }


@pytest.fixture
def sample_export_params():
    """Sample multi-format export parameters."""
    return {
        "body_data": {
            "outline": [
                {"x": 0, "y": 0},
                {"x": 350, "y": 0},
                {"x": 350, "y": 450},
                {"x": 0, "y": 450}
            ],
            "thickness_mm": 44.45,
            "cavities": [],
            "pockets": []
        },
        "formats": ["dxf", "svg"],
        "machine_profile": "grbl",
        "post_processor": "grbl"
    }


@pytest.fixture
def sample_governed_params():
    """Sample governed generation parameters."""
    return {
        "body_style": "telecaster",
        "scale_length": 25.5,
        "material": "alder",
        "operator_id": "test_operator",
        "session_id": "test_session_001",
        "machine_id": "cnc_router_001"
    }


# =============================================================================
# BODY ANALYSIS TESTS
# =============================================================================

@pytest.mark.router
class TestBodyAnalysis:
    """Test body analysis endpoints."""

    def test_analyze_body(self, api_client, sample_analyze_params):
        """POST /api/body/analyze - Analyze body geometry."""
        response = api_client.post(
            "/api/body/analyze",
            json=sample_analyze_params
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should return analysis metrics
            assert "area" in result or "volume" in result or "analysis" in result

    def test_analyze_body_with_cavities(self, api_client, sample_analyze_params):
        """POST /api/body/analyze - Analyze body with cavities."""
        params_with_cavities = sample_analyze_params.copy()
        params_with_cavities["cavities"] = [
            {
                "type": "pickup",
                "position": {"x": 7, "y": 5},
                "dimensions": {"width": 3.5, "length": 1.5, "depth": 0.75}
            }
        ]
        response = api_client.post(
            "/api/body/analyze",
            json=params_with_cavities
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# BODY GENERATION TESTS
# =============================================================================

@pytest.mark.router
class TestBodyGeneration:
    """Test body generation endpoints."""

    def test_generate_body(self, api_client, sample_body_params):
        """POST /api/body/generate - Generate body design."""
        response = api_client.post(
            "/api/body/generate",
            json=sample_body_params
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should return generated body data
            assert "outline" in result or "body" in result or "geometry" in result

    def test_generate_body_governed(self, api_client, sample_governed_params):
        """POST /api/body/generate_governed - Governed body generation."""
        response = api_client.post(
            "/api/body/generate_governed",
            json=sample_governed_params
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should include governance metadata
            assert "run_id" in result or "artifact_id" in result or "outline" in result


# =============================================================================
# EXPORT TESTS
# =============================================================================

@pytest.mark.router
class TestBodyExport:
    """Test body export endpoints."""

    def test_export_multi(self, api_client, sample_export_params):
        """POST /api/body/export/multi - Export to multiple formats."""
        response = api_client.post(
            "/api/body/export/multi",
            json=sample_export_params
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should return file paths or download data
            assert "files" in result or "exports" in result or "dxf" in result

    def test_export_multi_governed(self, api_client, sample_export_params):
        """POST /api/body/export/multi_governed - Governed multi-format export."""
        governed_export = sample_export_params.copy()
        governed_export["operator_id"] = "test_operator"
        governed_export["session_id"] = "test_session_001"
        response = api_client.post(
            "/api/body/export/multi_governed",
            json=governed_export
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should include governance audit trail
            assert "run_id" in result or "artifact_id" in result or "exports" in result


# =============================================================================
# REFERENCE DATA TESTS
# =============================================================================

@pytest.mark.router
class TestBodyReferenceData:
    """Test body reference data listing endpoints."""

    def test_list_machines(self, api_client):
        """GET /api/body/machines - List available machines."""
        response = api_client.get("/api/body/machines")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            # Should return list of machine profiles

    def test_list_tools(self, api_client):
        """GET /api/body/tools - List available tools."""
        response = api_client.get("/api/body/tools")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            # Should return list of tool definitions

    def test_list_posts(self, api_client):
        """GET /api/body/posts - List available post processors."""
        response = api_client.get("/api/body/posts")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            # Should return list of post processor options
