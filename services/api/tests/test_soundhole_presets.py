"""
Tests for soundhole_presets.py — Preset data module.

DECOMP-002 Phase 5: extracted from soundhole_calc.py.
"""
import pytest

from app.calculators.soundhole_presets import (
    # Preset dictionaries
    PRESETS,
    BODY_DIMENSION_PRESETS,
    TOP_SPECIES_THICKNESS,
    STANDARD_DIAMETERS_MM,
    STANDARD_POSITION_FRACTION,
    POSITION_MIN_FRACTION,
    POSITION_MAX_FRACTION,
    # Helper functions
    get_preset,
    list_presets,
    get_species_thickness,
    list_top_species,
    list_body_styles,
    get_standard_diameter,
)


# ── PRESETS Tests ─────────────────────────────────────────────────────────────

class TestPresets:
    def test_presets_exist(self):
        """PRESETS dictionary should contain expected guitar models."""
        expected_keys = {
            "martin_om", "martin_d28", "gibson_j45", "classical",
            "selmer_oval", "om_side_port", "benedetto_17"
        }
        assert set(PRESETS.keys()) == expected_keys

    def test_preset_has_required_keys(self):
        """Each preset should have all required keys."""
        required_keys = {
            "label", "volume_liters", "ports", "ring_width_mm",
            "x_from_neck_fraction", "body_length_mm", "target_f_hz", "notes"
        }
        for preset_name, preset_data in PRESETS.items():
            assert set(preset_data.keys()) == required_keys, \
                f"Preset '{preset_name}' missing required keys"

    def test_preset_ports_initialized(self):
        """Ports should be initialized after get_preset() call."""
        preset = get_preset("martin_om")
        assert preset is not None
        assert preset["ports"] is not None
        assert len(preset["ports"]) > 0

    def test_list_presets_returns_all(self):
        """list_presets() should return summary for all presets."""
        preset_list = list_presets()
        assert len(preset_list) == len(PRESETS)
        for item in preset_list:
            assert "id" in item
            assert "label" in item
            assert "target_f_hz" in item
            assert "volume_liters" in item


# ── BODY_DIMENSION_PRESETS Tests ──────────────────────────────────────────────

class TestBodyDimensionPresets:
    def test_body_dimension_presets_exist(self):
        """BODY_DIMENSION_PRESETS should contain expected models."""
        expected_keys = {
            "martin_om", "martin_d28", "gibson_j45", "gibson_l00",
            "classical_650", "parlor", "benedetto_17"
        }
        assert set(BODY_DIMENSION_PRESETS.keys()) == expected_keys

    def test_body_dimensions_have_required_keys(self):
        """Each body dimension preset should have required dimension keys."""
        required_keys = {
            "label", "lower_bout_mm", "upper_bout_mm", "waist_mm",
            "body_length_mm", "depth_endblock_mm", "depth_neck_mm"
        }
        for preset_name, preset_data in BODY_DIMENSION_PRESETS.items():
            actual_keys = set(preset_data.keys())
            # benedetto_17 has an additional shape_factor key
            if preset_name == "benedetto_17":
                assert "shape_factor" in actual_keys
                actual_keys.remove("shape_factor")
            assert required_keys.issubset(actual_keys), \
                f"Body dimension preset '{preset_name}' missing required keys"

    def test_dimensions_are_positive(self):
        """All dimension values should be positive numbers."""
        for preset_name, preset_data in BODY_DIMENSION_PRESETS.items():
            for key, value in preset_data.items():
                if key != "label":  # Skip string fields
                    assert value > 0, \
                        f"Preset '{preset_name}' has non-positive value for '{key}': {value}"


# ── TOP_SPECIES_THICKNESS Tests ───────────────────────────────────────────────

