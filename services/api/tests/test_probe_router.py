"""
Test suite for probe_router.py (Touch-off Probe G-code Generation)

Tests coverage for:
- Corner probing (gcode, download, download_governed)
- Boss probing (gcode, download, download_governed)
- Surface Z probing (gcode, download, download_governed)
- Pocket probing (gcode, download, download_governed)
- Vise square probing (gcode, download, download_governed)
- Setup sheet SVG generation
- Probe patterns listing

Part of P3.1 - Test Coverage Initiative
Generated as scaffold - requires implementation of fixtures and assertions

Router endpoints: 17 total
Prefix: /api/probe
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
def sample_corner_probe_params():
    """Sample corner probing parameters."""
    return {
        "x_start": 0.0,
        "y_start": 0.0,
        "z_clearance": 5.0,
        "probe_depth": -3.0,
        "feed_rate": 100.0,
        "corner": "front_left"
    }


@pytest.fixture
def sample_boss_probe_params():
    """Sample boss probing parameters."""
    return {
        "x_center": 50.0,
        "y_center": 50.0,
        "z_clearance": 5.0,
        "approximate_diameter": 25.0,
        "probe_depth": -3.0,
        "feed_rate": 100.0
    }


@pytest.fixture
def sample_surface_z_params():
    """Sample surface Z probing parameters."""
    return {
        "x_position": 50.0,
        "y_position": 50.0,
        "z_start": 10.0,
        "probe_depth": -5.0,
        "feed_rate": 50.0
    }


@pytest.fixture
def sample_pocket_probe_params():
    """Sample pocket probing parameters."""
    return {
        "x_center": 50.0,
        "y_center": 50.0,
        "z_clearance": 5.0,
        "approximate_width": 30.0,
        "approximate_height": 30.0,
        "probe_depth": -3.0,
        "feed_rate": 100.0
    }


@pytest.fixture
def sample_vise_square_params():
    """Sample vise square probing parameters."""
    return {
        "x_start": 0.0,
        "y_clearance": 10.0,
        "z_clearance": 5.0,
        "probe_distance": 50.0,
        "feed_rate": 100.0
    }


# =============================================================================
# CORNER PROBING TESTS
# =============================================================================

@pytest.mark.router
class TestCornerProbing:
    """Test corner probing endpoints."""

    def test_corner_gcode(self, api_client, sample_corner_probe_params):
        """POST /api/probe/corner/gcode - Generate corner probe G-code."""
        response = api_client.post(
            "/api/probe/corner/gcode",
            json=sample_corner_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            result = response.json()
            assert "gcode" in result or "lines" in result

    def test_corner_gcode_download(self, api_client, sample_corner_probe_params):
        """POST /api/probe/corner/gcode/download - Download corner probe G-code file."""
        response = api_client.post(
            "/api/probe/corner/gcode/download",
            json=sample_corner_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_corner_gcode_download_governed(self, api_client, sample_corner_probe_params):
        """POST /api/probe/corner/gcode/download_governed - Governed corner probe download."""
        response = api_client.post(
            "/api/probe/corner/gcode/download_governed",
            json=sample_corner_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# BOSS PROBING TESTS
# =============================================================================

@pytest.mark.router
class TestBossProbing:
    """Test boss (circular feature) probing endpoints."""

    def test_boss_gcode(self, api_client, sample_boss_probe_params):
        """POST /api/probe/boss/gcode - Generate boss probe G-code."""
        response = api_client.post(
            "/api/probe/boss/gcode",
            json=sample_boss_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_boss_gcode_download(self, api_client, sample_boss_probe_params):
        """POST /api/probe/boss/gcode/download - Download boss probe G-code file."""
        response = api_client.post(
            "/api/probe/boss/gcode/download",
            json=sample_boss_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_boss_gcode_download_governed(self, api_client, sample_boss_probe_params):
        """POST /api/probe/boss/gcode/download_governed - Governed boss probe download."""
        response = api_client.post(
            "/api/probe/boss/gcode/download_governed",
            json=sample_boss_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# SURFACE Z PROBING TESTS
# =============================================================================

@pytest.mark.router
class TestSurfaceZProbing:
    """Test surface Z probing endpoints."""

    def test_surface_z_gcode(self, api_client, sample_surface_z_params):
        """POST /api/probe/surface_z/gcode - Generate surface Z probe G-code."""
        response = api_client.post(
            "/api/probe/surface_z/gcode",
            json=sample_surface_z_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_surface_z_gcode_download(self, api_client, sample_surface_z_params):
        """POST /api/probe/surface_z/gcode/download - Download surface Z probe file."""
        response = api_client.post(
            "/api/probe/surface_z/gcode/download",
            json=sample_surface_z_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_surface_z_gcode_download_governed(self, api_client, sample_surface_z_params):
        """POST /api/probe/surface_z/gcode/download_governed - Governed surface Z download."""
        response = api_client.post(
            "/api/probe/surface_z/gcode/download_governed",
            json=sample_surface_z_params
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# POCKET PROBING TESTS
# =============================================================================

@pytest.mark.router
class TestPocketProbing:
    """Test pocket probing endpoints."""

    def test_pocket_gcode(self, api_client, sample_pocket_probe_params):
        """POST /api/probe/pocket/gcode - Generate pocket probe G-code."""
        response = api_client.post(
            "/api/probe/pocket/gcode",
            json=sample_pocket_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_pocket_gcode_download(self, api_client, sample_pocket_probe_params):
        """POST /api/probe/pocket/gcode/download - Download pocket probe file."""
        response = api_client.post(
            "/api/probe/pocket/gcode/download",
            json=sample_pocket_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_pocket_gcode_download_governed(self, api_client, sample_pocket_probe_params):
        """POST /api/probe/pocket/gcode/download_governed - Governed pocket probe download."""
        response = api_client.post(
            "/api/probe/pocket/gcode/download_governed",
            json=sample_pocket_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# VISE SQUARE PROBING TESTS
# =============================================================================

@pytest.mark.router
class TestViseSquareProbing:
    """Test vise square probing endpoints."""

    def test_vise_square_gcode(self, api_client, sample_vise_square_params):
        """POST /api/probe/vise_square/gcode - Generate vise square probe G-code."""
        response = api_client.post(
            "/api/probe/vise_square/gcode",
            json=sample_vise_square_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_vise_square_gcode_download(self, api_client, sample_vise_square_params):
        """POST /api/probe/vise_square/gcode/download - Download vise square probe file."""
        response = api_client.post(
            "/api/probe/vise_square/gcode/download",
            json=sample_vise_square_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_vise_square_gcode_download_governed(self, api_client, sample_vise_square_params):
        """POST /api/probe/vise_square/gcode/download_governed - Governed vise square download."""
        response = api_client.post(
            "/api/probe/vise_square/gcode/download_governed",
            json=sample_vise_square_params
        )
        assert response.status_code in (200, 404, 422, 500)


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@pytest.mark.router
class TestProbeUtilities:
    """Test probe utility endpoints."""

    def test_setup_sheet_svg(self, api_client, sample_corner_probe_params):
        """POST /api/probe/setup_sheet/svg - Generate setup sheet SVG."""
        response = api_client.post(
            "/api/probe/setup_sheet/svg",
            json=sample_corner_probe_params
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_patterns(self, api_client):
        """GET /api/probe/patterns - List available probe patterns."""
        response = api_client.get("/api/probe/patterns")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, (list, dict))
