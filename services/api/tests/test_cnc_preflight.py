"""
Tests for CNC Preflight Safety Checks.

These tests verify the fail-closed safety validation for CNC parameters.
"""
import pytest

from app.safety.cnc_preflight import (
    CNCPreflightError,
    CNCPreflightResult,
    CNCPreflightError_ZeroRPM,
    CNCPreflightError_ZeroFlutes,
    CNCPreflightError_InvalidFeedRange,
    CNCPreflightError_InvalidDepth,
    CNCPreflightError_InvalidToolDiameter,
    validate_cnc_params,
    require_safe_cnc_params,
    calculate_chipload_safe,
)


class TestCNCPreflightResult:
    """Tests for CNCPreflightResult dataclass."""

    def test_safe_result_is_truthy(self):
        result = CNCPreflightResult(safe=True)
        assert result
        assert bool(result) is True

    def test_unsafe_result_is_falsy(self):
        result = CNCPreflightResult(safe=False)
        assert not result
        assert bool(result) is False

    def test_to_dict_with_errors(self):
        error = CNCPreflightError(code="TEST", message="Test error")
        result = CNCPreflightResult(
            safe=False,
            errors=[error],
            warnings=["Test warning"]
        )
        d = result.to_dict()
        assert d["safe"] is False
        assert len(d["errors"]) == 1
        assert d["errors"][0]["code"] == "TEST"
        assert d["errors"][0]["message"] == "Test error"
        assert d["errors"][0]["severity"] == "CRITICAL"
        assert d["warnings"] == ["Test warning"]

    def test_to_dict_safe_empty(self):
        result = CNCPreflightResult(safe=True)
        d = result.to_dict()
        assert d["safe"] is True
        assert d["errors"] == []
        assert d["warnings"] == []


class TestValidateCNCParams:
    """Tests for validate_cnc_params function."""

    def test_all_valid_params_returns_safe(self):
        result = validate_cnc_params(
            spindle_rpm=18000,
            flute_count=2,
            feed_rate_min=1000,
            feed_rate_max=3000,
            depth_of_cut=3.0,
            tool_diameter=6.35,
            stepover_percent=40,
        )
        assert result.safe
        assert len(result.errors) == 0

    def test_zero_rpm_returns_error(self):
        result = validate_cnc_params(spindle_rpm=0)
        assert not result.safe
        assert any(e.code == "ZERO_RPM" for e in result.errors)

    def test_negative_rpm_returns_error(self):
        result = validate_cnc_params(spindle_rpm=-1000)
        assert not result.safe
        assert any(e.code == "ZERO_RPM" for e in result.errors)

    def test_low_rpm_returns_warning(self):
        result = validate_cnc_params(spindle_rpm=500)
        assert result.safe  # Still safe, just warning
        assert any("Very low RPM" in w for w in result.warnings)

    def test_zero_flutes_returns_error(self):
        result = validate_cnc_params(flute_count=0)
        assert not result.safe
        assert any(e.code == "ZERO_FLUTES" for e in result.errors)

    def test_negative_flutes_returns_error(self):
        result = validate_cnc_params(flute_count=-1)
        assert not result.safe
        assert any(e.code == "ZERO_FLUTES" for e in result.errors)

    def test_min_feed_greater_than_max_returns_error(self):
        result = validate_cnc_params(feed_rate_min=3000, feed_rate_max=1000)
        assert not result.safe
        assert any(e.code == "INVALID_FEED_RANGE" for e in result.errors)

    def test_zero_feed_min_returns_error(self):
        result = validate_cnc_params(feed_rate_min=0)
        assert not result.safe
        assert any(e.code == "ZERO_FEED_MIN" for e in result.errors)

    def test_zero_feed_max_returns_error(self):
        result = validate_cnc_params(feed_rate_max=0)
        assert not result.safe
        assert any(e.code == "ZERO_FEED_MAX" for e in result.errors)

    def test_zero_depth_returns_error(self):
        result = validate_cnc_params(depth_of_cut=0)
        assert not result.safe
        assert any(e.code == "INVALID_DEPTH" for e in result.errors)

    def test_negative_depth_returns_error(self):
        result = validate_cnc_params(depth_of_cut=-2.5)
        assert not result.safe
        assert any(e.code == "INVALID_DEPTH" for e in result.errors)

    def test_zero_tool_diameter_returns_error(self):
        result = validate_cnc_params(tool_diameter=0)
        assert not result.safe
        assert any(e.code == "INVALID_TOOL_DIAMETER" for e in result.errors)

    def test_negative_tool_diameter_returns_error(self):
        result = validate_cnc_params(tool_diameter=-6.35)
        assert not result.safe
        assert any(e.code == "INVALID_TOOL_DIAMETER" for e in result.errors)

    def test_zero_stepover_returns_error(self):
        result = validate_cnc_params(stepover_percent=0)
        assert not result.safe
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_over_100_stepover_returns_error(self):
        result = validate_cnc_params(stepover_percent=150)
        assert not result.safe
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_high_stepover_returns_warning(self):
        result = validate_cnc_params(stepover_percent=85)
        assert result.safe  # Still safe, just warning
        assert any("High stepover" in w for w in result.warnings)

    def test_none_params_are_skipped(self):
        result = validate_cnc_params()
        assert result.safe
        assert len(result.errors) == 0


class TestValidateCNCParamsRaiseOnError:
    """Tests for validate_cnc_params with raise_on_error=True."""

    def test_zero_rpm_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            validate_cnc_params(spindle_rpm=0, raise_on_error=True)

    def test_zero_flutes_raises(self):
        with pytest.raises(CNCPreflightError_ZeroFlutes):
            validate_cnc_params(flute_count=0, raise_on_error=True)

    def test_invalid_feed_range_raises(self):
        with pytest.raises(CNCPreflightError_InvalidFeedRange):
            validate_cnc_params(feed_rate_min=3000, feed_rate_max=1000, raise_on_error=True)

    def test_invalid_depth_raises(self):
        with pytest.raises(CNCPreflightError_InvalidDepth):
            validate_cnc_params(depth_of_cut=0, raise_on_error=True)

    def test_invalid_tool_diameter_raises(self):
        with pytest.raises(CNCPreflightError_InvalidToolDiameter):
            validate_cnc_params(tool_diameter=0, raise_on_error=True)


class TestRequireSafeCNCParams:
    """Tests for require_safe_cnc_params function."""

    def test_valid_params_does_not_raise(self):
        # Should not raise
        require_safe_cnc_params(
            spindle_rpm=18000,
            flute_count=2,
        )

    def test_invalid_params_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            require_safe_cnc_params(spindle_rpm=0)


class TestCalculateChiploadSafe:
    """Tests for calculate_chipload_safe function."""

    def test_valid_params_returns_chipload(self):
        chipload = calculate_chipload_safe(
            feed_rate_mm_min=1500,
            spindle_rpm=18000,
            flute_count=2,
        )
        # chipload = 1500 / (18000 * 2) = 0.0417 mm/tooth
        assert 0.04 < chipload < 0.05

    def test_zero_rpm_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            calculate_chipload_safe(
                feed_rate_mm_min=1500,
                spindle_rpm=0,
                flute_count=2,
            )

    def test_zero_flutes_raises(self):
        with pytest.raises(CNCPreflightError_ZeroFlutes):
            calculate_chipload_safe(
                feed_rate_mm_min=1500,
                spindle_rpm=18000,
                flute_count=0,
            )
