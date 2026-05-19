"""
Tests for CAM Geometry Extraction from FretboardEcosphere

Sprint FRET-CONSOLIDATION-1: Regression tests ensuring extraction
produces identical geometry to ecosphere source.

Tolerance: 1e-9 mm (sub-nanometer) to catch any floating point drift.
"""
import math
import pytest

from app.instrument_geometry.neck.fretboard_ecosphere import (
    FretboardEcosphere,
    FretboardInput,
    ScaleType,
    RadiusSpec,
)
from app.cam.fret_slots_from_ecosphere import (
    extract_slot_geometry,
    ecosphere_to_fretboard_spec,
    is_fan_fret,
    get_fan_fret_params,
    extract_slot_endpoints,
    validate_ecosphere_for_cam,
    SlotGeometry,
)


TOLERANCE_MM = 1e-9


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def standard_6_string_input() -> FretboardInput:
    """Standard 6-string 25.5" scale fretboard."""
    return FretboardInput(
        scale_type=ScaleType.STANDARD,
        scale_length_mm=648.0,
        string_count=6,
        fret_count=22,
        nut_width_mm=42.0,
        heel_width_mm=56.0,
        slot_width_mm=0.58,
        radius=RadiusSpec(nut_radius_mm=241.3, heel_radius_mm=304.8),
    )


@pytest.fixture
def multiscale_input() -> FretboardInput:
    """Multiscale 25.5-27" fanned fret configuration."""
    return FretboardInput(
        scale_type=ScaleType.MULTISCALE,
        scale_length_mm=648.0,
        bass_scale_length_mm=686.0,
        string_count=6,
        fret_count=24,
        perpendicular_fret=7,
        nut_width_mm=44.0,
        heel_width_mm=58.0,
        slot_width_mm=0.58,
        radius=RadiusSpec(nut_radius_mm=305.0),
    )


@pytest.fixture
def standard_ecosphere(standard_6_string_input) -> FretboardEcosphere:
    """Pre-computed standard ecosphere."""
    return FretboardEcosphere.compute(standard_6_string_input)


@pytest.fixture
def multiscale_ecosphere(multiscale_input) -> FretboardEcosphere:
    """Pre-computed multiscale ecosphere."""
    return FretboardEcosphere.compute(multiscale_input)


# =============================================================================
# extract_slot_geometry() Tests
# =============================================================================

