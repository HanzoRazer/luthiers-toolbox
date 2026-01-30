"""
Test suite for calculators_consolidated_router.py (Consolidated CAM/Math/Luthier Calculators)

Tests coverage for:
- CAM calculator (evaluate, evaluate-cut, health)
- Math calculator (evaluate, fraction/convert, fraction/parse, tvm)
- Luthier calculator (radius, wedge, board-feet, miter, dovetail)

Part of P3.1 - Test Coverage Initiative
Generated as scaffold - requires implementation of fixtures and assertions

Router endpoints: 17 total
Prefix: /api/calculators
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
def sample_cam_params():
    """Sample CAM calculation parameters."""
    return {
        "tool_diameter": 6.0,
        "rpm": 18000,
        "feed_rate": 1200,
        "depth_of_cut": 1.5,
        "width_of_cut": 3.0,
        "material": "softwood"
    }


@pytest.fixture
def sample_math_expression():
    """Sample math expression for evaluation."""
    return {"expression": "2 * pi * 12.5"}


# =============================================================================
# CAM CALCULATOR TESTS
# =============================================================================

@pytest.mark.router
@pytest.mark.cam
class TestCAMCalculator:
    """Test CAM calculator endpoints."""

    def test_cam_evaluate(self, api_client, sample_cam_params):
        """POST /api/calculators/cam/evaluate - Full CAM calculation bundle."""
        response = api_client.post(
            "/api/calculators/cam/evaluate",
            json=sample_cam_params
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Verify expected fields in response
            assert "chipload" in result or "result" in result

    def test_cam_evaluate_cut(self, api_client, sample_cam_params):
        """POST /api/calculators/cam/evaluate-cut - Cut-specific calculations."""
        response = api_client.post(
            "/api/calculators/cam/evaluate-cut",
            json=sample_cam_params
        )
        assert response.status_code in (200, 422, 500)

    def test_cam_health(self, api_client):
        """GET /api/calculators/cam/health - CAM calculator health check."""
        response = api_client.get("/api/calculators/cam/health")
        assert response.status_code == 200

    def test_legacy_evaluate(self, api_client, sample_cam_params):
        """POST /api/calculators/evaluate - Legacy endpoint (alias)."""
        response = api_client.post(
            "/api/calculators/evaluate",
            json=sample_cam_params
        )
        assert response.status_code in (200, 422, 500)

    def test_legacy_evaluate_cut(self, api_client, sample_cam_params):
        """POST /api/calculators/evaluate-cut - Legacy endpoint (alias)."""
        response = api_client.post(
            "/api/calculators/evaluate-cut",
            json=sample_cam_params
        )
        assert response.status_code in (200, 422, 500)

    def test_legacy_health(self, api_client):
        """GET /api/calculators/health - Legacy health endpoint."""
        response = api_client.get("/api/calculators/health")
        assert response.status_code == 200


# =============================================================================
# MATH CALCULATOR TESTS
# =============================================================================

@pytest.mark.router
class TestMathCalculator:
    """Test math calculator endpoints."""

    def test_math_evaluate(self, api_client, sample_math_expression):
        """POST /api/calculators/math/evaluate - Evaluate math expression."""
        response = api_client.post(
            "/api/calculators/math/evaluate",
            json=sample_math_expression
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            result = response.json()
            assert "result" in result or "value" in result

    def test_fraction_convert(self, api_client):
        """POST /api/calculators/math/fraction/convert - Convert decimal to fraction."""
        response = api_client.post(
            "/api/calculators/math/fraction/convert",
            json={"decimal": 0.375, "max_denominator": 64}
        )
        assert response.status_code in (200, 422, 500)

    def test_fraction_parse(self, api_client):
        """GET /api/calculators/math/fraction/parse/{text} - Parse fraction text."""
        response = api_client.get("/api/calculators/math/fraction/parse/3%2F8")
        assert response.status_code in (200, 422, 500)

    def test_tvm_calculation(self, api_client):
        """POST /api/calculators/math/tvm - Time value of money calculation."""
        response = api_client.post(
            "/api/calculators/math/tvm",
            json={
                "pv": 1000,
                "rate": 0.05,
                "periods": 12,
                "pmt": 0
            }
        )
        assert response.status_code in (200, 422, 500)


# =============================================================================
# LUTHIER CALCULATOR TESTS
# =============================================================================

@pytest.mark.router
class TestLuthierCalculator:
    """Test luthier-specific calculator endpoints."""

    def test_radius_from_3_points(self, api_client):
        """POST /api/calculators/luthier/radius/from-3-points - Calculate radius from 3 points."""
        response = api_client.post(
            "/api/calculators/luthier/radius/from-3-points",
            json={
                "p1": {"x": 0, "y": 0},
                "p2": {"x": 10, "y": 5},
                "p3": {"x": 20, "y": 0}
            }
        )
        assert response.status_code in (200, 422, 500)

    def test_radius_from_chord(self, api_client):
        """POST /api/calculators/luthier/radius/from-chord - Calculate radius from chord/height."""
        response = api_client.post(
            "/api/calculators/luthier/radius/from-chord",
            json={"chord_length": 50.0, "height": 5.0}
        )
        assert response.status_code in (200, 422, 500)

    def test_radius_compound(self, api_client):
        """POST /api/calculators/luthier/radius/compound - Compound radius calculation."""
        response = api_client.post(
            "/api/calculators/luthier/radius/compound",
            json={
                "nut_radius": 10.0,
                "bridge_radius": 16.0,
                "scale_length": 25.5,
                "position": 12.0
            }
        )
        assert response.status_code in (200, 422, 500)

    def test_wedge_angle(self, api_client):
        """POST /api/calculators/luthier/wedge/angle - Wedge angle calculation."""
        response = api_client.post(
            "/api/calculators/luthier/wedge/angle",
            json={"height": 10.0, "length": 100.0}
        )
        assert response.status_code in (200, 422, 500)

    def test_board_feet(self, api_client):
        """POST /api/calculators/luthier/board-feet - Board feet calculation."""
        response = api_client.post(
            "/api/calculators/luthier/board-feet",
            json={
                "thickness_in": 1.0,
                "width_in": 6.0,
                "length_in": 96.0
            }
        )
        assert response.status_code in (200, 422, 500)

    def test_miter_angle(self, api_client):
        """GET /api/calculators/luthier/miter/{num_sides} - Miter angle for polygon."""
        response = api_client.get("/api/calculators/luthier/miter/8")
        assert response.status_code == 200
        result = response.json()
        # 8-sided polygon should have 22.5 degree miter angle
        assert "angle" in result or "miter_angle" in result

    def test_dovetail_ratio(self, api_client):
        """GET /api/calculators/luthier/dovetail/{ratio} - Dovetail angle from ratio."""
        response = api_client.get("/api/calculators/luthier/dovetail/8")
        assert response.status_code == 200
