"""
Minimal coverage tests for app.safety.cnc_preflight.

Target: bring cnc_preflight.py from 0% to >60% coverage.
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


class TestCNCPreflightDataclasses:
    """Test dataclass behavior."""

    def test_preflight_error_creation(self):
        err = CNCPreflightError(code="TEST", message="test msg")
        assert err.code == "TEST"
        assert err.message == "test msg"
        assert err.severity == "CRITICAL"

    def test_preflight_result_safe(self):
        result = CNCPreflightResult(safe=True)
        assert result.safe is True
        assert bool(result) is True
        assert result.errors == []

    def test_preflight_result_unsafe(self):
        result = CNCPreflightResult(
            safe=False,
            errors=[CNCPreflightError(code="X", message="Y")],
            warnings=["warn1"],
        )
        assert result.safe is False
        assert bool(result) is False
        assert len(result.errors) == 1

    def test_preflight_result_to_dict(self):
        result = CNCPreflightResult(
            safe=False,
            errors=[CNCPreflightError(code="X", message="Y", severity="CRITICAL")],
            warnings=["warn1"],
        )
        d = result.to_dict()
        assert d["safe"] is False
        assert d["errors"][0]["code"] == "X"
        assert d["warnings"] == ["warn1"]


class TestValidateCNCParams:
    """Test validate_cnc_params function."""

    def test_all_valid_params(self):
        result = validate_cnc_params(
            spindle_rpm=18000,
            flute_count=2,
            feed_rate_min=500,
            feed_rate_max=2000,
            depth_of_cut=3.0,
            tool_diameter=6.0,
            stepover_percent=40,
        )
        assert result.safe is True
        assert result is not None

    def test_zero_rpm_error(self):
        result = validate_cnc_params(spindle_rpm=0)
        assert result.safe is False
        assert any(e.code == "ZERO_RPM" for e in result.errors)

    def test_low_rpm_warning(self):
        result = validate_cnc_params(spindle_rpm=500)
        assert result.safe is True
        assert len(result.warnings) >= 1

    def test_zero_flutes_error(self):
        result = validate_cnc_params(flute_count=0)
        assert result.safe is False
        assert any(e.code == "ZERO_FLUTES" for e in result.errors)

    def test_invalid_feed_range(self):
        result = validate_cnc_params(feed_rate_min=2000, feed_rate_max=500)
        assert result.safe is False
        assert any(e.code == "INVALID_FEED_RANGE" for e in result.errors)

    def test_zero_feed_min(self):
        result = validate_cnc_params(feed_rate_min=0)
        assert result.safe is False
        assert any(e.code == "ZERO_FEED_MIN" for e in result.errors)

    def test_zero_feed_max(self):
        result = validate_cnc_params(feed_rate_max=0)
        assert result.safe is False
        assert any(e.code == "ZERO_FEED_MAX" for e in result.errors)

    def test_invalid_depth(self):
        result = validate_cnc_params(depth_of_cut=-1)
        assert result.safe is False
        assert any(e.code == "INVALID_DEPTH" for e in result.errors)

    def test_invalid_tool_diameter(self):
        result = validate_cnc_params(tool_diameter=0)
        assert result.safe is False
        assert any(e.code == "INVALID_TOOL_DIAMETER" for e in result.errors)

    def test_invalid_stepover_zero(self):
        result = validate_cnc_params(stepover_percent=0)
        assert result.safe is False
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_invalid_stepover_over_100(self):
        result = validate_cnc_params(stepover_percent=150)
        assert result.safe is False
        assert any(e.code == "INVALID_STEPOVER" for e in result.errors)

    def test_high_stepover_warning(self):
        result = validate_cnc_params(stepover_percent=85)
        assert result.safe is True
        assert len(result.warnings) >= 1


class TestValidateCNCParamsRaiseOnError:
    """Test raise_on_error=True behavior."""

    def test_zero_rpm_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            validate_cnc_params(spindle_rpm=0, raise_on_error=True)

    def test_zero_flutes_raises(self):
        with pytest.raises(CNCPreflightError_ZeroFlutes):
            validate_cnc_params(flute_count=0, raise_on_error=True)

    def test_invalid_feed_range_raises(self):
        with pytest.raises(CNCPreflightError_InvalidFeedRange):
            validate_cnc_params(feed_rate_min=2000, feed_rate_max=500, raise_on_error=True)

    def test_invalid_depth_raises(self):
        with pytest.raises(CNCPreflightError_InvalidDepth):
            validate_cnc_params(depth_of_cut=-1, raise_on_error=True)

    def test_invalid_tool_diameter_raises(self):
        with pytest.raises(CNCPreflightError_InvalidToolDiameter):
            validate_cnc_params(tool_diameter=0, raise_on_error=True)


class TestRequireSafeCNCParams:
    """Test require_safe_cnc_params function."""

    def test_valid_params_no_raise(self):
        require_safe_cnc_params(spindle_rpm=18000, flute_count=2)

    def test_invalid_params_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            require_safe_cnc_params(spindle_rpm=0)


class TestCalculateChiploadSafe:
    """Test calculate_chipload_safe function."""

    def test_valid_chipload(self):
        chipload = calculate_chipload_safe(
            feed_rate_mm_min=1000,
            spindle_rpm=10000,
            flute_count=2,
        )
        assert chipload is not None
        assert chipload == pytest.approx(0.05)

    def test_zero_rpm_raises(self):
        with pytest.raises(CNCPreflightError_ZeroRPM):
            calculate_chipload_safe(
                feed_rate_mm_min=1000,
                spindle_rpm=0,
                flute_count=2,
            )

    def test_zero_flutes_raises(self):
        with pytest.raises(CNCPreflightError_ZeroFlutes):
            calculate_chipload_safe(
                feed_rate_mm_min=1000,
                spindle_rpm=10000,
                flute_count=0,
            )
