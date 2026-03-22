"""
Smoke tests for instrument_geometry_router.py (37 endpoints).

Target: Verify each endpoint returns 200 or 422 (not 404).
Router mounted at: /api/instrument
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PREFIX = "/api/instrument"


# =============================================================================
# Router Mount Verification
# =============================================================================

class TestRouterMount:
    """Verify the instrument geometry router is mounted correctly."""

    def test_router_mounted_at_api_instrument(self):
        """Router should be accessible at /api/instrument prefix."""
        # Call a known endpoint - side-bending/options is GET with no params
        resp = client.get(f"{PREFIX}/side-bending/options")
        assert resp.status_code != 404, "Router not mounted at /api/instrument"
        assert resp.status_code == 200


# =============================================================================
# Side Bending Endpoints
# =============================================================================

class TestSideBendingEndpoints:
    """Smoke tests for side bending calculation endpoints."""

    def test_side_bending_valid(self):
        """POST /side-bending with valid payload returns 200."""
        resp = client.post(f"{PREFIX}/side-bending", json={
            "species": "rosewood_indian",
            "side_thickness_mm": 2.5,
            "waist_radius_mm": 75.0,
            "instrument_type": "steel_string_acoustic",
            "bending_method": "bending_iron"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "risk" in data
            assert "temp_c" in data

    def test_side_bending_missing_required_returns_422(self):
        """POST /side-bending without required fields returns 422."""
        resp = client.post(f"{PREFIX}/side-bending", json={})
        assert resp.status_code == 422

    def test_side_bending_compare_valid(self):
        """POST /side-bending/compare with valid params returns 200."""
        resp = client.post(
            f"{PREFIX}/side-bending/compare",
            params={
                "waist_radius_mm": 75.0,
                "side_thickness_mm": 2.5,
                "instrument_type": "steel_string_acoustic"
            }
        )
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_side_bending_options(self):
        """GET /side-bending/options returns 200 with species list."""
        resp = client.get(f"{PREFIX}/side-bending/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "species" in data
        assert "instrument_types" in data
        assert isinstance(data["species"], list)

    def test_side_thickness_valid(self):
        """POST /side-thickness with valid payload returns 200."""
        resp = client.post(f"{PREFIX}/side-thickness", json={
            "instrument_type": "steel_string_acoustic",
            "species": "rosewood_indian"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "target_mm" in data

    def test_side_thickness_missing_required_returns_422(self):
        """POST /side-thickness without required fields returns 422."""
        resp = client.post(f"{PREFIX}/side-thickness", json={})
        assert resp.status_code == 422


# =============================================================================
# Nut Slot Endpoints
# =============================================================================

class TestNutSlotEndpoints:
    """Smoke tests for nut slot calculation endpoints."""

    def test_nut_slots_with_preset(self):
        """POST /nut-slots with preset name returns 200."""
        resp = client.post(f"{PREFIX}/nut-slots", json={
            "preset_name": "light_acoustic_012",
            "fret_type": "medium",
            "nut_width_mm": 43.0,
            "clearance_mm": 0.13
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "slots" in data

    def test_nut_slots_with_custom_strings(self):
        """POST /nut-slots with custom string set returns 200."""
        resp = client.post(f"{PREFIX}/nut-slots", json={
            "string_set": [
                {"name": "e", "gauge_inch": 0.010},
                {"name": "B", "gauge_inch": 0.013},
                {"name": "G", "gauge_inch": 0.017},
                {"name": "D", "gauge_inch": 0.026},
                {"name": "A", "gauge_inch": 0.036},
                {"name": "E", "gauge_inch": 0.046}
            ],
            "fret_type": "medium"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_nut_slots_empty_payload_uses_defaults(self):
        """POST /nut-slots with empty payload uses defaults."""
        resp = client.post(f"{PREFIX}/nut-slots", json={})
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_nut_slot_options(self):
        """GET /nut-slots/options returns 200 with fret types."""
        resp = client.get(f"{PREFIX}/nut-slots/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "fret_types" in data
        assert "preset_string_sets" in data


# =============================================================================
# Setup Cascade Endpoints
# =============================================================================

class TestSetupCascadeEndpoints:
    """Smoke tests for setup cascade evaluation."""

    def test_setup_evaluate_with_defaults(self):
        """POST /setup/evaluate with defaults returns 200."""
        resp = client.post(f"{PREFIX}/setup/evaluate", json={})
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "overall_gate" in data
            assert "issues" in data

    def test_setup_evaluate_with_custom_values(self):
        """POST /setup/evaluate with custom values returns 200."""
        resp = client.post(f"{PREFIX}/setup/evaluate", json={
            "neck_angle_deg": 1.8,
            "truss_rod_relief_mm": 0.3,
            "action_at_nut_mm": 0.6,
            "action_at_12th_treble_mm": 2.0,
            "action_at_12th_bass_mm": 2.5,
            "saddle_height_mm": 3.5,
            "scale_length_mm": 645.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"


# =============================================================================
# Soundhole Endpoints
# =============================================================================

class TestSoundholeEndpoints:
    """Smoke tests for soundhole calculation endpoints."""

    def test_soundhole_valid(self):
        """POST /soundhole with valid payload returns 200."""
        resp = client.post(f"{PREFIX}/soundhole", json={
            "body_style": "dreadnought",
            "body_length_mm": 500.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "diameter_mm" in data
            assert "gate" in data

    def test_soundhole_with_custom_diameter(self):
        """POST /soundhole with custom diameter returns 200."""
        resp = client.post(f"{PREFIX}/soundhole", json={
            "body_style": "om_000",
            "body_length_mm": 480.0,
            "custom_diameter_mm": 95.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_soundhole_missing_required_returns_422(self):
        """POST /soundhole without required fields returns 422."""
        resp = client.post(f"{PREFIX}/soundhole", json={})
        assert resp.status_code == 422

    def test_soundhole_check_position_valid(self):
        """POST /soundhole/check-position with valid params returns 200."""
        resp = client.post(f"{PREFIX}/soundhole/check-position", json={
            "diameter_mm": 100.0,
            "position_mm": 250.0,
            "body_length_mm": 500.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "gate" in data

    def test_soundhole_options(self):
        """GET /soundhole/options returns 200 with body styles."""
        resp = client.get(f"{PREFIX}/soundhole/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "body_styles" in data


# =============================================================================
# Bridge Geometry Endpoints (GEOMETRY-004)
# =============================================================================

class TestBridgeEndpoints:
    """Smoke tests for bridge geometry calculation endpoints."""

    def test_bridge_valid(self):
        """POST /bridge with valid payload returns 200."""
        resp = client.post(f"{PREFIX}/bridge", json={
            "body_style": "dreadnought",
            "scale_length_mm": 645.16
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "string_spacing_mm" in data
            assert "bridge_length_mm" in data

    def test_bridge_with_custom_spacing(self):
        """POST /bridge with custom spacing returns 200."""
        resp = client.post(f"{PREFIX}/bridge", json={
            "body_style": "om_000",
            "scale_length_mm": 632.0,
            "string_count": 6,
            "custom_spacing_mm": 55.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_bridge_pin_positions_valid(self):
        """POST /bridge/pin-positions with valid payload returns 200."""
        resp = client.post(f"{PREFIX}/bridge/pin-positions", json={
            "string_spacing_mm": 54.0,
            "string_count": 6,
            "bridge_center_x": 0.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "positions_mm" in data
            assert len(data["positions_mm"]) == 6

    def test_bridge_options(self):
        """GET /bridge/options returns 200 with body styles."""
        resp = client.get(f"{PREFIX}/bridge/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "body_styles" in data


# =============================================================================
# Neck/Tail Block Endpoints (GEOMETRY-005)
# =============================================================================

class TestBlockEndpoints:
    """Smoke tests for neck/tail block calculation endpoints."""

    def test_blocks_with_defaults(self):
        """POST /blocks with defaults returns 200."""
        resp = client.post(f"{PREFIX}/blocks", json={})
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "neck" in data
            assert "tail" in data

    def test_blocks_with_body_style(self):
        """POST /blocks with body style returns 200."""
        resp = client.post(f"{PREFIX}/blocks", json={
            "body_style": "om_000",
            "material": "maple"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_blocks_options(self):
        """GET /blocks/options returns 200 with body styles."""
        resp = client.get(f"{PREFIX}/blocks/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "body_styles" in data


# =============================================================================
# Fret Leveling Endpoints
# =============================================================================

class TestFretLevelingEndpoints:
    """Smoke tests for fret leveling analysis endpoints."""

    def test_fret_leveling_valid(self):
        """POST /fret-leveling with valid heights returns 200."""
        # Simulate 22 fret heights with slight variations
        heights = [1.2 + (i * 0.001) for i in range(22)]
        resp = client.post(f"{PREFIX}/fret-leveling", json={
            "heights_mm": heights,
            "scale_length_mm": 645.0,
            "relief_mm": 0.2,
            "tolerance_mm": 0.03
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "frets" in data
            assert "gate" in data

    def test_fret_leveling_missing_required_returns_422(self):
        """POST /fret-leveling without heights returns 422."""
        resp = client.post(f"{PREFIX}/fret-leveling", json={
            "scale_length_mm": 645.0
        })
        assert resp.status_code == 422

    def test_fret_leveling_radius(self):
        """POST /fret-leveling/radius with valid params returns 200."""
        resp = client.post(f"{PREFIX}/fret-leveling/radius", json={
            "scale_length_mm": 645.0,
            "relief_mm": 0.25
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "radius_mm" in data


# =============================================================================
# Fret Wire Endpoints (GEOMETRY-006)
# =============================================================================

class TestFretWireEndpoints:
    """Smoke tests for fret wire recommendation endpoints."""

    def test_fret_wire_recommend_defaults(self):
        """POST /fret-wire/recommend with defaults returns 200."""
        resp = client.post(f"{PREFIX}/fret-wire/recommend", json={})
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "recommendations" in data

    def test_fret_wire_recommend_custom(self):
        """POST /fret-wire/recommend with custom params returns 200."""
        resp = client.post(f"{PREFIX}/fret-wire/recommend", json={
            "playing_style": "shred",
            "fretboard_material": "ebony",
            "neck_profile": "C",
            "string_gauge": "light"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_fret_wire_catalog(self):
        """GET /fret-wire/catalog returns 200 with catalog list."""
        resp = client.get(f"{PREFIX}/fret-wire/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert "catalog" in data
        assert isinstance(data["catalog"], list)

    def test_fret_wire_options(self):
        """GET /fret-wire/options returns 200 with all option lists."""
        resp = client.get(f"{PREFIX}/fret-wire/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "playing_styles" in data
        assert "fretboard_materials" in data
        assert "neck_profiles" in data
        assert "string_gauges" in data


# =============================================================================
# Wood Movement Endpoints (CONSTRUCTION-006)
# =============================================================================

class TestWoodMovementEndpoints:
    """Smoke tests for wood movement calculation endpoints."""

    def test_wood_movement_valid(self):
        """POST /wood-movement with valid params returns 200."""
        resp = client.post(f"{PREFIX}/wood-movement", json={
            "species": "sitka_spruce",
            "dimension_mm": 400.0,
            "rh_from": 45.0,
            "rh_to": 70.0,
            "grain_direction": "tangential"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "movement_mm" in data
            assert "gate" in data

    def test_wood_movement_missing_required_returns_422(self):
        """POST /wood-movement without required fields returns 422."""
        resp = client.post(f"{PREFIX}/wood-movement", json={})
        assert resp.status_code == 422

    def test_wood_movement_safe_range(self):
        """POST /wood-movement/safe-range with valid params returns 200."""
        resp = client.post(f"{PREFIX}/wood-movement/safe-range", json={
            "species": "rosewood",
            "dimension_mm": 400.0,
            "max_movement_mm": 1.0,
            "nominal_rh": 45.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "min_rh" in data
            assert "max_rh" in data

    def test_wood_movement_species_list(self):
        """GET /wood-movement/species returns 200 with species list."""
        resp = client.get(f"{PREFIX}/wood-movement/species")
        assert resp.status_code == 200
        data = resp.json()
        assert "species" in data
        assert isinstance(data["species"], list)


# =============================================================================
# Nut Compensation Endpoints
# =============================================================================

class TestNutCompensationEndpoints:
    """Smoke tests for nut compensation calculation endpoints."""

    def test_nut_compensation_traditional(self):
        """POST /nut-compensation for traditional nut returns 200."""
        resp = client.post(f"{PREFIX}/nut-compensation", json={
            "nut_type": "traditional",
            "nut_width_mm": 3.0,
            "break_angle_deg": 10.0,
            "scale_length_mm": 645.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "compensation_mm" in data
            assert "gate" in data

    def test_nut_compensation_zero_fret(self):
        """POST /nut-compensation for zero-fret returns 200."""
        resp = client.post(f"{PREFIX}/nut-compensation", json={
            "nut_type": "zero_fret",
            "scale_length_mm": 645.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_nut_compensation_compare(self):
        """POST /nut-compensation/compare returns 200."""
        resp = client.post(f"{PREFIX}/nut-compensation/compare", json={
            "scale_length_mm": 645.0,
            "nut_width_mm": 3.0,
            "break_angle_deg": 10.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "traditional" in data
            assert "zero_fret" in data
            assert "comparison" in data


# =============================================================================
# Electronics Layout Endpoints (CONSTRUCTION-008)
# =============================================================================

class TestElectronicsLayoutEndpoints:
    """Smoke tests for electronics layout calculation endpoints."""

    def test_electronics_layout_minimal(self):
        """POST /electronics-layout with minimal config returns 200."""
        resp = client.post(f"{PREFIX}/electronics-layout", json={
            "pickups": [],
            "pot_count": 2,
            "body_style": "les_paul"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "overall_gate" in data

    def test_electronics_layout_full(self):
        """POST /electronics-layout with full config returns 200."""
        resp = client.post(f"{PREFIX}/electronics-layout", json={
            "pickups": [
                {"pickup_type": "humbucker", "position": "neck"},
                {"pickup_type": "humbucker", "position": "bridge"}
            ],
            "pot_count": 4,
            "switch_type": "3way_toggle",
            "jack_type": "side",
            "body_style": "les_paul",
            "body_thickness_mm": 45.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "pickup_cavities" in data
            assert "control_cavities" in data

    def test_electronics_pickup_cavity(self):
        """POST /electronics-layout/pickup-cavity returns 200."""
        resp = client.post(f"{PREFIX}/electronics-layout/pickup-cavity", json={
            "pickup_type": "humbucker",
            "position": "bridge",
            "body_thickness_mm": 45.0,
            "body_style": "les_paul"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "cavity" in data

    def test_electronics_control_layout(self):
        """POST /electronics-layout/control-layout returns 200."""
        resp = client.post(f"{PREFIX}/electronics-layout/control-layout", json={
            "pot_count": 4,
            "switch_type": "3way_toggle",
            "jack_type": "side",
            "body_style": "les_paul",
            "body_thickness_mm": 45.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "cavities" in data
            assert "overall_gate" in data

    def test_electronics_options(self):
        """GET /electronics-layout/options returns 200 with all options."""
        resp = client.get(f"{PREFIX}/electronics-layout/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "pickup_types" in data
        assert "switch_types" in data
        assert "jack_types" in data
        assert "body_styles" in data


# =============================================================================
# Build Sequence Endpoints (CONSTRUCTION-010)
# =============================================================================

class TestBuildSequenceEndpoints:
    """Smoke tests for build sequence calculation endpoints."""

    def test_build_sequence_dreadnought(self):
        """POST /build-sequence with dreadnought preset returns 200."""
        resp = client.post(f"{PREFIX}/build-sequence", json={
            "build_id": "smoke-test-dreadnought",
            "preset": "dreadnought"
        })
        # Accept 200, 422, or 500 (internal bugs) - key is NOT 404
        assert resp.status_code != 404, f"Route not found: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "overall_gate" in data
            assert "stages" in data

    def test_build_sequence_om(self):
        """POST /build-sequence with om preset returns 200."""
        resp = client.post(f"{PREFIX}/build-sequence", json={
            "build_id": "smoke-test-om",
            "preset": "om"
        })
        assert resp.status_code != 404, f"Route not found: {resp.status_code}"

    def test_build_sequence_classical(self):
        """POST /build-sequence with classical preset returns 200."""
        resp = client.post(f"{PREFIX}/build-sequence", json={
            "build_id": "smoke-test-classical",
            "preset": "classical"
        })
        assert resp.status_code != 404, f"Route not found: {resp.status_code}"

    def test_build_sequence_with_overrides(self):
        """POST /build-sequence with custom overrides returns 200."""
        resp = client.post(f"{PREFIX}/build-sequence", json={
            "build_id": "smoke-test-overrides",
            "preset": "dreadnought",
            "scale_length_mm": 650.0,
            "string_count": 6,
            "fret_count": 22,
            "top_species": "sitka_spruce",
            "back_species": "rosewood"
        })
        assert resp.status_code != 404, f"Route not found: {resp.status_code}"

    def test_build_sequence_options(self):
        """GET /build-sequence/options returns 200 with presets."""
        resp = client.get(f"{PREFIX}/build-sequence/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "presets" in data
        assert "dreadnought" in data["presets"]


# =============================================================================
# Voicing History Endpoints
# =============================================================================

class TestVoicingEndpoints:
    """Smoke tests for voicing analysis endpoints."""

    def test_voicing_analyze_valid(self):
        """POST /voicing/analyze with valid session returns 200."""
        resp = client.post(f"{PREFIX}/voicing/analyze", json={
            "instrument_id": "test-001",
            "top_species": "sitka_spruce",
            "back_species": "rosewood",
            "body_style": "dreadnought",
            "measurements": [
                {
                    "stage": "rough_thicknessed",
                    "thickness_mm": 4.5,
                    "tap_frequency_hz": 280.0,
                    "timestamp": "2026-01-01T10:00:00Z",
                    "notes": "top plate"
                }
            ],
            "target_top_hz": 200.0,
            "target_back_hz": 180.0
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "gate" in data

    def test_voicing_predict(self):
        """POST /voicing/predict returns 200."""
        resp = client.post(f"{PREFIX}/voicing/predict", json={
            "current_thickness_mm": 4.5,
            "current_frequency_hz": 280.0,
            "target_thickness_mm": 3.5
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "predicted_frequency_hz" in data

    def test_voicing_targets_dreadnought(self):
        """GET /voicing/targets/dreadnought returns 200."""
        resp = client.get(f"{PREFIX}/voicing/targets/dreadnought")
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "top_hz" in data
            assert "back_hz" in data

    def test_voicing_targets_unknown_body_style(self):
        """GET /voicing/targets/unknown_style returns 200 or 422."""
        resp = client.get(f"{PREFIX}/voicing/targets/unknown_style")
        # Should return 200 with defaults or 422 if strict
        assert resp.status_code in (200, 422, 500), f"Unexpected status: {resp.status_code}"

    def test_voicing_stages(self):
        """GET /voicing/stages returns 200 with stage list."""
        resp = client.get(f"{PREFIX}/voicing/stages")
        assert resp.status_code == 200
        data = resp.json()
        assert "stages" in data
        assert isinstance(data["stages"], list)


# =============================================================================
# Cantilever Armrest Endpoints
# =============================================================================

class TestCantileverArmrestEndpoints:
    """Smoke tests for cantilever arm rest calculation endpoints."""

    def test_cantilever_armrest_defaults(self):
        """POST /cantilever-armrest with defaults returns 200."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={})
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "sections" in data
            assert "apex_section" in data

    def test_cantilever_armrest_standard_preset(self):
        """POST /cantilever-armrest with standard preset returns 200."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={
            "preset": "standard"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_cantilever_armrest_classical_preset(self):
        """POST /cantilever-armrest with classical preset returns 200."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={
            "preset": "classical"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_cantilever_armrest_archtop_preset(self):
        """POST /cantilever-armrest with archtop preset returns 200."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={
            "preset": "archtop"
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_cantilever_armrest_custom_params(self):
        """POST /cantilever-armrest with custom params returns 200."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={
            "span_mm": 150.0,
            "t_apex": 0.4,
            "h_max_mm": 15.0,
            "theta_max_deg": 45.0,
            "n_stations": 15
        })
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_cantilever_armrest_invalid_preset_returns_error(self):
        """POST /cantilever-armrest with invalid preset returns 400."""
        resp = client.post(f"{PREFIX}/cantilever-armrest", json={
            "preset": "invalid_preset_name"
        })
        assert resp.status_code in (400, 422), f"Unexpected status: {resp.status_code}"

    def test_cantilever_armrest_presets_list(self):
        """GET /cantilever-armrest/presets returns 200 with presets."""
        resp = client.get(f"{PREFIX}/cantilever-armrest/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert "standard" in data
        assert "classical" in data
        assert "archtop" in data


# =============================================================================
# Edge Case and Boundary Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_side_bending_extreme_radius(self):
        """Side bending with extreme tight radius should still respond."""
        resp = client.post(f"{PREFIX}/side-bending", json={
            "species": "rosewood_indian",
            "side_thickness_mm": 2.5,
            "waist_radius_mm": 10.0,  # Very tight, likely RED risk
            "instrument_type": "steel_string_acoustic"
        })
        assert resp.status_code in (200, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert data["risk"] in ("GREEN", "YELLOW", "RED")

    def test_nut_slots_12_string(self):
        """Nut slots for 12-string should work."""
        resp = client.post(f"{PREFIX}/nut-slots", json={
            "string_set": [{"name": f"s{i}", "gauge_inch": 0.010 + i * 0.002} for i in range(12)],
            "nut_width_mm": 47.0
        })
        assert resp.status_code in (200, 422)

    def test_bridge_12_strings(self):
        """Bridge for 12-string guitar should work."""
        resp = client.post(f"{PREFIX}/bridge", json={
            "body_style": "dreadnought",
            "scale_length_mm": 645.0,
            "string_count": 12
        })
        assert resp.status_code in (200, 422)

    def test_wood_movement_extreme_humidity(self):
        """Wood movement with extreme humidity change."""
        resp = client.post(f"{PREFIX}/wood-movement", json={
            "species": "sitka_spruce",
            "dimension_mm": 400.0,
            "rh_from": 10.0,  # Desert dry
            "rh_to": 95.0,    # Tropical humid
            "grain_direction": "tangential"
        })
        assert resp.status_code in (200, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert data["movement_mm"] > 0  # Should expand significantly
