# tests/test_neck_cnc_pipeline.py

"""
Tests for Neck CNC Pipeline (LP-GAP-03)

Validates the modular neck machining pipeline with full-scale station awareness.
"""

import pytest
import math

from app.cam.neck import (
    NeckPipeline,
    NeckPipelineConfig,
    NeckPipelineResult,
    TrussRodConfig,
    ProfileCarvingConfig,
    FretSlotConfig,
    NeckToolSpec,
    DEFAULT_NECK_TOOLS,
    TrussRodChannelGenerator,
    TrussRodResult,
    ProfileCarvingGenerator,
    ProfileCarvingResult,
    ProfileStation,
    FretSlotGenerator,
    FretSlotResult,
    FretSlotPosition,
)
from app.cam.neck.config import (
    NeckProfileType,
    MaterialType,
    create_lespaul_config,
    create_strat_config,
    create_classical_config,
)


# =============================================================================
# Configuration Tests
# =============================================================================

class TestNeckPipelineConfig:
    """Tests for NeckPipelineConfig."""

    def test_default_config_has_valid_scale_length(self):
        """Default config should have Les Paul scale length."""
        config = NeckPipelineConfig()
        assert config.scale_length_mm == pytest.approx(628.65, rel=0.01)

    def test_body_joint_calculated_from_fret_count(self):
        """Body joint Y should be calculated based on fret count."""
        config = NeckPipelineConfig(scale_length_mm=628.65, fret_count=22)
        # Body joint should be at 16th fret for 22-fret neck
        expected_y = 628.65 * (1 - (1 / (2 ** (16 / 12))))
        assert config.body_joint_y_mm == pytest.approx(expected_y, rel=0.01)

    def test_get_station_y_positions_extends_beyond_12_inches(self):
        """Station positions should extend beyond 12 inches (304.8mm)."""
        config = NeckPipelineConfig(scale_length_mm=628.65, fret_count=22)
        stations = config.get_station_y_positions()

        # Should have stations beyond 304.8mm (12")
        max_station = max(stations)
        assert max_station > 304.8, "Stations should extend beyond 12 inches"

    def test_station_count_scales_with_neck_length(self):
        """Longer necks should have more stations."""
        short_config = NeckPipelineConfig(scale_length_mm=500.0, fret_count=19)
        long_config = NeckPipelineConfig(scale_length_mm=700.0, fret_count=24)

        short_stations = short_config.get_station_y_positions()
        long_stations = long_config.get_station_y_positions()

        assert len(long_stations) > len(short_stations)

    def test_body_joint_included_in_stations(self):
        """Body joint position should always be in station list."""
        config = NeckPipelineConfig(scale_length_mm=628.65, fret_count=22)
        stations = config.get_station_y_positions()
        assert config.body_joint_y_mm in stations


class TestPresetConfigs:
    """Tests for preset configurations."""

    def test_lespaul_config(self):
        """Les Paul config should have correct specifications."""
        config = create_lespaul_config()
        assert config.scale_length_mm == pytest.approx(628.65, rel=0.01)
        assert config.fret_count == 22
        assert config.material == MaterialType.MAHOGANY

    def test_strat_config(self):
        """Strat config should have correct specifications."""
        config = create_strat_config()
        assert config.scale_length_mm == pytest.approx(647.7, rel=0.01)
        assert config.fret_count == 22
        assert config.material == MaterialType.MAPLE

    def test_classical_config(self):
        """Classical config should have correct specifications."""
        config = create_classical_config()
        assert config.scale_length_mm == pytest.approx(650.0, rel=0.01)
        assert config.fret_count == 19
        assert config.profile_type == NeckProfileType.D_SHAPE


# =============================================================================
# Fret Position Tests
# =============================================================================

class TestFretPositions:
    """Tests for 12-TET fret position calculations."""

    def test_fret_12_is_half_scale_length(self):
        """12th fret should be exactly half the scale length."""
        config = NeckPipelineConfig(scale_length_mm=628.65)
        fret_12_y = config._fret_position(12)
        assert fret_12_y == pytest.approx(628.65 / 2, rel=0.001)

    def test_fret_positions_are_increasing(self):
        """Each fret should be further from nut than previous."""
        config = NeckPipelineConfig(scale_length_mm=628.65, fret_count=22)
        positions = [config._fret_position(f) for f in range(1, 23)]

        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]

    def test_fret_0_is_at_nut(self):
        """Fret 0 (nut) should be at Y=0."""
        config = NeckPipelineConfig(scale_length_mm=628.65)
        assert config._fret_position(0) == 0.0


# =============================================================================
# Truss Rod Channel Tests
# =============================================================================

