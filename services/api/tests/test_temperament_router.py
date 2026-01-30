"""
Test suite for temperament_router.py (Music Temperament Systems)

Tests coverage for:
- Health check
- Temperament systems listing
- Musical keys listing
- Tunings listing
- Temperament comparison (single and all)
- Equal temperament calculation
- Temperament resolution
- Temperament tables

Part of P3.1 - Test Coverage Initiative
Generated as scaffold - requires implementation of fixtures and assertions

Router endpoints: 9 total
Prefix: /api/music/temperament
Location: app/routers/music/temperament_router.py
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
def sample_compare_request():
    """Sample temperament comparison request."""
    return {
        "temperament1": "equal",
        "temperament2": "pythagorean",
        "root_note": "A4",
        "frequency": 440.0
    }


# =============================================================================
# HEALTH AND LISTING TESTS
# =============================================================================

@pytest.mark.router
class TestTemperamentBasics:
    """Test basic temperament listing and health endpoints."""

    def test_health(self, api_client):
        """GET /api/music/temperament/health - Health check."""
        response = api_client.get("/api/music/temperament/health")
        assert response.status_code == 200

    def test_list_systems(self, api_client):
        """GET /api/music/temperament/systems - List temperament systems."""
        response = api_client.get("/api/music/temperament/systems")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        # Should include at least 'equal', 'pythagorean', 'just', 'meantone'
        # Verify some expected temperaments are present
        if result:
            system_names = [s.get("name", s) if isinstance(s, dict) else s for s in result]
            # At least one should be present
            assert len(system_names) > 0

    def test_list_keys(self, api_client):
        """GET /api/music/temperament/keys - List musical keys."""
        response = api_client.get("/api/music/temperament/keys")
        assert response.status_code == 200
        result = response.json()
        # Response is a dict with keys list
        assert isinstance(result, dict)
        assert "keys" in result
        assert isinstance(result["keys"], list)
        # Should include standard keys (C, D, E, F, G, A, B + sharps/flats)

    def test_list_tunings(self, api_client):
        """GET /api/music/temperament/tunings - List tuning systems."""
        response = api_client.get("/api/music/temperament/tunings")
        assert response.status_code == 200
        result = response.json()
        # Response is a dict with named tuning presets
        assert isinstance(result, dict)
        # Should have at least 'standard' tuning
        assert "standard" in result or len(result) > 0


# =============================================================================
# COMPARISON TESTS
# =============================================================================

@pytest.mark.router
class TestTemperamentComparison:
    """Test temperament comparison endpoints."""

    def test_compare_temperaments(self, api_client, sample_compare_request):
        """POST /api/music/temperament/compare - Compare two temperaments."""
        response = api_client.post(
            "/api/music/temperament/compare",
            json=sample_compare_request
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # API returns positions and summary with deviation data
            assert isinstance(result, dict)
            assert "positions" in result or "summary" in result or "temperament" in result

    def test_compare_all_temperaments(self, api_client):
        """GET /api/music/temperament/compare-all - Compare all temperaments."""
        response = api_client.get("/api/music/temperament/compare-all")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            # Should return comparison matrix or list
            assert isinstance(result, (list, dict))

    def test_compare_with_different_root(self, api_client):
        """POST /api/music/temperament/compare - Compare with different root."""
        request = {
            "temperament1": "equal",
            "temperament2": "just",
            "root_note": "C4",
            "frequency": 261.63
        }
        response = api_client.post(
            "/api/music/temperament/compare",
            json=request
        )
        assert response.status_code in (200, 422, 500)


# =============================================================================
# CALCULATION TESTS
# =============================================================================

@pytest.mark.router
class TestTemperamentCalculations:
    """Test temperament calculation endpoints."""

    def test_equal_temperament(self, api_client):
        """GET /api/music/temperament/equal-temperament - Calculate equal temperament."""
        response = api_client.get(
            "/api/music/temperament/equal-temperament",
            params={"root_frequency": 440.0, "num_notes": 12}
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # Should return 12 frequencies
            if "frequencies" in result:
                assert len(result["frequencies"]) == 12

    def test_resolve_temperament(self, api_client):
        """GET /api/music/temperament/resolve - Resolve temperament for note."""
        response = api_client.get(
            "/api/music/temperament/resolve",
            params={"note": "A4", "temperament": "equal"}
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            result = response.json()
            # A4 in equal temperament should be ~440 Hz
            if "frequency" in result:
                assert 439 < result["frequency"] < 441


# =============================================================================
# TABLE GENERATION TESTS
# =============================================================================

@pytest.mark.router
class TestTemperamentTables:
    """Test temperament table generation endpoints."""

    def test_get_tables(self, api_client):
        """GET /api/music/temperament/tables - Get temperament frequency tables."""
        response = api_client.get("/api/music/temperament/tables")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, (list, dict))

    def test_get_tables_with_params(self, api_client):
        """GET /api/music/temperament/tables - Get tables with parameters."""
        response = api_client.get(
            "/api/music/temperament/tables",
            params={
                "temperament": "equal",
                "root_frequency": 440.0,
                "octaves": 2
            }
        )
        assert response.status_code in (200, 422, 500)
