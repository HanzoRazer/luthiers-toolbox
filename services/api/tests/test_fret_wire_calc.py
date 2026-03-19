"""
Tests for Fret Wire Selection Calculator (GEOMETRY-006)
"""

import pytest
from fastapi.testclient import TestClient

from app.calculators.fret_wire_calc import (
    recommend_fret_wire,
    list_fret_wire_catalog,
    list_fret_wire_names,
    list_playing_styles,
    get_fret_wire,
    FretWireSpec,
    FRET_WIRE_CATALOG,
)
from app.main import app

client = TestClient(app)


# ─── Unit Tests ───────────────────────────────────────────────────────────────

class TestFretWireCatalog:
    """Tests for fret wire catalog data."""

    def test_catalog_has_seven_profiles(self):
        """Catalog should have 7 fret wire profiles."""
        assert len(FRET_WIRE_CATALOG) == 7

    def test_all_profiles_have_required_fields(self):
        """All profiles should have required fields."""
        for name, spec in FRET_WIRE_CATALOG.items():
            assert spec.name == name
            assert spec.crown_width_mm > 0
            assert spec.crown_height_mm > 0
            assert spec.tang_depth_mm > 0
            assert spec.material in ("nickel_silver", "stainless", "evo_gold")
            assert spec.hardness_hv > 0

    def test_get_fret_wire_returns_spec(self):
        """get_fret_wire should return correct spec."""
        spec = get_fret_wire("jumbo")
        assert spec is not None
        assert spec.crown_height_mm == 1.52


class TestRecommendFretWire:
    """Tests for recommend_fret_wire function."""

    def test_returns_all_profiles_ranked(self):
        """Should return all profiles ranked by suitability."""
        recs = recommend_fret_wire(
            playing_style="flatpick",
            fretboard_material="rosewood",
            neck_profile="C",
            string_gauge="medium",
        )
        assert len(recs) == 7

    def test_fingerstyle_prefers_lower_frets(self):
        """Fingerstyle should rank vintage/medium higher."""
        recs = recommend_fret_wire(
            playing_style="fingerstyle",
            fretboard_material="rosewood",
            neck_profile="C",
            string_gauge="light",
        )
        # Top recommendation should be vintage_narrow or medium
        top_names = [r.name for r in recs[:3]]
        assert "vintage_narrow" in top_names or "medium" in top_names

    def test_shred_prefers_jumbo_frets(self):
        """Shred style should rank jumbo frets higher."""
        recs = recommend_fret_wire(
            playing_style="shred",
            fretboard_material="maple",
            neck_profile="D",
            string_gauge="light",
        )
        # Top recommendations should include jumbo variants
        top_names = [r.name for r in recs[:3]]
        assert any("jumbo" in name for name in top_names)

    def test_heavy_strings_boost_taller_frets(self):
        """Heavy string gauge should boost score for taller frets."""
        light_recs = recommend_fret_wire(
            playing_style="flatpick",
            string_gauge="light",
        )
        heavy_recs = recommend_fret_wire(
            playing_style="flatpick",
            string_gauge="heavy",
        )
        # With heavy strings, jumbo should rank higher than with light
        light_jumbo_idx = next(i for i, r in enumerate(light_recs) if r.name == "jumbo")
        heavy_jumbo_idx = next(i for i, r in enumerate(heavy_recs) if r.name == "jumbo")
        assert heavy_jumbo_idx <= light_jumbo_idx


# ─── API Endpoint Tests ───────────────────────────────────────────────────────

class TestFretWireRecommendEndpoint:
    """Tests for POST /api/instrument/fret-wire/recommend endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/fret-wire/recommend",
            json={"playing_style": "flatpick"},
        )
        assert response.status_code == 200

    def test_endpoint_returns_ranked_recommendations(self):
        """Response should include ranked recommendations."""
        response = client.post(
            "/api/instrument/fret-wire/recommend",
            json={
                "playing_style": "jazz",
                "fretboard_material": "ebony",
                "neck_profile": "V",
                "string_gauge": "light",
            },
        )
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 7
        # Check structure
        rec = data["recommendations"][0]
        assert "name" in rec
        assert "crown_width_mm" in rec
        assert "gate" in rec


class TestFretWireCatalogEndpoint:
    """Tests for GET /api/instrument/fret-wire/catalog endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.get("/api/instrument/fret-wire/catalog")
        assert response.status_code == 200

    def test_endpoint_returns_full_catalog(self):
        """Response should include all fret wire profiles."""
        response = client.get("/api/instrument/fret-wire/catalog")
        data = response.json()
        assert "catalog" in data
        assert len(data["catalog"]) == 7


class TestFretWireOptionsEndpoint:
    """Tests for GET /api/instrument/fret-wire/options endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.get("/api/instrument/fret-wire/options")
        assert response.status_code == 200

    def test_endpoint_returns_all_option_lists(self):
        """Response should include all option lists."""
        response = client.get("/api/instrument/fret-wire/options")
        data = response.json()
        assert "playing_styles" in data
        assert "fretboard_materials" in data
        assert "neck_profiles" in data
        assert "string_gauges" in data
        assert "fret_wire_names" in data
        assert len(data["playing_styles"]) >= 4
        assert len(data["fret_wire_names"]) == 7