class TestTrussRodChannel:
    """Tests for truss rod channel generation."""

    def test_truss_rod_generates_gcode(self):
        """Truss rod generator should produce G-code."""
        config = NeckPipelineConfig()
        gen = TrussRodChannelGenerator(config)
        result = gen.generate()

        assert isinstance(result, TrussRodResult)
        assert len(result.gcode_lines) > 0

    def test_truss_rod_has_multi_pass_depth(self):
        """Deep channels should use multiple passes."""
        config = NeckPipelineConfig()
        config.truss_rod.depth_mm = 10.0  # Deep channel
        gen = TrussRodChannelGenerator(config)
        result = gen.generate()

        assert result.passes > 1

    def test_truss_rod_calculates_volume(self):
        """Result should include channel volume."""
        config = NeckPipelineConfig()
        gen = TrussRodChannelGenerator(config)
        result = gen.generate()

        expected_volume = (
            config.truss_rod.width_mm *
            config.truss_rod.depth_mm *
            config.truss_rod.length_mm
        )
        assert result.channel_volume_mm3 == pytest.approx(expected_volume, rel=0.01)

    def test_access_pocket_wider_than_channel(self):
        """Access pocket should only generate if wider than channel."""
        config = NeckPipelineConfig()
        config.truss_rod.access_pocket_width_mm = config.truss_rod.width_mm  # Same width
        gen = TrussRodChannelGenerator(config)
        lines = gen.generate_access_pocket()
        assert len(lines) == 0  # No access pocket if same width


# =============================================================================
# Profile Carving Tests
# =============================================================================

class TestProfileCarving:
    """Tests for profile carving generation."""

    def test_profile_generates_stations(self):
        """Profile generator should create stations."""
        config = NeckPipelineConfig()
        gen = ProfileCarvingGenerator(config)
        stations = gen.generate_stations()

        assert len(stations) > 0
        assert all(isinstance(s, ProfileStation) for s in stations)

    def test_stations_extend_full_scale(self):
        """Stations should extend to body joint (not limited to 12")."""
        config = create_lespaul_config()
        gen = ProfileCarvingGenerator(config)
        stations = gen.generate_stations()

        # Les Paul body joint is around 396mm (16th fret position)
        max_y = max(s.y_mm for s in stations)
        assert max_y > 304.8, "Stations must extend beyond 12 inches"

    def test_roughing_has_finish_allowance(self):
        """Roughing pass should leave finish allowance."""
        config = NeckPipelineConfig()
        gen = ProfileCarvingGenerator(config)
        result = gen.generate_roughing()

        # Check that finish allowance is mentioned in comments
        gcode = "\n".join(result.gcode_lines)
        assert "allowance" in gcode.lower()

    def test_finishing_removes_allowance(self):
        """Finishing pass should cut to final depth (no allowance)."""
        config = NeckPipelineConfig()
        gen = ProfileCarvingGenerator(config)

        rough_result = gen.generate_roughing()
        finish_result = gen.generate_finishing()

        # Both should have stations
        assert len(rough_result.stations) == len(finish_result.stations)

    def test_profile_width_tapers(self):
        """Neck width should taper from nut to heel."""
        config = NeckPipelineConfig(nut_width_mm=43.0, heel_width_mm=56.0)
        gen = ProfileCarvingGenerator(config)
        stations = gen.generate_stations()

        first_station = stations[0]
        last_station = stations[-1]

        assert first_station.width_mm < last_station.width_mm

    def test_compound_profile_blending(self):
        """Compound profile should blend V to C shape."""
        config = NeckPipelineConfig(profile_type=NeckProfileType.COMPOUND)
        gen = ProfileCarvingGenerator(config)
        stations = gen.generate_stations()

        # All stations should have profile points
        for station in stations:
            assert len(station.profile_points) > 0


# =============================================================================
# Fret Slot Tests
# =============================================================================

class TestFretSlots:
    """Tests for fret slot generation."""

    def test_fret_slots_generates_correct_count(self):
        """Should generate correct number of fret slots."""
        config = NeckPipelineConfig(fret_count=22)
        gen = FretSlotGenerator(config)
        result = gen.generate()

        assert len(result.slots) == 22

    def test_fret_slot_positions_are_correct(self):
        """Slot positions should match 12-TET formula."""
        config = NeckPipelineConfig(scale_length_mm=628.65, fret_count=22)
        gen = FretSlotGenerator(config)
        slots = gen.calculate_slot_positions()

        # Check 12th fret is at half scale length
        fret_12 = slots[11]  # 0-indexed
        assert fret_12.fret_number == 12
        assert fret_12.y_mm == pytest.approx(628.65 / 2, rel=0.001)

    def test_compound_radius_adjusts_depth(self):
        """Compound radius should vary slot depth."""
        config = NeckPipelineConfig()
        config.fret_slots.compound_radius = True
        config.fret_slots.radius_at_nut_mm = 254.0
        config.fret_slots.radius_at_heel_mm = 406.4

        gen = FretSlotGenerator(config)
        slots = gen.calculate_slot_positions()

        # Depths should vary (not all the same)
        depths = [s.slot_depth_mm for s in slots]
        assert len(set(round(d, 3) for d in depths)) > 1

    def test_flat_radius_has_constant_depth(self):
        """Non-compound radius should have constant slot depth."""
        config = NeckPipelineConfig()
        config.fret_slots.compound_radius = False

        gen = FretSlotGenerator(config)
        slots = gen.calculate_slot_positions()

        depths = [s.slot_depth_mm for s in slots]
        assert all(d == depths[0] for d in depths)


