"""
Tests for Side Bending Calculator (GEOMETRY-010)

Updated to match physics-based calculator with:
- Lignin Tg temperature model: Tg(MC) = 200 - 8 * MC
- Physics-derived R_min = E * t / (2 * MOR)
- Wood database integration with species variants
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


class TestComputeBendingParameters:

    def test_rosewood_tight_om_waist_returns_yellow_or_red(self):
        plan = compute_bending_parameters(
            species="rosewood",
            side_thickness_mm=2.2,
            waist_radius_mm=25,
            instrument_type="steel_string_acoustic",
        )
        assert plan.risk in ("YELLOW", "RED")

    def test_mahogany_dreadnought_standard_waist_returns_green(self):
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=2.3,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert plan.risk == "GREEN"
        assert 150 <= plan.temp_c <= 200
        assert 6 <= plan.moisture_pct <= 12

    def test_thickness_too_thin_adds_note(self):
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=1.5,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("below" in note.lower() for note in plan.notes)

    def test_thickness_too_thick_adds_note(self):
        plan = compute_bending_parameters(
            species="mahogany",
            side_thickness_mm=3.5,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("above" in note.lower() or "exceed" in note.lower() for note in plan.notes)

    def test_unknown_species_uses_default_with_note(self):
        plan = compute_bending_parameters(
            species="zebrawood",
            side_thickness_mm=2.3,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert any("unknown" in note.lower() for note in plan.notes)
        assert 140 <= plan.temp_c <= 200

    def test_spring_back_is_reasonable(self):
        plan = compute_bending_parameters(
            species="maple",
            side_thickness_mm=2.3,
            waist_radius_mm=90,
            instrument_type="steel_string_acoustic",
        )
        assert 3.0 <= plan.spring_back_deg <= 10.0

    def test_archtop_jazz_uses_correct_thickness_range(self):
        plan = compute_bending_parameters(
            species="maple",
            side_thickness_mm=2.0,
            waist_radius_mm=100,
            instrument_type="archtop_jazz",
        )
        assert any("below" in note.lower() for note in plan.notes)


class TestCheckSideThickness:

    def test_steel_string_returns_correct_range(self):
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="mahogany",
        )
        assert spec.min_mm == 2.0
        assert spec.max_mm == 2.5
        assert spec.target_mm == 2.3

    def test_rosewood_adds_density_note(self):
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="rosewood",
        )
        assert "dense" in spec.note.lower()

    def test_cedar_adds_lightwood_note(self):
        spec = check_side_thickness(
            instrument_type="steel_string_acoustic",
            species="cedar",
        )
        assert "light" in spec.note.lower() or "soft" in spec.note.lower()

    def test_unknown_instrument_uses_defaults(self):
        spec = check_side_thickness(
            instrument_type="mandolin",
            species="sapele",
        )
        assert "unknown" in spec.note.lower()
        assert spec.min_mm == 2.0
        assert spec.max_mm == 2.5


class TestHelperFunctions:

    def test_list_supported_species(self):
        species = list_supported_species()
        assert any("mahogany" in s for s in species)
        assert any("rosewood" in s for s in species)
        assert any("maple" in s for s in species)
        assert len(species) > 0

    def test_list_instrument_types(self):
        types = list_instrument_types()
        assert "steel_string_acoustic" in types
        assert "classical" in types
        assert "archtop_jazz" in types
        assert len(types) == len(SIDE_THICKNESS_TARGETS_MM)


class TestSideBendingEndpoint:

    def test_endpoint_exists_and_returns_200(self):
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
        response = client.post(
            "/api/instrument/side-bending",
            json={
                "species": "mahogany",
                "side_thickness_mm": 0,
                "waist_radius_mm": 90,
                "instrument_type": "steel_string_acoustic",
            },
        )
        assert response.status_code == 422


class TestSideThicknessEndpoint:

    def test_endpoint_exists_and_returns_200(self):
        response = client.post(
            "/api/instrument/side-thickness",
            json={
                "instrument_type": "classical",
                "species": "cedar",
            },
        )
        assert response.status_code == 200

    def test_endpoint_returns_correct_structure(self):
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

    def test_endpoint_exists_and_returns_200(self):
        response = client.get("/api/instrument/side-bending/options")
        assert response.status_code == 200

    def test_endpoint_returns_species_and_types(self):
        response = client.get("/api/instrument/side-bending/options")
        data = response.json()
        assert "species" in data
        assert "instrument_types" in data
        assert len(data["species"]) > 0
        assert len(data["instrument_types"]) > 0