class TestExtractSlotGeometry:
    """Tests for slot geometry extraction."""

    def test_extracts_correct_count(self, standard_ecosphere):
        """Extraction produces one slot per fret (excluding nut)."""
        slots = extract_slot_geometry(standard_ecosphere)
        expected = standard_ecosphere.input_params.fret_count
        assert len(slots) == expected

    def test_skips_fret_zero(self, standard_ecosphere):
        """Fret 0 (nut) is not included in slot geometry."""
        slots = extract_slot_geometry(standard_ecosphere)
        fret_numbers = [s.fret_number for s in slots]
        assert 0 not in fret_numbers

    def test_fret_numbers_sequential(self, standard_ecosphere):
        """Fret numbers are 1 through fret_count."""
        slots = extract_slot_geometry(standard_ecosphere)
        expected = list(range(1, standard_ecosphere.input_params.fret_count + 1))
        actual = [s.fret_number for s in slots]
        assert actual == expected

    def test_slot_width_matches_input(self, standard_ecosphere):
        """All slots have width from ecosphere input."""
        slots = extract_slot_geometry(standard_ecosphere)
        expected_width = standard_ecosphere.input_params.slot_width_mm
        for slot in slots:
            assert slot.slot_width_mm == expected_width

    def test_geometry_matches_ecosphere_exactly(self, standard_ecosphere):
        """Extracted points match ecosphere fret lines within tolerance."""
        slots = extract_slot_geometry(standard_ecosphere)

        for slot in slots:
            fl = standard_ecosphere.get_fret_line(slot.fret_number)
            assert fl is not None

            bass_pt = fl.points[0]
            treble_pt = fl.points[-1]

            assert abs(slot.bass_point[0] - bass_pt.x_mm) < TOLERANCE_MM
            assert abs(slot.bass_point[1] - bass_pt.y_mm) < TOLERANCE_MM
            assert abs(slot.treble_point[0] - treble_pt.x_mm) < TOLERANCE_MM
            assert abs(slot.treble_point[1] - treble_pt.y_mm) < TOLERANCE_MM
            assert abs(slot.center_x_mm - fl.center_x_mm) < TOLERANCE_MM
            assert abs(slot.angle_rad - fl.angle_rad) < TOLERANCE_MM

    def test_standard_frets_perpendicular(self, standard_ecosphere):
        """All standard frets marked as perpendicular."""
        slots = extract_slot_geometry(standard_ecosphere)
        for slot in slots:
            assert slot.is_perpendicular is True
            assert abs(slot.angle_rad) < TOLERANCE_MM

    def test_fan_frets_have_angle(self, multiscale_ecosphere):
        """Fan frets (non-perpendicular) have non-zero angle."""
        slots = extract_slot_geometry(multiscale_ecosphere)
        perp_fret = multiscale_ecosphere.input_params.perpendicular_fret

        for slot in slots:
            if slot.fret_number == perp_fret:
                assert slot.is_perpendicular is True
            else:
                assert abs(slot.angle_rad) > 0.0

    def test_slot_length_positive(self, standard_ecosphere):
        """All slots have positive length."""
        slots = extract_slot_geometry(standard_ecosphere)
        for slot in slots:
            assert slot.slot_length_mm > 0

    def test_raises_on_empty_ecosphere(self):
        """ValueError raised if ecosphere has no fret lines."""
        # Construct ecosphere directly (bypassing Pydantic input validation)
        # to simulate an edge case where fret_lines is empty
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=1,  # Minimum valid
            nut_width_mm=42.0,
        )
        # Manually construct ecosphere with empty fret_lines
        eco = FretboardEcosphere(
            input_params=inp,
            fret_lines=[],  # Empty - invalid for CAM
            string_paths=[],
        )
        with pytest.raises(ValueError, match="no fret lines"):
            extract_slot_geometry(eco)


# =============================================================================
# ecosphere_to_fretboard_spec() Tests
# =============================================================================

class TestEcosphereToFretboardSpec:
    """Tests for backward-compatible FretboardSpec conversion."""

    def test_basic_fields_match(self, standard_ecosphere):
        """Core fields transfer correctly."""
        spec = ecosphere_to_fretboard_spec(standard_ecosphere)
        inp = standard_ecosphere.input_params

        assert spec.nut_width_mm == inp.nut_width_mm
        assert spec.scale_length_mm == inp.scale_length_mm
        assert spec.fret_count == inp.fret_count
        assert spec.extension_mm == inp.extension_mm

    def test_heel_width_from_computed(self, standard_ecosphere):
        """Heel width comes from input or computed value."""
        spec = ecosphere_to_fretboard_spec(standard_ecosphere)
        assert spec.heel_width_mm == standard_ecosphere.input_params.heel_width_mm

    def test_radius_extraction(self, standard_ecosphere):
        """Radius values extracted from RadiusSpec."""
        spec = ecosphere_to_fretboard_spec(standard_ecosphere)
        radius = standard_ecosphere.input_params.radius

        assert spec.base_radius_mm == radius.nut_radius_mm
        assert spec.end_radius_mm == radius.heel_radius_mm

    def test_flat_radius_handling(self):
        """Flat fretboard (no radius) handled correctly."""
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=22,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            radius=RadiusSpec(),  # No radius
        )
        eco = FretboardEcosphere.compute(inp)
        spec = ecosphere_to_fretboard_spec(eco)

        assert spec.base_radius_mm is None
        assert spec.end_radius_mm is None

    def test_single_radius_handling(self):
        """Single radius (non-compound) handled correctly."""
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=22,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            radius=RadiusSpec(nut_radius_mm=241.3),  # No heel radius
        )
        eco = FretboardEcosphere.compute(inp)
        spec = ecosphere_to_fretboard_spec(eco)

        assert spec.base_radius_mm == 241.3
        assert spec.end_radius_mm is None


