"""
Tests for Saw CAM Guard Module.

Tests safety guards for saw operations: rim speed, bite/tooth, heat, deflection, kickback.
"""
import math
import pytest

from app.rmos.saw_cam_guard import (
    SawCutOperation,
    RiskResult,
    compute_rim_speed_risk,
    compute_bite_risk,
    compute_saw_heat_risk,
    compute_saw_deflection_risk,
    compute_kickback_risk,
    run_saw_cam_guard,
)


class TestSawCutOperation:
    """Tests for SawCutOperation model."""

    def test_model_with_required_fields(self):
        """Should create operation with required fields."""
        op = SawCutOperation(
            op_id="op_1",
            blade_id="blade_100",
            material_id="hardwood_walnut",
            feed_mm_min=2000,
            rpm=3000,
            depth_mm=50,
            width_mm=3,
            cut_length_mm=300,
        )
        assert op.op_id == "op_1"
        assert op.blade_diameter_mm == 250.0  # default
        assert op.tooth_count == 60  # default

    def test_model_with_custom_blade_specs(self):
        """Should allow custom blade diameter and tooth count."""
        op = SawCutOperation(
            op_id="op_2",
            blade_id="blade_200",
            material_id="softwood_pine",
            feed_mm_min=3000,
            rpm=4000,
            depth_mm=40,
            width_mm=2.5,
            cut_length_mm=200,
            blade_diameter_mm=300,
            tooth_count=80,
        )
        assert op.blade_diameter_mm == 300
        assert op.tooth_count == 80


class TestComputeRimSpeedRisk:
    """Tests for compute_rim_speed_risk function."""

    def test_safe_rim_speed_no_message(self):
        """Safe rim speed should return no message."""
        result = compute_rim_speed_risk(
            blade_id="blade_1",
            rpm=3000,
            blade_diameter_mm=250,
            max_surface_speed_mpm=4000,
        )
        # rim_speed = π * 250 * 3000 / 1000 ≈ 2356 m/min (well under 4000)
        assert result.message is None
        assert result.value is not None
        assert result.value < 4000 * 0.9  # Below 90% threshold

    def test_high_rim_speed_warning(self):
        """Rim speed above 90% of max should produce warning."""
        # Target: rim_speed > 4000 * 0.9 = 3600, but < 4000 * 1.1 = 4400
        # π * d * rpm / 1000 = 3800 → d * rpm = 1209860 → rpm ~4850 for d=250
        result = compute_rim_speed_risk(
            blade_id="blade_2",
            rpm=4850,
            blade_diameter_mm=250,
            max_surface_speed_mpm=4000,
        )
        assert result.message is not None
        assert result.message.severity == "warning"
        assert result.message.code == "RIM_SPEED_HIGH"

    def test_exceeded_rim_speed_error(self):
        """Rim speed above 110% of max should produce error."""
        # Target: rim_speed > 4000 * 1.1 = 4400
        # π * 250 * rpm / 1000 = 4500 → rpm ≈ 5730
        result = compute_rim_speed_risk(
            blade_id="blade_3",
            rpm=6000,
            blade_diameter_mm=250,
            max_surface_speed_mpm=4000,
        )
        assert result.message is not None
        assert result.message.severity == "error"
        assert result.message.code == "RIM_SPEED_EXCEEDED"
        assert "blade_3" in str(result.message.context)

    def test_rim_speed_calculation_accuracy(self):
        """Should calculate rim speed correctly."""
        # π * 300 * 4000 / 1000 = 3769.9
        result = compute_rim_speed_risk(
            blade_id="blade_4",
            rpm=4000,
            blade_diameter_mm=300,
            max_surface_speed_mpm=5000,
        )
        expected = math.pi * 300 * 4000 / 1000
        assert abs(result.value - expected) < 0.1


