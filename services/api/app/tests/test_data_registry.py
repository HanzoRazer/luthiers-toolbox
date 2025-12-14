# services/api/app/tests/test_data_registry.py

"""
Data Registry Integration Tests

Tests for:
- Registry initialization and data loading
- Edition-based entitlements
- API endpoints (/api/registry/*)
- Edition middleware
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data_registry import Registry, Edition, EntitlementError


client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Registry Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRegistryInitialization:
    """Test registry initialization with different editions."""

    def test_express_edition_initializes(self):
        """Express edition should initialize successfully."""
        reg = Registry(edition="express")
        assert reg.edition == Edition.EXPRESS

    def test_pro_edition_initializes(self):
        """Pro edition should initialize successfully."""
        reg = Registry(edition="pro")
        assert reg.edition == Edition.PRO

    def test_enterprise_edition_initializes(self):
        """Enterprise edition should initialize successfully."""
        reg = Registry(edition="enterprise")
        assert reg.edition == Edition.ENTERPRISE

    def test_invalid_edition_raises(self):
        """Invalid edition string should raise ValueError."""
        with pytest.raises(ValueError):
            Registry(edition="invalid_edition")


class TestSystemTierData:
    """Test system tier data (available to all editions)."""

    @pytest.fixture
    def express_registry(self):
        return Registry(edition="express")

    @pytest.fixture
    def pro_registry(self):
        return Registry(edition="pro")

    def test_express_can_load_scale_lengths(self, express_registry):
        """Express users can access scale lengths."""
        data = express_registry.get_scale_lengths()
        assert "scales" in data
        assert len(data["scales"]) > 0

    def test_express_can_load_wood_species(self, express_registry):
        """Express users can access wood species."""
        data = express_registry.get_wood_species()
        assert "species" in data
        assert len(data["species"]) > 0

    def test_express_can_load_fret_formulas(self, express_registry):
        """Express users can access fret formulas."""
        data = express_registry.get_fret_formulas()
        assert "formulas" in data

    def test_pro_can_load_scale_lengths(self, pro_registry):
        """Pro users can access scale lengths."""
        data = pro_registry.get_scale_lengths()
        assert "scales" in data
        assert len(data["scales"]) > 0


class TestEditionTierData:
    """Test edition tier data (Pro/Enterprise only)."""

    @pytest.fixture
    def express_registry(self):
        return Registry(edition="express")

    @pytest.fixture
    def pro_registry(self):
        return Registry(edition="pro")

    def test_express_cannot_load_empirical_limits(self, express_registry):
        """Express users should get EntitlementError for empirical limits."""
        with pytest.raises(EntitlementError) as exc_info:
            express_registry.get_empirical_limits()
        assert "empirical" in str(exc_info.value).lower()

    def test_pro_can_load_empirical_limits(self, pro_registry):
        """Pro users can access empirical limits."""
        data = pro_registry.get_empirical_limits()
        assert "limits" in data
        assert len(data["limits"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRegistryInfoEndpoint:
    """Test GET /api/registry/info"""

    def test_info_returns_metadata(self):
        """Info endpoint should return registry metadata."""
        response = client.get("/api/registry/info?edition=pro")
        assert response.status_code == 200
        data = response.json()
        assert "edition" in data
        assert "system_datasets" in data
        assert "edition_datasets" in data

    def test_info_express_has_no_edition_datasets(self):
        """Express edition should have empty edition_datasets."""
        response = client.get("/api/registry/info?edition=express")
        assert response.status_code == 200
        data = response.json()
        assert data["edition"] == "express"
        assert data["edition_datasets"] == []

    def test_info_pro_has_edition_datasets(self):
        """Pro edition should have edition_datasets."""
        response = client.get("/api/registry/info?edition=pro")
        assert response.status_code == 200
        data = response.json()
        assert data["edition"] == "pro"
        assert len(data["edition_datasets"]) > 0


class TestScaleLengthsEndpoint:
    """Test GET /api/registry/scale_lengths"""

    def test_scales_returns_data(self):
        """Scale lengths endpoint should return data."""
        response = client.get("/api/registry/scale_lengths?edition=express")
        assert response.status_code == 200
        data = response.json()
        assert "scales" in data
        assert "count" in data
        assert data["count"] > 0

    def test_scales_accessible_to_all_editions(self):
        """Scale lengths should be accessible to all editions."""
        for edition in ["express", "pro", "enterprise"]:
            response = client.get(f"/api/registry/scale_lengths?edition={edition}")
            assert response.status_code == 200


class TestWoodSpeciesEndpoint:
    """Test GET /api/registry/wood_species"""

    def test_woods_returns_data(self):
        """Wood species endpoint should return data."""
        response = client.get("/api/registry/wood_species?edition=express")
        assert response.status_code == 200
        data = response.json()
        assert "species" in data
        assert "count" in data
        assert data["count"] > 0


class TestEmpiricalLimitsEndpoint:
    """Test GET /api/registry/empirical_limits"""

    def test_limits_requires_pro(self):
        """Empirical limits should return 403 for Express."""
        response = client.get(
            "/api/registry/empirical_limits",
            headers={"X-Edition": "express"}
        )
        assert response.status_code == 403
        data = response.json()
        assert "error" in data["detail"]

    def test_limits_accessible_to_pro(self):
        """Empirical limits should be accessible to Pro."""
        response = client.get(
            "/api/registry/empirical_limits",
            headers={"X-Edition": "pro"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "limits" in data
        assert "count" in data


class TestFretFormulasEndpoint:
    """Test GET /api/registry/fret_formulas"""

    def test_formulas_returns_data(self):
        """Fret formulas endpoint should return data."""
        response = client.get("/api/registry/fret_formulas?edition=express")
        assert response.status_code == 200
        data = response.json()
        assert "formulas" in data
        assert "count" in data


class TestHealthEndpoint:
    """Test GET /api/registry/health"""

    def test_health_returns_status(self):
        """Health endpoint should return status."""
        response = client.get("/api/registry/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


# ─────────────────────────────────────────────────────────────────────────────
# Edition Middleware Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestEditionMiddleware:
    """Test edition detection from headers."""

    def test_x_edition_header_works(self):
        """X-Edition header should override default edition."""
        # Test with Express header
        response = client.get(
            "/api/registry/empirical_limits",
            headers={"X-Edition": "express"}
        )
        assert response.status_code == 403

        # Test with Pro header
        response = client.get(
            "/api/registry/empirical_limits",
            headers={"X-Edition": "pro"}
        )
        assert response.status_code == 200

    def test_edition_query_param_works(self):
        """edition query param should work for info endpoint."""
        response = client.get("/api/registry/info?edition=enterprise")
        assert response.status_code == 200
        data = response.json()
        assert data["edition"] == "enterprise"