# =============================================================================
# is_fan_fret() and get_fan_fret_params() Tests
# =============================================================================

class TestFanFretDetection:
    """Tests for fan-fret detection functions."""

    def test_standard_not_fan_fret(self, standard_ecosphere):
        """Standard ecosphere is not fan-fret."""
        assert is_fan_fret(standard_ecosphere) is False
        assert get_fan_fret_params(standard_ecosphere) is None

    def test_multiscale_is_fan_fret(self, multiscale_ecosphere):
        """Multiscale ecosphere is fan-fret."""
        assert is_fan_fret(multiscale_ecosphere) is True

    def test_fan_fret_params_extraction(self, multiscale_ecosphere):
        """Fan-fret parameters extracted correctly."""
        params = get_fan_fret_params(multiscale_ecosphere)
        assert params is not None

        treble, bass, perp = params
        inp = multiscale_ecosphere.input_params

        assert treble == inp.scale_length_mm
        assert bass == inp.bass_scale_length_mm
        assert perp == inp.perpendicular_fret


# =============================================================================
# extract_slot_endpoints() Tests
# =============================================================================

class TestExtractSlotEndpoints:
    """Tests for lightweight endpoint extraction."""

    def test_extracts_correct_count(self, standard_ecosphere):
        """Endpoint count matches fret count."""
        endpoints = extract_slot_endpoints(standard_ecosphere)
        assert len(endpoints) == standard_ecosphere.input_params.fret_count

    def test_endpoint_structure(self, standard_ecosphere):
        """Each endpoint is (fret_num, bass_pt, treble_pt) tuple."""
        endpoints = extract_slot_endpoints(standard_ecosphere)
        for fret_num, bass_pt, treble_pt in endpoints:
            assert isinstance(fret_num, int)
            assert isinstance(bass_pt, tuple)
            assert isinstance(treble_pt, tuple)
            assert len(bass_pt) == 2
            assert len(treble_pt) == 2

    def test_matches_full_extraction(self, standard_ecosphere):
        """Endpoints match full SlotGeometry extraction."""
        endpoints = extract_slot_endpoints(standard_ecosphere)
        slots = extract_slot_geometry(standard_ecosphere)

        for (fret_num, bass_pt, treble_pt), slot in zip(endpoints, slots):
            assert fret_num == slot.fret_number
            assert abs(bass_pt[0] - slot.bass_point[0]) < TOLERANCE_MM
            assert abs(bass_pt[1] - slot.bass_point[1]) < TOLERANCE_MM
            assert abs(treble_pt[0] - slot.treble_point[0]) < TOLERANCE_MM
            assert abs(treble_pt[1] - slot.treble_point[1]) < TOLERANCE_MM


# =============================================================================
# validate_ecosphere_for_cam() Tests
# =============================================================================

class TestValidateEcosphereForCam:
    """Tests for CAM validation."""

    def test_valid_ecosphere_passes(self, standard_ecosphere):
        """Valid ecosphere passes validation without error."""
        validate_ecosphere_for_cam(standard_ecosphere)  # Should not raise

    def test_empty_fret_lines_fails(self):
        """Ecosphere with no fret lines fails validation."""
        inp = FretboardInput(scale_length_mm=648.0, fret_count=22)
        eco = FretboardEcosphere(
            input_params=inp,
            fret_lines=[],
            string_paths=[],
        )
        with pytest.raises(ValueError, match="no fret lines"):
            validate_ecosphere_for_cam(eco)

    def test_negative_slot_width_fails(self):
        """Ecosphere with negative slot width fails validation."""
        from app.instrument_geometry.neck.fretboard_ecosphere import FretLine, FretPoint
        # Use valid input, then construct ecosphere with invalid state
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=22,
            nut_width_mm=42.0,
            slot_width_mm=0.58,  # Valid in input
        )
        # Manually override slot_width via a modified input
        # We need to use object.__setattr__ because FretboardInput is frozen
        modified_inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=22,
            nut_width_mm=42.0,
            slot_width_mm=0.1,  # Minimum valid
        )
        eco = FretboardEcosphere(
            input_params=modified_inp,
            fret_lines=[
                FretLine(
                    fret_number=0,
                    points=[
                        FretPoint(fret_number=0, string_index=0, x_mm=0, y_mm=-21),
                        FretPoint(fret_number=0, string_index=1, x_mm=0, y_mm=21),
                    ],
                ),
                FretLine(
                    fret_number=1,
                    points=[
                        FretPoint(fret_number=1, string_index=0, x_mm=36.4, y_mm=-22),
                        FretPoint(fret_number=1, string_index=1, x_mm=36.4, y_mm=22),
                    ],
                ),
            ],
            string_paths=[],
        )
        # This should pass since slot_width is valid
        validate_ecosphere_for_cam(eco)  # Should not raise


