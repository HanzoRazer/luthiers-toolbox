"""
Tests for build_sequence.py — CONSTRUCTION-010.

Validates build sequence composition:
- BuildSpec configuration
- Stage execution and dependencies
- Result accumulation
- Factory functions
"""

import pytest

from app.calculators.build_sequence import (
    BuildSpec,
    BuildResult,
    BuildSequence,
    StageResult,
    StageStatus,
    InstrumentType,
    BodyStyle,
    NeckJointType,
    StringTensionStage,
    BridgeGeometryStage,
    WoodMovementStage,
    FinishScheduleStage,
    create_dreadnought_spec,
    create_om_spec,
    create_classical_spec,
    run_build_sequence,
)


class TestBuildSpec:
    """Test BuildSpec configuration."""

    def test_default_spec_values(self):
        """Default spec should have reasonable acoustic guitar values."""
        spec = BuildSpec()

        assert spec.instrument_type == InstrumentType.ACOUSTIC_STEEL
        assert spec.body_style == BodyStyle.DREADNOUGHT
        assert spec.scale_length_mm == 647.7
        assert spec.string_count == 6
        assert len(spec.string_gauges_inches) == 6
        assert len(spec.tuning_hz) == 6

    def test_spec_to_dict(self):
        """to_dict should serialize all fields."""
        spec = BuildSpec(build_id="test-001")
        d = spec.to_dict()

        assert d["build_id"] == "test-001"
        assert d["instrument_type"] == "acoustic_steel"
        assert d["body_style"] == "dreadnought"
        assert "scale_length_mm" in d
        assert "string_gauges_inches" in d

    def test_spec_custom_values(self):
        """Spec should accept custom values."""
        spec = BuildSpec(
            build_id="custom-001",
            scale_length_mm=628.65,  # Les Paul
            fret_count=22,
            top_species="sitka_spruce",
            finish_type="nitro",
        )

        assert spec.scale_length_mm == 628.65
        assert spec.fret_count == 22
        assert spec.top_species == "sitka_spruce"


class TestFactoryFunctions:
    """Test spec factory functions."""

    def test_create_dreadnought_spec(self):
        """Dreadnought spec should have correct dimensions."""
        spec = create_dreadnought_spec("dn-001")

        assert spec.build_id == "dn-001"
        assert spec.body_style == BodyStyle.DREADNOUGHT
        assert spec.scale_length_mm == 647.7
        assert spec.target_air_resonance_hz == 98.0

    def test_create_om_spec(self):
        """OM spec should have smaller body dimensions."""
        spec = create_om_spec("om-001")

        assert spec.body_style == BodyStyle.OM_000
        assert spec.scale_length_mm < 647.7  # Shorter than dreadnought
        assert spec.target_air_resonance_hz > 98.0  # Higher for smaller body

    def test_create_classical_spec(self):
        """Classical spec should have nylon guitar settings."""
        spec = create_classical_spec("cl-001")

        assert spec.instrument_type == InstrumentType.ACOUSTIC_NYLON
        assert spec.body_style == BodyStyle.CLASSICAL
        assert spec.nut_width_mm == 52.0  # Wider nut
        assert spec.fret_count == 19
        assert spec.bracing_pattern == "fan"
        assert spec.finish_type == "french_polish"


class TestBuildStages:
    """Test individual build stages."""

    def test_string_tension_stage(self):
        """String tension stage should compute tension."""
        spec = create_dreadnought_spec()
        result = BuildResult(spec=spec)
        stage = StringTensionStage()

        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.COMPLETED
        assert stage_result.stage_name == "string_tension"
        assert result.string_tension is not None
        assert result.string_tension.total_tension_n > 0  # Tension in Newtons

    def test_bridge_geometry_stage(self):
        """Bridge geometry stage should compute bridge dims."""
        spec = create_dreadnought_spec()
        result = BuildResult(spec=spec)
        stage = BridgeGeometryStage()

        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.COMPLETED
        assert result.bridge_geometry is not None
        assert result.bridge_geometry.bridge_length_mm > 0

    def test_wood_movement_stage(self):
        """Wood movement stage should compute expansion/contraction."""
        spec = create_dreadnought_spec()
        spec.build_rh_pct = 45.0
        spec.target_rh_pct = 55.0  # Humid environment
        result = BuildResult(spec=spec)
        stage = WoodMovementStage()

        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.COMPLETED
        assert result.wood_movement is not None
        # Should expand in higher humidity
        assert result.wood_movement.movement_mm > 0

    def test_finish_schedule_stage(self):
        """Finish schedule stage should compute finish plan."""
        spec = create_dreadnought_spec()
        spec.finish_type = "nitro"
        spec.back_species = "indian_rosewood"
        result = BuildResult(spec=spec)
        stage = FinishScheduleStage()

        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.COMPLETED
        assert result.finish_schedule is not None
        assert result.finish_schedule.total_coats > 0


