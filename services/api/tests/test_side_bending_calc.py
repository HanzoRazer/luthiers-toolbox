"""
Tests for Side Bending Calculator (GEOMETRY-010)
"""

import pytest
from fastapi.testclient import TestClient

from app.calculators.side_bending_calc import (
    compute_bending_parameters,
    check_side_thickness,
    list_supported_species,
    list_instrument_types,
    BENDING_PARAMS,
    SIDE_THICKNESS_TARGETS_MM,
)
from app.main import app

client = TestClient(app)


# ─── Unit Tests ───────────────────────────────────────────────────────────────

class TestComputeBendingParameters:
    """Tests for compute_bending_parameters function."""

    def test_rosewood_tight_om_waist_returns_yellow_or_red(self):
        """Rosewood on tight OM waist (~25mm) should be YELLOW or RED."""
        # OM waist is typically around 25-35mm, which is below rosewood's 45mm min
        plan = compute_bending_parameters(
            species="rosewood",
            side_thickness_mm=2.2,
            waist_radius_mm=25,  # Tight OM waist
            instrument_type="steel_string_acoustic",
        )
        assert plan.risk in ("YELLOW", "RED")
        assert any("cracking" in note.lower() or "radius" in note.lower() for note in plan.notes)

    def test_mahogany_dreadnought_standard_waist_returns_green(self):
        """Mahogany on dreadnought standard waist should be GREEN."""
        # Dreadnought waist is typically 80-100mm, well above mahogany's 50mm min
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=2.3,
            waist_radius_mm=90,  # Standard dreadnought waist
            instrument_type="steel_string_acoustic",
        )
        assert plan.risk == "GREEN"
        assert plan.temp_c == 150  # Mahogany bending temp
        assert plan.moisture_pct == 8

    def test_thickness_too_thin_adds_note(self):
        """Thickness below minimum should add a warning note."""
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=1.5,  # Below 2.0mm minimum for steel string
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("below minimum" in note.lower() for note in plan.notes)

    def test_thickness_too_thick_adds_note(self):
        """Thickness above maximum should add a warning note."""
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=3.5,  # Above 2.5mm maximum for steel string
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("above maximum" in note.lower() for note in plan.notes)

    def test_unknown_species_uses_default_with_note(self):
        """Unknown species should use defaults and add a note."""
        plan = compute_bending_parameters(
            species="zebrawood",  # Not in BENDING_PARAMS
            side_thickness_mm=2.3,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("unknown species" in note.lower() for note in plan.notes)
        # Should use default temp (155°C)
        assert plan.temp_c == 155

    def test_spring_back_is_reasonable(self):
        """Spring-back should be in reasonable range (3-10 degrees)."""
        plan = compute_bending_parameters(
            species="maple",
            side_thickness_mm=2.3,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert 3.0 <= plan.spring_back_deg <= 10.0

    def test_archtop_jazz_uses_correct_thickness_range(self):
        """Archtop jazz should use 2.5-3.0mm thickness range."""
        plan = compute_bending_parameters(
            species="maple",
            side_thickness_mm=2.0,  # Below archtop minimum of 2.5mm
            waist_radius_mm=100,
            instrument_type="archtop_jazz",
        )
        assert any("below minimum" in note.lower() for note in plan.notes)


class TestCheckSideThickness:
    """Tests for check_side_thickness function."""

    def test_steel_string_returns_correct_range(self):
        """Steel string acoustic should return 2.0-2.5mm range."""
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="mahogany",
        )
        assert spec.min_mm == 2.0
        assert spec.max_mm == 2.5
        assert spec.target_mm == 2.3

    def test_rosewood_adds_density_note(self):
        """Rosewood should add a note about density."""
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="rosewood",
        )
        assert "dense" in spec.note.lower()

    def test_cedar_adds_softwood_note(self):
        """Cedar should add a note about soft wood."""
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="cedar",
        )
        assert "soft" in spec.note.lower()

    def test_unknown_instrument_uses_defaults(self):
        """Unknown instrument type should use acoustic defaults with note."""
        spec = check_side_thickness(
            instrument_type="mandolin",  # Not in SIDE_THICKNESS_TARGETS_MM
            species="sapele",  # Species without special note
        )
        assert "unknown instrument" in spec.note.lower()
        # Should use defaults similar to acoustic
        assert spec.min_mm == 1.8
        assert spec.max_mm == 2.5


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_list_supported_species(self):
        """Should return all species from BENDING_PARAMS."""
        species = list_supported_species()
        assert "mahogany" in species
        assert "rosewood" in species
        assert "maple" in species
        assert len(species) == len(BENDING_PARAMS)

    def test_list_instrument_types(self):
        """Should return all instrument types."""
        types = list_instrument_types()
        assert "steel_string_acoustic" in types
        assert "classical" in types
        assert "archtop_jazz" in types
        assert len(types) == len(SIDE_THICKNESS_TARGETS_MM)


# ─── API Endpoint Tests ───────────────────────────────────────────────────────

class TestSideBendingEndpoint:
    """Tests for POST /api/instrument/side-bending endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/side-bending",
            json={
                "species": "mahogany",
                "side_thickness_mm": 2.3,
                "waist_radius_mm": 90,
                "instrument_type": "steel_string_acoustic",
            },
        )
        assert response.status_code == 200

    def test_endpoint_returns_correct_structure(self):
        """Response should have correct structure."""
        response = client.post(
            "/api/instrument/side-bending",
            json={
                "species": "rosewood",
                "side_thickness_mm": 2.2,
                "waist_radius_mm": 50,
                "instrument_type": "steel_string_acoustic",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk" in data
        assert "temp_c" in data
        assert "moisture_pct" in data
        assert "spring_back_deg" in data
        assert "notes" in data
        assert data["risk"] in ("GREEN", "YELLOW", "RED")

    def test_endpoint_rejects_invalid_thickness(self):
        """Endpoint should reject non-positive thickness."""
        response = client.post(
            "/api/instrument/side-bending",
            json={
                "species": "mahogany",
                "side_thickness_mm": 0,  # Invalid
                "waist_radius_mm": 90,
                "instrument_type": "steel_string_acoustic",
            },
        )
        assert response.status_code == 422


class TestSideThicknessEndpoint:
    """Tests for POST /api/instrument/side-thickness endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/side-thickness",
            json={
                "instrument_type": "classical",
                "species": "cedar",
            },
        )
        assert response.status_code == 200

    def test_endpoint_returns_correct_structure(self):
        """Response should have correct structure."""
        response = client.post(
            "/api/instrument/side-thickness",
            json={
                "instrument_type": "steel_string_acoustic",
                "species": "mahogany",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "target_mm" in data
        assert "min_mm" in data
        assert "max_mm" in data
        assert "note" in data


class TestBendingOptionsEndpoint:
    """Tests for GET /api/instrument/side-bending/options endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.get("/api/instrument/side-bending/options")
        assert response.status_code == 200

    def test_endpoint_returns_species_and_types(self):
        """Response should include species and instrument types."""
        response = client.get("/api/instrument/side-bending/options")
        data = response.json()
        assert "species" in data
        assert "instrument_types" in data
        assert len(data["species"]) > 0
        assert len(data["instrument_types"]) > 0