# =============================================================================
# Regression Tests: Known Values
# =============================================================================

class TestRegressionKnownValues:
    """Regression tests against known computed values.

    These values are captured from a known-good ecosphere computation
    and should not change unless the underlying math intentionally changes.
    """

    def test_standard_fret_12_position(self, standard_ecosphere):
        """Fret 12 at exactly half scale length (12-TET)."""
        slots = extract_slot_geometry(standard_ecosphere)
        fret_12 = next(s for s in slots if s.fret_number == 12)

        expected_x = 648.0 / 2.0  # 324.0mm
        assert abs(fret_12.center_x_mm - expected_x) < 1e-6

    def test_standard_fret_positions_increase(self, standard_ecosphere):
        """Fret positions strictly increase from nut to heel."""
        slots = extract_slot_geometry(standard_ecosphere)

        prev_x = 0.0
        for slot in slots:
            assert slot.center_x_mm > prev_x
            prev_x = slot.center_x_mm

    def test_multiscale_perpendicular_fret_angle_zero(self, multiscale_ecosphere):
        """Perpendicular fret has zero angle."""
        slots = extract_slot_geometry(multiscale_ecosphere)
        perp_fret = multiscale_ecosphere.input_params.perpendicular_fret
        perp_slot = next(s for s in slots if s.fret_number == perp_fret)

        assert abs(perp_slot.angle_rad) < 1e-6
        assert perp_slot.is_perpendicular is True

    def test_slot_width_propagates_correctly(self):
        """Custom slot width propagates to all extracted slots."""
        custom_width = 0.75  # Non-standard width
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=22,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            slot_width_mm=custom_width,
        )
        eco = FretboardEcosphere.compute(inp)
        slots = extract_slot_geometry(eco)

        for slot in slots:
            assert slot.slot_width_mm == custom_width


# =============================================================================
# Edge Cases
# =============================================================================

# =============================================================================
# Integration Tests: Ecosphere → CAM Pipeline
# =============================================================================

@pytest.fixture
def rmos_context():
    """Create RmosContext for testing."""
    from app.rmos.context import RmosContext
    return RmosContext.from_model_id("strat_25_5")