class TestTopSpeciesThickness:
    def test_species_thickness_exists(self):
        """TOP_SPECIES_THICKNESS should contain expected wood species."""
        expected_keys = {
            "sitka_spruce", "adirondack_spruce", "engelmann_spruce",
            "european_spruce", "western_red_cedar", "redwood",
            "mahogany", "koa", "archtop_carved"
        }
        assert set(TOP_SPECIES_THICKNESS.keys()) == expected_keys

    def test_species_has_required_keys(self):
        """Each species should have all required acoustic property keys."""
        required_keys = {
            "label", "thick_mm", "range_mm", "E_L_GPa",
            "E_C_GPa", "rho_kg_m3", "note"
        }
        for species_key, species_data in TOP_SPECIES_THICKNESS.items():
            assert set(species_data.keys()) == required_keys, \
                f"Species '{species_key}' missing required keys"

    def test_acoustic_properties_are_positive(self):
        """All acoustic properties should be positive values."""
        for species_key, species_data in TOP_SPECIES_THICKNESS.items():
            assert species_data["thick_mm"] > 0
            assert species_data["range_mm"][0] > 0
            assert species_data["range_mm"][1] > species_data["range_mm"][0]
            assert species_data["E_L_GPa"] > 0
            assert species_data["E_C_GPa"] > 0
            assert species_data["rho_kg_m3"] > 0

    def test_get_species_thickness(self):
        """get_species_thickness() should return species data."""
        sitka = get_species_thickness("sitka_spruce")
        assert sitka is not None
        assert sitka["label"] == "Sitka Spruce"
        assert sitka["thick_mm"] == 2.5

    def test_list_top_species(self):
        """list_top_species() should return all species."""
        species_list = list_top_species()
        assert len(species_list) == len(TOP_SPECIES_THICKNESS)
        for item in species_list:
            assert "key" in item
            assert "label" in item
            assert "thick_mm" in item


# ── Standard Body Style Data Tests ────────────────────────────────────────────

class TestStandardBodyStyleData:
    def test_standard_diameters_exist(self):
        """STANDARD_DIAMETERS_MM should contain expected body styles."""
        expected_keys = {
            "dreadnought", "om_000", "jumbo", "parlor",
            "classical", "concert", "auditorium", "archtop"
        }
        assert set(STANDARD_DIAMETERS_MM.keys()) == expected_keys

    def test_standard_positions_exist(self):
        """STANDARD_POSITION_FRACTION should match STANDARD_DIAMETERS_MM."""
        assert set(STANDARD_POSITION_FRACTION.keys()) == set(STANDARD_DIAMETERS_MM.keys())

    def test_position_fractions_are_valid(self):
        """Position fractions should be between min and max (or None for archtop)."""
        for style, fraction in STANDARD_POSITION_FRACTION.items():
            if fraction is not None:
                assert POSITION_MIN_FRACTION <= fraction <= POSITION_MAX_FRACTION, \
                    f"Style '{style}' position {fraction} outside valid range"

    def test_list_body_styles(self):
        """list_body_styles() should exclude archtop."""
        styles = list_body_styles()
        assert "archtop" not in styles
        assert len(styles) == len(STANDARD_DIAMETERS_MM) - 1

    def test_get_standard_diameter(self):
        """get_standard_diameter() should return diameter for known styles."""
        dread = get_standard_diameter("dreadnought")
        assert dread == 100.0

        om = get_standard_diameter("om_000")
        assert om == 98.0

        # Should handle different formats
        om_alt = get_standard_diameter("OM-000")
        assert om_alt == 98.0


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestIntegration:
    def test_presets_match_body_dimensions(self):
        """Guitar presets should have matching body dimension presets."""
        # Not all soundhole presets have body dimensions, but key ones should match
        matching_keys = {"martin_om", "martin_d28", "gibson_j45"}
        for key in matching_keys:
            assert key in PRESETS
            assert key in BODY_DIMENSION_PRESETS

    def test_preset_volumes_are_reasonable(self):
        """All preset volumes should be in reasonable range for acoustic guitars."""
        for preset_name, preset_data in PRESETS.items():
            volume = preset_data["volume_liters"]
            # Acoustic guitar bodies typically 15-25 liters
            assert 10 < volume < 30, \
                f"Preset '{preset_name}' has unusual volume: {volume}L"

    def test_preset_target_frequencies_are_reasonable(self):
        """All preset target frequencies should be in typical Helmholtz range."""
        for preset_name, preset_data in PRESETS.items():
            f_hz = preset_data["target_f_hz"]
            # Acoustic guitar Helmholtz typically 85-120 Hz
            assert 70 < f_hz < 150, \
                f"Preset '{preset_name}' has unusual target f_H: {f_hz} Hz"
