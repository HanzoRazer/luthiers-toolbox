# tests/test_cnc_preflight_safety.py
"""
Tests for CNC Preflight Safety Checks (fail-closed mode).

These tests verify that unsafe CNC parameters are BLOCKED before
G-code generation can occur.
"""
import pytest

from app.safety.cnc_preflight import (
    validate_cnc_params,
    require_safe_cnc_params,
    calculate_chipload_safe,
    CNCPreflightError_ZeroRPM,
    CNCPreflightError_ZeroFlutes,
    CNCPreflightError_InvalidFeedRange,
    CNCPreflightError_InvalidDepth,
    CNCPreflightError_InvalidToolDiameter,
)


class TestValidateCNCParams:
    """Tests for validate_cnc_params function."""

    def test_valid_params_are_safe(self):
        """All valid parameters should pass."""
        result = validate_cnc_params(
            spindle_rpm=18000,
            flute_count=2,
            feed_rate_min=1000,
            feed_rate_max=3000,
            depth_of_cut=3.0,
            tool_diameter=6.35,
            stepover_percent=40,
        )
        assert result.safe is True
        assert len(result.errors) == 0

    def test_zero_rpm_blocked(self):
        """Zero RPM must be blocked - tool drags without cutting."""
        result = validate_cnc_params(spindle_rpm=0)
        assert result.safe is False
        assert any(e.code == "ZERO_RPM" for e in result.errors)

    def test_negative_rpm_blocked(self):
        """Negative RPM must be blocked."""
        result = validate_cnc_params(spindle_rpm=-1000)
        assert result.safe is False
        assert any(e.code == "ZERO_RPM" for e in result.errors)

    def test_zero_flutes_blocked(self):
        """Zero flutes must be blocked - division by zero in chipload."""
        result = validate_cnc_params(flute_count=0)
        assert result.safe is False
        assert any(e.code == "ZERO_FLUTES" for e in result.errors)

    def test_negative_flutes_blocked(self):
        """Negative flutes must be blocked."""
        result = validate_cnc_params(flute_count=-1)
        assert result.safe is False
        assert any(e.code == "ZERO_FLUTES" for e in result.errors)

    def test_min_feed_greater_than_max_blocked(self):
        """Min feed > max feed must be blocked - nonsensical range."""
        result = validate_cnc_params(
            feed_rate_min=3000,
            feed_rate_max=1000,
        )
        assert result.safe is False
        assert any(e.code == "INVALID_FEED_RANGE" for e in result.errors)

    def test_zero_depth_blocked(self):
        """Zero depth of cut must be blocked - no material removal."""
        result = validate_cnc_params(depth_of_cut=0)
        assert result.safe is False
        assert any(e.code == "INVALID_DEPTH" for e in result.errors)

    def test_negative_depth_blocked(self):
        """Negative depth must be blocked."""
        result = validate_cnc_params(depth_of_cut=-5.0)
        assert result.safe is False
        assert any(e.code == "INVALID_DEPTH" for e in result.errors)

    def test_zero_tool_diameter_blocked(self):
        """Zero tool diameter must be blocked - undefined geometry."""
        result = validate_cnc_params(tool_diameter=0)
        assert result.safe is False
        assert any(e.code == "INVALID_TOOL_DIAMETER" for e in result.errors)

    def test_zero_stepover_blocked(self):
        """Zero stepover must be blocked - infinite passes."""
        result = validate_cnc_params(stepover_percent=0)
        assert result.safe is False
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_over_100_stepover_blocked(self):
        """Over 100% stepover must be blocked - leaves uncut material."""
        result = validate_cnc_params(stepover_percent=150)
        assert result.safe is False
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_low_rpm_warning(self):
        """Very low RPM should produce warning but still pass."""
        result = validate_cnc_params(spindle_rpm=500)
        assert result.safe is True  # Warning, not error
        assert len(result.warnings) > 0
        assert "low rpm" in result.warnings[0].lower()

    def test_high_stepover_warning(self):
        """High stepover should produce warning but still pass."""
        result = validate_cnc_params(stepover_percent=85)
        assert result.safe is True  # Warning, not error
        assert len(result.warnings) > 0
        assert "stepover" in result.warnings[0].lower()

    def test_multiple_errors_collected(self):
        """Multiple errors should all be collected."""
        result = validate_cnc_params(
            spindle_rpm=0,
            flute_count=0,
            depth_of_cut=0,
        )
        assert result.safe is False
        assert len(result.errors) == 3

    def test_to_dict_format(self):
        """Result should serialize to proper dict format."""
        result = validate_cnc_params(spindle_rpm=0)
        d = result.to_dict()
        assert "safe" in d
        assert "errors" in d
        assert "warnings" in d
        assert d["safe"] is False
        assert len(d["errors"]) == 1
        assert d["errors"][0]["code"] == "ZERO_RPM"