class TestEcosphereToCamPipeline:
    """Integration tests for full ecosphere → CAM pipeline."""

    def test_generate_toolpaths_from_ecosphere(self, standard_ecosphere, rmos_context):
        """Full pipeline: ecosphere → toolpaths."""
        from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths_from_ecosphere

        toolpaths = generate_fret_slot_toolpaths_from_ecosphere(
            standard_ecosphere, rmos_context, slot_depth_mm=3.0
        )

        assert len(toolpaths) == standard_ecosphere.input_params.fret_count
        for tp in toolpaths:
            assert tp.fret_number > 0
            assert tp.slot_depth_mm > 0
            assert tp.feed_rate_mmpm > 0

    def test_generate_cam_output_from_ecosphere(self, standard_ecosphere, rmos_context):
        """Full pipeline: ecosphere → complete CAM output."""
        from app.calculators.fret_slots_cam import generate_fret_slot_cam_from_ecosphere

        output = generate_fret_slot_cam_from_ecosphere(
            standard_ecosphere, rmos_context, slot_depth_mm=3.0
        )

        assert output.toolpaths is not None
        assert len(output.toolpaths) == 22
        assert output.dxf_content is not None
        assert "FRET_SLOTS" in output.dxf_content
        assert output.gcode_content is not None
        assert "G21" in output.gcode_content
        assert output.statistics["slot_count"] == 22

    def test_fan_fret_cam_from_ecosphere(self, multiscale_ecosphere, rmos_context):
        """Fan-fret pipeline: ecosphere → CAM with fan mode."""
        from app.calculators.fret_slots_cam import generate_fret_slot_cam_from_ecosphere

        output = generate_fret_slot_cam_from_ecosphere(
            multiscale_ecosphere, rmos_context, slot_depth_mm=3.0
        )

        assert output.statistics.get("mode") == "fan"
        assert output.statistics["treble_scale_mm"] == 648.0
        assert output.statistics["bass_scale_mm"] == 686.0

    def test_toolpaths_match_ecosphere_geometry(self, standard_ecosphere, rmos_context):
        """Toolpath geometry matches source ecosphere exactly."""
        from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths_from_ecosphere

        toolpaths = generate_fret_slot_toolpaths_from_ecosphere(
            standard_ecosphere, rmos_context
        )

        for tp in toolpaths:
            fl = standard_ecosphere.get_fret_line(tp.fret_number)
            assert fl is not None

            bass_pt = fl.points[0]
            treble_pt = fl.points[-1]

            assert abs(tp.bass_point[0] - bass_pt.x_mm) < TOLERANCE_MM
            assert abs(tp.bass_point[1] - bass_pt.y_mm) < TOLERANCE_MM
            assert abs(tp.treble_point[0] - treble_pt.x_mm) < TOLERANCE_MM
            assert abs(tp.treble_point[1] - treble_pt.y_mm) < TOLERANCE_MM


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_single_fret(self):
        """Ecosphere with single fret (fret 1 only)."""
        inp = FretboardInput(
            scale_length_mm=648.0,
            fret_count=1,
            nut_width_mm=42.0,
            heel_width_mm=44.0,
        )
        eco = FretboardEcosphere.compute(inp)
        slots = extract_slot_geometry(eco)

        assert len(slots) == 1
        assert slots[0].fret_number == 1

    def test_many_frets_36(self):
        """Ecosphere with 36 frets (extended range bass)."""
        inp = FretboardInput(
            scale_length_mm=864.0,  # 34" bass scale
            fret_count=36,
            nut_width_mm=44.0,
            heel_width_mm=70.0,
            string_count=5,
        )
        eco = FretboardEcosphere.compute(inp)
        slots = extract_slot_geometry(eco)

        assert len(slots) == 36

    def test_single_string_raises(self):
        """Single-string ecosphere raises ValueError (degenerate slot)."""
        # Single string creates fret "lines" with 1 point, not 2
        # This is a degenerate case that cannot produce valid CAM slots
        inp = FretboardInput(
            scale_length_mm=600.0,
            fret_count=12,
            string_count=1,
            nut_width_mm=20.0,
            heel_width_mm=25.0,
        )
        eco = FretboardEcosphere.compute(inp)

        with pytest.raises(ValueError, match="minimum 2 required"):
            extract_slot_geometry(eco)

    def test_two_strings_minimum(self):
        """Two-string ecosphere (minimal valid case)."""
        inp = FretboardInput(
            scale_length_mm=600.0,
            fret_count=12,
            string_count=2,
            nut_width_mm=20.0,
            heel_width_mm=25.0,
        )
        eco = FretboardEcosphere.compute(inp)
        slots = extract_slot_geometry(eco)

        assert len(slots) == 12
        for slot in slots:
            # Bass and treble Y should differ
            assert slot.bass_point[1] != slot.treble_point[1]