class TestComputeBiteRisk:
    """Tests for compute_bite_risk function."""

    def test_normal_bite_no_message(self):
        """Normal bite per tooth should return no message."""
        # bite = 2000 / (3000 * 60) = 0.0111mm (within range)
        result = compute_bite_risk(
            blade_id="blade_1",
            feed_mm_min=2000,
            material_id="softwood_pine",
            rpm=3000,
            tooth_count=60,
        )
        assert result.message is None
        assert 0.01 < result.value < 0.25

    def test_high_bite_hardwood_warning(self):
        """High bite on hardwood should produce warning."""
        # bite = 10000 / (3000 * 60) = 0.0556mm
        # Max for hardwood is 0.15
        # Need bite > 0.15: feed / (3000 * 60) > 0.15 → feed > 27000
        result = compute_bite_risk(
            blade_id="blade_2",
            feed_mm_min=30000,
            material_id="hardwood_walnut",
            rpm=3000,
            tooth_count=60,
        )
        assert result.message is not None
        assert result.message.severity == "warning"
        assert result.message.code == "BITE_PER_TOOTH_HIGH"

    def test_high_bite_softwood_warning(self):
        """High bite on softwood should produce warning at higher threshold."""
        # Max for softwood is 0.25
        # feed / (3000 * 60) > 0.25 → feed > 45000
        result = compute_bite_risk(
            blade_id="blade_3",
            feed_mm_min=50000,
            material_id="softwood_pine",
            rpm=3000,
            tooth_count=60,
        )
        assert result.message is not None
        assert result.message.code == "BITE_PER_TOOTH_HIGH"

    def test_low_bite_info(self):
        """Very low bite should produce info message about rubbing."""
        # bite = 100 / (3000 * 60) = 0.00056mm < 0.01
        result = compute_bite_risk(
            blade_id="blade_4",
            feed_mm_min=100,
            material_id="softwood",
            rpm=3000,
            tooth_count=60,
        )
        assert result.message is not None
        assert result.message.severity == "info"
        assert result.message.code == "BITE_PER_TOOTH_LOW"

    def test_zero_rpm_guard(self):
        """Zero RPM should not crash (division guard)."""
        result = compute_bite_risk(
            blade_id="blade_5",
            feed_mm_min=2000,
            material_id="softwood",
            rpm=0,
            tooth_count=60,
        )
        # Should handle gracefully (bite = 999)
        assert result.value == 999


class TestComputeSawHeatRisk:
    """Tests for compute_saw_heat_risk function."""

    def test_short_cut_no_warning(self):
        """Short cut should have no heat warning."""
        result = compute_saw_heat_risk(
            blade_id="blade_1",
            material_id="hardwood",
            cut_length_mm=300,
            heat_threshold_mm=500,
        )
        assert result.message is None
        assert result.value == 300

    def test_long_cut_warning(self):
        """Long cut should produce heat warning."""
        result = compute_saw_heat_risk(
            blade_id="blade_2",
            material_id="hardwood_ebony",
            cut_length_mm=600,
            heat_threshold_mm=500,
        )
        assert result.message is not None
        assert result.message.severity == "warning"
        assert result.message.code == "SAW_HEAT_BUILDUP"
        assert "600" in result.message.message

    def test_custom_threshold(self):
        """Should respect custom heat threshold."""
        result = compute_saw_heat_risk(
            blade_id="blade_3",
            material_id="softwood",
            cut_length_mm=250,
            heat_threshold_mm=200,  # Lower threshold
        )
        assert result.message is not None
        assert result.message.code == "SAW_HEAT_BUILDUP"


class TestComputeSawDeflectionRisk:
    """Tests for compute_saw_deflection_risk function."""

    def test_shallow_cut_no_warning(self):
        """Shallow cut should have no deflection warning."""
        # depth_ratio = 50 / 250 = 0.2 (under 0.4)
        result = compute_saw_deflection_risk(
            blade_id="blade_1",
            depth_mm=50,
            blade_diameter_mm=250,
            max_depth_ratio=0.4,
        )
        assert result.message is None
        assert result.value == 0.2

    def test_deep_cut_warning(self):
        """Deep cut should produce deflection warning."""
        # depth_ratio = 120 / 250 = 0.48 (over 0.4)
        result = compute_saw_deflection_risk(
            blade_id="blade_2",
            depth_mm=120,
            blade_diameter_mm=250,
            max_depth_ratio=0.4,
        )
        assert result.message is not None
        assert result.message.severity == "warning"
        assert result.message.code == "SAW_DEPTH_HIGH"
        assert "48%" in result.message.message

    def test_zero_diameter_guard(self):
        """Zero blade diameter should not crash."""
        result = compute_saw_deflection_risk(
            blade_id="blade_3",
            depth_mm=50,
            blade_diameter_mm=0,
            max_depth_ratio=0.4,
        )
        # Should handle gracefully (depth_ratio = 999)
        assert result.value == 999
        assert result.message is not None