class TestBuildSequence:
    """Test build sequence orchestration."""

    def test_default_stages(self):
        """Default sequence should include core stages."""
        sequence = BuildSequence()

        stage_names = [s.name for s in sequence.stages]
        assert "string_tension" in stage_names
        assert "bridge_geometry" in stage_names
        assert "finish_schedule" in stage_names

    def test_run_sequence(self):
        """Running sequence should execute all stages."""
        spec = create_dreadnought_spec("test-run")
        sequence = BuildSequence()

        result = sequence.run(spec)

        assert result.spec.build_id == "test-run"
        assert "string_tension" in result.stages
        assert "bridge_geometry" in result.stages
        assert "finish_schedule" in result.stages

        # All stages should complete
        for stage_name, stage_result in result.stages.items():
            assert stage_result.status == StageStatus.COMPLETED, \
                f"Stage {stage_name} did not complete"

    def test_validate_spec_valid(self):
        """Valid spec should pass validation."""
        spec = create_dreadnought_spec()
        sequence = BuildSequence()

        errors = sequence.validate_spec(spec)

        assert len(errors) == 0

    def test_validate_spec_mismatched_strings(self):
        """Mismatched string count should fail validation."""
        spec = create_dreadnought_spec()
        spec.string_count = 7  # Mismatch with 6 gauges

        sequence = BuildSequence()
        errors = sequence.validate_spec(spec)

        assert len(errors) > 0
        assert any("String count" in e for e in errors)

    def test_validate_spec_invalid_scale(self):
        """Zero scale length should fail validation."""
        spec = create_dreadnought_spec()
        spec.scale_length_mm = 0

        sequence = BuildSequence()
        errors = sequence.validate_spec(spec)

        assert len(errors) > 0
        assert any("Scale length" in e for e in errors)


class TestBuildResult:
    """Test build result accumulation."""

    def test_result_to_dict(self):
        """Result should serialize to dict."""
        spec = create_dreadnought_spec("dict-test")
        result = run_build_sequence(spec)

        d = result.to_dict()

        assert "spec" in d
        assert "stages" in d
        assert "overall_gate" in d
        assert d["spec"]["build_id"] == "dict-test"

    def test_result_accumulates_warnings(self):
        """Result should collect warnings from stages."""
        spec = create_dreadnought_spec()
        result = BuildResult(spec=spec)

        # Add stage with warning
        result.add_stage(StageResult(
            stage_name="test_stage",
            status=StageStatus.COMPLETED,
            warnings=["Test warning"],
            gate="YELLOW",
        ))

        assert "Test warning" in result.warnings
        assert result.overall_gate == "YELLOW"

    def test_result_gate_degrades(self):
        """Overall gate should degrade on RED stage."""
        spec = create_dreadnought_spec()
        result = BuildResult(spec=spec)

        # Add GREEN stage
        result.add_stage(StageResult(
            stage_name="green_stage",
            status=StageStatus.COMPLETED,
            gate="GREEN",
        ))
        assert result.overall_gate == "GREEN"

        # Add RED stage
        result.add_stage(StageResult(
            stage_name="red_stage",
            status=StageStatus.FAILED,
            gate="RED",
        ))
        assert result.overall_gate == "RED"


class TestConvenienceFunction:
    """Test run_build_sequence convenience function."""

    def test_run_build_sequence(self):
        """run_build_sequence should execute full sequence."""
        spec = create_dreadnought_spec("conv-test")

        result = run_build_sequence(spec)

        assert result.overall_gate in ["GREEN", "YELLOW", "RED"]
        assert len(result.stages) > 0

    def test_run_build_sequence_with_invalid_spec(self):
        """Invalid spec should return RED result."""
        spec = create_dreadnought_spec()
        spec.scale_length_mm = 0  # Invalid

        result = run_build_sequence(spec)

        assert result.overall_gate == "RED"
        assert len(result.errors) > 0


class TestCrossStageIntegration:
    """Test data flow between stages."""

    def test_tension_informs_later_stages(self):
        """String tension result should be available for later stages."""
        spec = create_dreadnought_spec()
        result = run_build_sequence(spec)

        # Verify tension is populated
        assert result.string_tension is not None

        # Later stages could reference this (future implementation)
        # For now, just verify it's accessible (convert N to kg)
        total_tension_kg = result.string_tension.total_tension_n / 9.81
        assert total_tension_kg > 50  # Typical acoustic tension

    def test_full_sequence_classical(self):
        """Full sequence on classical should use correct settings."""
        spec = create_classical_spec("classical-full")

        result = run_build_sequence(spec)

        # Should use French polish for classical
        assert result.finish_schedule is not None
        assert result.finish_schedule.finish_type == "french_polish"

        # Should have high coat count
        assert result.finish_schedule.total_coats >= 10
