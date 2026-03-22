"""
Tests for ACOUSTIC-005 build sequence acoustic chain.

4 test cases:
1. All 6 new stages instantiate without error
2. Stage with missing upstream → YELLOW not crash
3. default_acoustic_stages() returns 10 stages
4. Full chain runs end-to-end with mock spec
"""
import pytest

from app.calculators.build_sequence import (
    BuildSpec,
    BuildResult,
    BuildSequence,
    StageStatus,
    # Original stages
    StringTensionStage,
    BridgeGeometryStage,
    WoodMovementStage,
    FinishScheduleStage,
    # New acoustic chain stages
    NeckAngleStage,
    SaddleHeightStage,
    BreakAngleStage,
    SaddleForceStage,
    TopDeflectionStage,
    BraceSizingStage,
    # Standalone function
    default_acoustic_stages,
)


class TestNewStagesInstantiate:
    """Test 1: All 6 new stages instantiate without error."""

    def test_all_new_stages_instantiate(self):
        """All 6 new acoustic chain stages can be instantiated."""
        stages = [
            NeckAngleStage(),
            SaddleHeightStage(),
            BreakAngleStage(),
            SaddleForceStage(),
            TopDeflectionStage(),
            BraceSizingStage(),
        ]

        assert len(stages) == 6

        # Check each has a name
        expected_names = [
            "neck_angle",
            "saddle_height",
            "break_angle",
            "saddle_force",
            "top_deflection",
            "brace_sizing",
        ]
        for stage, expected_name in zip(stages, expected_names):
            assert stage.name == expected_name


class TestMissingUpstreamYellow:
    """Test 2: Stage with missing upstream returns YELLOW, not crash."""

    def test_saddle_height_missing_neck_angle(self):
        """SaddleHeightStage returns YELLOW when neck_angle is missing."""
        spec = BuildSpec()
        result = BuildResult(spec=spec)

        # result.neck_angle is None by default
        stage = SaddleHeightStage()
        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.SKIPPED
        assert stage_result.gate == "YELLOW"
        assert "Missing upstream" in stage_result.warnings[0]

    def test_break_angle_missing_saddle_height(self):
        """BreakAngleStage returns YELLOW when saddle_height is missing."""
        spec = BuildSpec()
        result = BuildResult(spec=spec)

        stage = BreakAngleStage()
        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.SKIPPED
        assert stage_result.gate == "YELLOW"
        assert "Missing upstream" in stage_result.warnings[0]

    def test_saddle_force_missing_break_angle(self):
        """SaddleForceStage returns YELLOW when break_angle is missing."""
        spec = BuildSpec()
        result = BuildResult(spec=spec)

        stage = SaddleForceStage()
        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.SKIPPED
        assert stage_result.gate == "YELLOW"
        assert "Missing upstream" in stage_result.warnings[0]

    def test_top_deflection_missing_saddle_force(self):
        """TopDeflectionStage returns YELLOW when saddle_force is missing."""
        spec = BuildSpec()
        result = BuildResult(spec=spec)

        stage = TopDeflectionStage()
        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.SKIPPED
        assert stage_result.gate == "YELLOW"
        assert "Missing upstream" in stage_result.warnings[0]

    def test_brace_sizing_missing_top_deflection(self):
        """BraceSizingStage returns YELLOW when top_deflection is missing."""
        spec = BuildSpec()
        result = BuildResult(spec=spec)

        stage = BraceSizingStage()
        stage_result = stage.run(spec, result)

        assert stage_result.status == StageStatus.SKIPPED
        assert stage_result.gate == "YELLOW"
        assert "Missing upstream" in stage_result.warnings[0]


class TestDefaultAcousticStages:
    """Test 3: default_acoustic_stages() returns 10 stages."""

    def test_default_acoustic_stages_returns_10(self):
        """default_acoustic_stages() returns exactly 10 stages."""
        stages = default_acoustic_stages()

        assert len(stages) == 10

    def test_default_acoustic_stages_order(self):
        """Stages are in correct dependency order."""
        stages = default_acoustic_stages()

        expected_order = [
            "string_tension",
            "bridge_geometry",
            "wood_movement",
            "finish_schedule",
            "neck_angle",
            "saddle_height",
            "break_angle",
            "saddle_force",
            "top_deflection",
            "brace_sizing",
        ]

        actual_order = [s.name for s in stages]
        assert actual_order == expected_order

    def test_build_sequence_default_stages_is_10(self):
        """BuildSequence.default_acoustic_stages() also returns 10 stages."""
        stages = BuildSequence.default_acoustic_stages()

        assert len(stages) == 10


class TestFullChainEndToEnd:
    """Test 4: Full chain runs end-to-end with mock spec."""

    def test_full_chain_runs_without_crash(self):
        """Full 10-stage chain runs without crashing."""
        spec = BuildSpec(
            scale_length_mm=647.7,
            target_action_mm_12th=2.5,
            string_gauges_inches=[0.012, 0.016, 0.024, 0.032, 0.042, 0.054],
            tuning_hz=[329.63, 246.94, 196.00, 146.83, 110.00, 82.41],
        )

        sequence = BuildSequence()
        result = sequence.run(spec)

        # Should have run all 10 stages
        assert len(result.stages) == 10

        # Check original stages completed
        assert result.stages["string_tension"].status == StageStatus.COMPLETED
        assert result.stages["bridge_geometry"].status == StageStatus.COMPLETED
        assert result.stages["wood_movement"].status == StageStatus.COMPLETED
        assert result.stages["finish_schedule"].status == StageStatus.COMPLETED

    def test_full_chain_acoustic_stages_run(self):
        """Acoustic chain stages run (may skip due to dependencies)."""
        spec = BuildSpec()
        sequence = BuildSequence()
        result = sequence.run(spec)

        # All acoustic chain stages should be in result
        acoustic_stages = [
            "neck_angle",
            "saddle_height",
            "break_angle",
            "saddle_force",
            "top_deflection",
            "brace_sizing",
        ]

        for stage_name in acoustic_stages:
            assert stage_name in result.stages
            # Should be either COMPLETED or SKIPPED (not FAILED)
            assert result.stages[stage_name].status in (
                StageStatus.COMPLETED,
                StageStatus.SKIPPED,
            )

    def test_overall_gate_propagates(self):
        """Overall gate propagates from individual stages."""
        spec = BuildSpec()
        sequence = BuildSequence()
        result = sequence.run(spec)

        # Overall gate should be one of GREEN, YELLOW, RED
        assert result.overall_gate in ("GREEN", "YELLOW", "RED")

        # If any stage is YELLOW, overall should be at least YELLOW
        has_yellow = any(
            s.gate == "YELLOW" for s in result.stages.values()
        )
        if has_yellow:
            assert result.overall_gate in ("YELLOW", "RED")