# =============================================================================
# Pipeline Orchestrator Tests
# =============================================================================

class TestNeckPipeline:
    """Tests for the pipeline orchestrator."""

    def test_pipeline_generates_complete_program(self):
        """Pipeline should generate complete G-code program."""
        config = create_lespaul_config()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        assert isinstance(result, NeckPipelineResult)
        assert len(result.gcode_lines) > 0
        assert result.total_operations > 0

    def test_pipeline_includes_all_operations(self):
        """Full pipeline should include all operations."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        assert result.truss_rod is not None
        assert result.profile_rough is not None
        assert result.profile_finish is not None
        assert result.fret_slots is not None
        assert result.total_operations == 4

    def test_pipeline_can_exclude_operations(self):
        """Operations can be individually disabled."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate(
            include_truss_rod=False,
            include_fret_slots=False,
        )

        assert result.truss_rod is None
        assert result.fret_slots is None
        assert result.profile_rough is not None
        assert result.total_operations == 2

    def test_pipeline_calculates_total_time(self):
        """Pipeline should calculate total cut time."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        assert result.total_cut_time_seconds > 0

        # Total should be sum of operations
        expected_time = 0
        if result.truss_rod:
            expected_time += result.truss_rod.cut_time_seconds
        if result.profile_rough:
            expected_time += result.profile_rough.cut_time_seconds
        if result.profile_finish:
            expected_time += result.profile_finish.cut_time_seconds
        if result.fret_slots:
            expected_time += result.fret_slots.cut_time_seconds

        assert result.total_cut_time_seconds == pytest.approx(expected_time, rel=0.01)

    def test_pipeline_gcode_has_header_footer(self):
        """G-code should have proper header and footer."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        gcode = result.get_gcode()
        assert "NECK CNC PIPELINE" in gcode
        assert "END OF PROGRAM" in gcode
        assert "M30" in gcode

    def test_pipeline_uses_vine05_coordinates(self):
        """G-code should reference VINE-05 coordinate system."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        gcode = result.get_gcode()
        assert "VINE-05" in gcode
        assert "Y=0 at nut" in gcode

    def test_single_operation_generation(self):
        """Can generate a single operation."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate_operation("fret_slots")

        assert result.fret_slots is not None
        assert result.truss_rod is None
        assert result.total_operations == 1

    def test_preview_stations(self):
        """Can preview stations without generating G-code."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        stations = pipeline.preview_stations()

        assert len(stations) > 0
        assert "y_mm" in stations[0]
        assert "width_mm" in stations[0]

    def test_preview_fret_positions(self):
        """Can preview fret positions without generating G-code."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        frets = pipeline.preview_fret_positions()

        assert len(frets) == config.fret_count
        assert "fret_number" in frets[0]
        assert "y_mm" in frets[0]


# =============================================================================
# Integration Tests
# =============================================================================

class TestNeckPipelineIntegration:
    """Integration tests for complete neck workflow."""

    def test_lespaul_full_pipeline(self):
        """Full Les Paul neck should generate valid G-code."""
        config = create_lespaul_config()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        gcode = result.get_gcode()

        # Should have G-code motion commands
        assert "G0" in gcode or "G00" in gcode
        assert "G1" in gcode or "G01" in gcode

        # Should have tool changes
        assert "T1" in gcode
        assert "M6" in gcode

        # Should have spindle commands
        assert "M3" in gcode
        assert "M5" in gcode

    def test_strat_full_pipeline(self):
        """Full Strat neck should generate valid G-code."""
        config = create_strat_config()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        assert result.total_operations == 4
        assert len(result.gcode_lines) > 100

    def test_result_serialization(self):
        """Result should serialize to dict."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        data = result.to_dict()

        assert "generated_at" in data
        assert "total_cut_time_seconds" in data
        assert "operations" in data
        assert "config" in data

    def test_tools_are_specified_correctly(self):
        """Each operation should use correct tool."""
        config = NeckPipelineConfig()
        pipeline = NeckPipeline(config)
        result = pipeline.generate()

        # Truss rod uses T2
        assert result.truss_rod.tool_number == 2

        # Profile rough uses T1
        assert result.profile_rough.tool_number == 1

        # Profile finish uses T3
        assert result.profile_finish.tool_number == 3

        # Fret slots use T4
        assert result.fret_slots.tool_number == 4