class TestComputeKickbackRisk:
    """Tests for compute_kickback_risk function."""

    def test_moderate_feed_no_warning(self):
        """Moderate feed rate should have no kickback warning."""
        result = compute_kickback_risk(
            blade_id="blade_1",
            material_id="softwood_pine",
            feed_mm_min=3000,
            feed_threshold_mm_min=5000,
        )
        assert result.message is None
        assert result.value == 3000

    def test_high_feed_softwood_warning(self):
        """High feed on softwood should produce warning."""
        result = compute_kickback_risk(
            blade_id="blade_2",
            material_id="softwood",
            feed_mm_min=6000,
            feed_threshold_mm_min=5000,
        )
        assert result.message is not None
        assert result.message.severity == "warning"
        assert result.message.code == "KICKBACK_RISK"

    def test_high_feed_dense_wood_lower_threshold(self):
        """Dense wood should have lower kickback threshold (70%)."""
        # Threshold for dense wood = 5000 * 0.7 = 3500
        result = compute_kickback_risk(
            blade_id="blade_3",
            material_id="hardwood_ebony",  # "hard" in name triggers dense
            feed_mm_min=4000,
            feed_threshold_mm_min=5000,
        )
        assert result.message is not None
        assert result.message.code == "KICKBACK_RISK"

    def test_dense_woods_detection(self):
        """Should detect various dense wood types."""
        dense_woods = ["hardwood_maple", "ebony_african", "rosewood_brazilian"]
        for wood in dense_woods:
            result = compute_kickback_risk(
                blade_id="blade_4",
                material_id=wood,
                feed_mm_min=4000,
                feed_threshold_mm_min=5000,
            )
            # All should trigger at 4000 mm/min (above 3500 threshold)
            assert result.message is not None, f"Should warn for {wood}"


class TestRunSawCamGuard:
    """Tests for run_saw_cam_guard function."""

    def test_safe_operation_no_messages(self):
        """Safe operation should produce no messages."""
        op = SawCutOperation(
            op_id="safe_op",
            blade_id="blade_safe",
            material_id="softwood_pine",
            feed_mm_min=2000,
            rpm=3000,
            depth_mm=50,
            width_mm=3,
            cut_length_mm=200,
            blade_diameter_mm=250,
            tooth_count=60,
        )
        messages = run_saw_cam_guard(operations=[op])
        assert messages == []

    def test_multiple_operations(self):
        """Should check all operations."""
        ops = [
            SawCutOperation(
                op_id="op_1",
                blade_id="blade_1",
                material_id="softwood",
                feed_mm_min=2000,
                rpm=3000,
                depth_mm=50,
                width_mm=3,
                cut_length_mm=200,
            ),
            SawCutOperation(
                op_id="op_2",
                blade_id="blade_2",
                material_id="hardwood",
                feed_mm_min=50000,  # High bite
                rpm=3000,
                depth_mm=50,
                width_mm=3,
                cut_length_mm=200,
            ),
        ]
        messages = run_saw_cam_guard(operations=ops)
        # Should have at least one message for op_2's high bite
        assert len(messages) >= 1
        assert any(m.context.get("op_id") == "op_2" for m in messages)

    def test_op_id_in_message_context(self):
        """Messages should include op_id in context."""
        op = SawCutOperation(
            op_id="traced_op",
            blade_id="blade_x",
            material_id="hardwood",
            feed_mm_min=50000,  # Will trigger bite warning
            rpm=3000,
            depth_mm=50,
            width_mm=3,
            cut_length_mm=200,
        )
        messages = run_saw_cam_guard(operations=[op])
        assert len(messages) >= 1
        for msg in messages:
            assert msg.context.get("op_id") == "traced_op"

    def test_all_risks_checked(self):
        """Should check all five risk types."""
        # Design operation that triggers all risks
        op = SawCutOperation(
            op_id="risky_op",
            blade_id="blade_risky",
            material_id="hardwood_ebony",  # Dense
            feed_mm_min=8000,  # High bite & kickback
            rpm=6000,  # High rim speed
            depth_mm=120,  # Deep cut (deflection)
            width_mm=3,
            cut_length_mm=800,  # Long cut (heat)
            blade_diameter_mm=250,
            tooth_count=60,
        )
        messages = run_saw_cam_guard(operations=[op])

        codes = {m.code for m in messages}
        # Should have multiple warnings
        assert len(messages) >= 3
        # Check for expected codes
        assert "RIM_SPEED_EXCEEDED" in codes or "RIM_SPEED_HIGH" in codes
        assert "SAW_HEAT_BUILDUP" in codes
        assert "SAW_DEPTH_HIGH" in codes

    def test_empty_operations_list(self):
        """Empty operations list should return empty messages."""
        messages = run_saw_cam_guard(operations=[])
        assert messages == []


class TestRiskResult:
    """Tests for RiskResult model."""

    def test_risk_result_with_message(self):
        """Should store value and message."""
        from app.rmos.messages import as_warning

        msg = as_warning("TEST_CODE", "Test message")
        result = RiskResult(value=42.0, message=msg)
        assert result.value == 42.0
        assert result.message.code == "TEST_CODE"

    def test_risk_result_no_message(self):
        """Should allow None message for safe results."""
        result = RiskResult(value=10.0, message=None)
        assert result.value == 10.0
        assert result.message is None
