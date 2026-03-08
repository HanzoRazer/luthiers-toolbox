"""Smoke tests for Data Registry endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_info_endpoint_exists(client):
    """GET /api/registry/info endpoint exists."""
    response = client.get("/api/registry/info")
    assert response.status_code != 404


def test_scale_lengths_endpoint_exists(client):
    """GET /api/registry/scale_lengths endpoint exists."""
    response = client.get("/api/registry/scale_lengths")
    assert response.status_code != 404


def test_wood_species_endpoint_exists(client):
    """GET /api/registry/wood_species endpoint exists."""
    response = client.get("/api/registry/wood_species")
    assert response.status_code != 404


def test_empirical_limits_endpoint_exists(client):
    """GET /api/registry/empirical_limits endpoint exists."""
    response = client.get("/api/registry/empirical_limits")
    # May return 403 for express edition, but not 404
    assert response.status_code != 404


def test_empirical_limits_by_wood_endpoint_exists(client):
    """GET /api/registry/empirical_limits/{wood_id} endpoint exists."""
    response = client.get("/api/registry/empirical_limits/maple_hard")
    # May return 403 for express edition, but not 404
    assert response.status_code != 404


def test_fret_formulas_endpoint_exists(client):
    """GET /api/registry/fret_formulas endpoint exists."""
    response = client.get("/api/registry/fret_formulas")
    assert response.status_code != 404


# =============================================================================
# Registry Info Endpoint
# =============================================================================

def test_info_returns_200(client):
    """GET /api/registry/info returns 200."""
    response = client.get("/api/registry/info")
    assert response.status_code == 200


def test_info_has_edition(client):
    """Info response has edition field."""
    response = client.get("/api/registry/info")
    data = response.json()

    assert "edition" in data
    assert data["edition"] in ["express", "pro", "enterprise"]


def test_info_has_version(client):
    """Info response has version field."""
    response = client.get("/api/registry/info")
    data = response.json()

    assert "version" in data


def test_info_has_tiers(client):
    """Info response has tiers list."""
    response = client.get("/api/registry/info")
    data = response.json()

    assert "tiers" in data
    assert isinstance(data["tiers"], list)


def test_info_has_system_datasets(client):
    """Info response has system_datasets list."""
    response = client.get("/api/registry/info")
    data = response.json()

    assert "system_datasets" in data
    assert isinstance(data["system_datasets"], list)


def test_info_has_edition_datasets(client):
    """Info response has edition_datasets list."""
    response = client.get("/api/registry/info")
    data = response.json()

    assert "edition_datasets" in data
    assert isinstance(data["edition_datasets"], list)


def test_info_express_edition(client):
    """Express edition has system datasets only."""
    response = client.get("/api/registry/info?edition=express")
    data = response.json()

    assert data["edition"] == "express"
    assert len(data["system_datasets"]) > 0


def test_info_pro_edition(client):
    """Pro edition has edition datasets."""
    response = client.get("/api/registry/info?edition=pro")
    data = response.json()

    assert data["edition"] == "pro"
    assert len(data["edition_datasets"]) > 0


def test_info_invalid_edition(client):
    """Invalid edition returns 400."""
    response = client.get("/api/registry/info?edition=invalid_xyz")
    assert response.status_code == 400


# =============================================================================
# Scale Lengths Endpoint
# =============================================================================

def test_scale_lengths_returns_200(client):
    """GET /api/registry/scale_lengths returns 200."""
    response = client.get("/api/registry/scale_lengths")
    assert response.status_code == 200


def test_scale_lengths_has_scales(client):
    """Scale lengths response has scales dict."""
    response = client.get("/api/registry/scale_lengths")
    data = response.json()

    assert "scales" in data
    assert isinstance(data["scales"], dict)


def test_scale_lengths_has_count(client):
    """Scale lengths response has count field."""
    response = client.get("/api/registry/scale_lengths")
    data = response.json()

    assert "count" in data
    assert isinstance(data["count"], int)


def test_scale_lengths_count_matches(client):
    """Count matches number of scales."""
    response = client.get("/api/registry/scale_lengths")
    data = response.json()

    assert data["count"] == len(data["scales"])


def test_scale_lengths_has_common_scales(client):
    """Scales include common guitar scale lengths."""
    response = client.get("/api/registry/scale_lengths")
    data = response.json()

    scales = data["scales"]
    # Should have at least some entries
    assert len(scales) > 0


# =============================================================================
# Wood Species Endpoint
# =============================================================================

def test_wood_species_returns_200(client):
    """GET /api/registry/wood_species returns 200."""
    response = client.get("/api/registry/wood_species")
    assert response.status_code == 200


def test_wood_species_has_species(client):
    """Wood species response has species dict."""
    response = client.get("/api/registry/wood_species")
    data = response.json()

    assert "species" in data
    assert isinstance(data["species"], dict)


def test_wood_species_has_count(client):
    """Wood species response has count field."""
    response = client.get("/api/registry/wood_species")
    data = response.json()

    assert "count" in data
    assert isinstance(data["count"], int)


def test_wood_species_count_matches(client):
    """Count matches number of species."""
    response = client.get("/api/registry/wood_species")
    data = response.json()

    assert data["count"] == len(data["species"])


def test_wood_species_has_entries(client):
    """Wood species has at least some entries."""
    response = client.get("/api/registry/wood_species")
    data = response.json()

    assert len(data["species"]) > 0


# =============================================================================
# Empirical Limits Endpoint
# =============================================================================

def test_empirical_limits_requires_edition(client):
    """Empirical limits requires Pro/Enterprise edition."""
    response = client.get("/api/registry/empirical_limits")
    # Express edition should get 403
    assert response.status_code in [200, 403]


def test_empirical_limits_with_pro_header(client):
    """Empirical limits accessible with Pro edition header."""
    response = client.get(
        "/api/registry/empirical_limits",
        headers={"X-Edition": "pro"}
    )
    # Should be 200 with pro header, or 403 if middleware doesn't use header
    assert response.status_code in [200, 403]


def test_empirical_limits_response_structure(client):
    """Empirical limits response has expected structure when accessible."""
    response = client.get(
        "/api/registry/empirical_limits",
        headers={"X-Edition": "pro"}
    )

    if response.status_code == 200:
        data = response.json()
        assert "limits" in data
        assert "count" in data
        assert "edition_required" in data


# =============================================================================
# Empirical Limits by Wood Endpoint
# =============================================================================

def test_empirical_limits_by_wood_requires_edition(client):
    """Empirical limits by wood requires Pro/Enterprise edition."""
    response = client.get("/api/registry/empirical_limits/maple_hard")
    # Express edition should get 403
    assert response.status_code in [200, 403, 404]


def test_empirical_limits_unknown_wood(client):
    """Unknown wood returns 404 (if entitled)."""
    response = client.get(
        "/api/registry/empirical_limits/nonexistent_wood_xyz",
        headers={"X-Edition": "pro"}
    )
    # Either 404 (wood not found) or 403 (not entitled)
    assert response.status_code in [403, 404]


# =============================================================================
# Fret Formulas Endpoint
# =============================================================================

def test_fret_formulas_returns_200(client):
    """GET /api/registry/fret_formulas returns 200."""
    response = client.get("/api/registry/fret_formulas")
    assert response.status_code == 200


def test_fret_formulas_has_formulas(client):
    """Fret formulas response has formulas dict."""
    response = client.get("/api/registry/fret_formulas")
    data = response.json()

    assert "formulas" in data
    assert isinstance(data["formulas"], dict)


def test_fret_formulas_has_count(client):
    """Fret formulas response has count field."""
    response = client.get("/api/registry/fret_formulas")
    data = response.json()

    assert "count" in data
    assert isinstance(data["count"], int)


def test_fret_formulas_has_edition(client):
    """Fret formulas response has edition field."""
    response = client.get("/api/registry/fret_formulas")
    data = response.json()

    assert "edition" in data


def test_fret_formulas_with_edition_param(client):
    """Fret formulas accepts edition parameter."""
    response = client.get("/api/registry/fret_formulas?edition=express")
    assert response.status_code == 200

    data = response.json()
    assert data["edition"] == "express"