class TestRequireSafeCNCParams:
    """Tests for require_safe_cnc_params function (raise on error)."""

    def test_valid_params_no_exception(self):
        """Valid parameters should not raise."""
        # Should not raise
        require_safe_cnc_params(
            spindle_rpm=18000,
            flute_count=2,
        )

    def test_zero_rpm_raises(self):
        """Zero RPM should raise CNCPreflightError_ZeroRPM."""
        with pytest.raises(CNCPreflightError_ZeroRPM) as exc_info:
            require_safe_cnc_params(spindle_rpm=0)
        assert "Zero RPM" in str(exc_info.value)

    def test_zero_flutes_raises(self):
        """Zero flutes should raise CNCPreflightError_ZeroFlutes."""
        with pytest.raises(CNCPreflightError_ZeroFlutes) as exc_info:
            require_safe_cnc_params(flute_count=0)
        assert "division-by-zero" in str(exc_info.value)

    def test_invalid_feed_range_raises(self):
        """Invalid feed range should raise CNCPreflightError_InvalidFeedRange."""
        with pytest.raises(CNCPreflightError_InvalidFeedRange):
            require_safe_cnc_params(
                feed_rate_min=3000,
                feed_rate_max=1000,
            )

    def test_invalid_depth_raises(self):
        """Invalid depth should raise CNCPreflightError_InvalidDepth."""
        with pytest.raises(CNCPreflightError_InvalidDepth):
            require_safe_cnc_params(depth_of_cut=0)

    def test_invalid_tool_diameter_raises(self):
        """Invalid tool diameter should raise CNCPreflightError_InvalidToolDiameter."""
        with pytest.raises(CNCPreflightError_InvalidToolDiameter):
            require_safe_cnc_params(tool_diameter=0)


class TestCalculateChiploadSafe:
    """Tests for calculate_chipload_safe function."""

    def test_valid_calculation(self):
        """Valid params should return correct chipload."""
        # chipload = feed / (rpm * flutes) = 2000 / (20000 * 2) = 0.05
        chipload = calculate_chipload_safe(
            feed_rate_mm_min=2000,
            spindle_rpm=20000,
            flute_count=2,
        )
        assert abs(chipload - 0.05) < 0.001

    def test_zero_rpm_raises(self):
        """Zero RPM should raise, not return 0.0."""
        with pytest.raises(CNCPreflightError_ZeroRPM):
            calculate_chipload_safe(
                feed_rate_mm_min=2000,
                spindle_rpm=0,
                flute_count=2,
            )

    def test_zero_flutes_raises(self):
        """Zero flutes should raise, not return 0.0."""
        with pytest.raises(CNCPreflightError_ZeroFlutes):
            calculate_chipload_safe(
                feed_rate_mm_min=2000,
                spindle_rpm=20000,
                flute_count=0,
            )


class TestFailClosedPhilosophy:
    """
    Tests verifying the fail-closed philosophy.

    The key difference from fail-open:
    - Fail-OPEN: Return a default value (0.0) when params are bad → dangerous G-code generated
    - Fail-CLOSED: Raise exception → no G-code generated
    """

    def test_chipload_original_fails_open(self):
        """Original chipload calculation fails open (returns 0.0)."""
        from app.cam.vcarve.chipload import calculate_chipload

        # Original returns 0.0 instead of raising
        result = calculate_chipload(
            feed_rate_mm_min=2000,
            spindle_rpm=0,  # Bad!
            flute_count=2,
        )
        assert result == 0.0  # Fails open - dangerous!

    def test_chipload_safe_fails_closed(self):
        """Safe chipload calculation fails closed (raises)."""
        with pytest.raises(CNCPreflightError_ZeroRPM):
            calculate_chipload_safe(
                feed_rate_mm_min=2000,
                spindle_rpm=0,  # Bad!
                flute_count=2,
            )
        # No return value - operation blocked
