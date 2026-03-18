"""
Tests for app.cam.preflight_gate — safety-critical pre-flight validation.

This module is the last safety gate before G-code reaches the CNC machine.
Coverage target: >60%
"""

import pytest
from unittest.mock import patch, MagicMock

from app.cam.preflight_gate import (
    PreflightConfig,
    PreflightResult,
    PreflightBlockedError,
    preflight_validate,
    preflight_gate,
    _validate_depth_vs_stock,
    _validate_tool_vs_bounds,
)
from app.saw_lab.toolpaths_validate_service import Bounds


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def clean_gcode():
    """Sample G-code that passes basic validation."""
    return """
G21 ; mm mode
G90 ; absolute
G17 ; XY plane
M3 S18000 ; spindle on
G0 Z5.0
G0 X0 Y0
G1 Z-3.0 F500
G1 X50 Y50 F1000
G0 Z5.0
M5
M30
"""


@pytest.fixture
def mock_validate_ok():
    """Mock validate_gcode_static returning clean result."""
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "summary": {
            "units": "mm",
            "distance_mode": "absolute",
            "spindle_on": True,
            "bounds": {
                "min_x": 0.0,
                "max_x": 50.0,
                "min_y": 0.0,
                "max_y": 50.0,
                "min_z": -3.0,
                "max_z": 5.0,
            },
        },
    }


@pytest.fixture
def mock_validate_with_warnings():
    """Mock validate_gcode_static returning warnings."""
    return {
        "ok": True,
        "errors": [],
        "warnings": ["Feed rate very low on line 5"],
        "summary": {
            "bounds": {
                "min_x": 0.0,
                "max_x": 50.0,
                "min_y": 0.0,
                "max_y": 50.0,
                "min_z": -3.0,
                "max_z": 5.0,
            },
        },
    }


@pytest.fixture
def mock_validate_with_errors():
    """Mock validate_gcode_static returning errors."""
    return {
        "ok": False,
        "errors": ["Missing feed rate on G1 move"],
        "warnings": [],
        "summary": {
            "bounds": {
                "min_x": 0.0,
                "max_x": 50.0,
                "min_y": 0.0,
                "max_y": 50.0,
                "min_z": -3.0,
                "max_z": 5.0,
            },
        },
    }


# -----------------------------------------------------------------------------
# PreflightConfig Tests
# -----------------------------------------------------------------------------

class TestPreflightConfig:
    """Tests for PreflightConfig dataclass."""

    def test_default_config(self):
        """Default config has expected defaults."""
        config = PreflightConfig()
        assert config.stock_thickness_mm is None
        assert config.safe_z_mm == 5.0
        assert config.max_depth_margin_mm == 1.0
        assert config.require_units_mm is True
        assert config.require_absolute is True
        assert config.strict_mode is False

    def test_custom_config(self):
        """Custom values override defaults."""
        config = PreflightConfig(
            stock_thickness_mm=25.0,
            tool_diameter_mm=6.0,
            strict_mode=True,
        )
        assert config.stock_thickness_mm == 25.0
        assert config.tool_diameter_mm == 6.0
        assert config.strict_mode is True


# -----------------------------------------------------------------------------
# PreflightResult Tests
# -----------------------------------------------------------------------------

class TestPreflightResult:
    """Tests for PreflightResult dataclass."""

    def test_result_ok(self):
        """Result with ok=True has empty errors."""
        result = PreflightResult(ok=True)
        assert result.ok is True
        assert result.errors == []
        assert result.warnings == []

    def test_result_with_errors(self):
        """Result with errors has ok=False."""
        result = PreflightResult(
            ok=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert result.ok is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """to_dict() returns correct structure."""
        result = PreflightResult(
            ok=False,
            errors=["Error 1"],
            warnings=["Warning 1"],
            summary={"key": "value"},
        )
        d = result.to_dict()
        assert d["ok"] is False
        assert d["errors"] == ["Error 1"]
        assert d["warnings"] == ["Warning 1"]
        assert d["summary"] == {"key": "value"}


# -----------------------------------------------------------------------------
# PreflightBlockedError Tests
# -----------------------------------------------------------------------------

class TestPreflightBlockedError:
    """Tests for PreflightBlockedError exception."""

    def test_error_with_errors_only(self):
        """Exception captures errors."""
        err = PreflightBlockedError(["Error 1", "Error 2"])
        assert err.errors == ["Error 1", "Error 2"]
        assert err.warnings == []
        assert "Pre-flight blocked" in str(err)

    def test_error_with_warnings(self):
        """Exception captures errors and warnings."""
        err = PreflightBlockedError(["Error 1"], ["Warning 1"])
        assert err.errors == ["Error 1"]
        assert err.warnings == ["Warning 1"]


# -----------------------------------------------------------------------------
# Test 1: preflight_validate with clean config → ok=True
# -----------------------------------------------------------------------------

class TestPreflightValidateClean:
    """Test preflight_validate with clean G-code returns ok=True."""

    def test_clean_gcode_passes(self, clean_gcode, mock_validate_ok):
        """Clean G-code with valid config passes validation."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_ok,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(stock_thickness_mm=25.0),
            )
            assert result.ok is True
            assert result.errors == []

    def test_clean_gcode_no_config(self, clean_gcode, mock_validate_ok):
        """Clean G-code with default config passes validation."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_ok,
        ):
            result = preflight_validate(gcode_text=clean_gcode)
            assert result.ok is True


# -----------------------------------------------------------------------------
# Test 2: preflight_validate with depth > stock → ok=False
# -----------------------------------------------------------------------------

class TestPreflightValidateDepthExceeds:
    """Test preflight_validate when cut depth exceeds stock thickness."""

    def test_depth_exceeds_stock_blocked(self, clean_gcode):
        """Cut deeper than stock thickness is blocked."""
        # Mock bounds with min_z = -30mm (deeper than 25mm stock)
        mock_result = {
            "ok": True,
            "errors": [],
            "warnings": [],
            "summary": {
                "bounds": {
                    "min_x": 0.0, "max_x": 50.0,
                    "min_y": 0.0, "max_y": 50.0,
                    "min_z": -30.0, "max_z": 5.0,
                },
            },
        }
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_result,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(stock_thickness_mm=25.0),
            )
            assert result.ok is False
            assert len(result.errors) == 1
            assert "exceeds stock thickness" in result.errors[0]
            assert "30.00mm" in result.errors[0]
            assert "25.00mm" in result.errors[0]

    def test_depth_within_margin_warning(self, clean_gcode):
        """Cut within margin of stock bottom produces warning."""
        # Mock bounds with min_z = -24.5mm (within 1mm margin of 25mm stock)
        mock_result = {
            "ok": True,
            "errors": [],
            "warnings": [],
            "summary": {
                "bounds": {
                    "min_x": 0.0, "max_x": 50.0,
                    "min_y": 0.0, "max_y": 50.0,
                    "min_z": -24.5, "max_z": 5.0,
                },
            },
        }
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_result,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(stock_thickness_mm=25.0),
            )
            assert result.ok is True  # Warning, not error
            assert len(result.warnings) == 1
            assert "within" in result.warnings[0] and "1.0" in result.warnings[0]


# -----------------------------------------------------------------------------
# Test 3: strict_mode=True with warnings → ok=False
# -----------------------------------------------------------------------------

class TestPreflightValidateStrictMode:
    """Test strict_mode promotes warnings to errors."""

    def test_strict_mode_promotes_warnings(self, clean_gcode, mock_validate_with_warnings):
        """In strict mode, warnings become errors."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_with_warnings,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(strict_mode=True),
            )
            assert result.ok is False
            assert "Feed rate very low" in result.errors[0]
            assert result.warnings == []  # Warnings moved to errors


# -----------------------------------------------------------------------------
# Test 4: warnings but strict_mode=False → ok=True, warnings not empty
# -----------------------------------------------------------------------------

class TestPreflightValidateNonStrictWarnings:
    """Test non-strict mode preserves warnings without blocking."""

    def test_warnings_dont_block_in_non_strict(self, clean_gcode, mock_validate_with_warnings):
        """In non-strict mode, warnings don't block execution."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_with_warnings,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(strict_mode=False),
            )
            assert result.ok is True
            assert len(result.warnings) >= 1


# -----------------------------------------------------------------------------
# Test 5: _validate_depth_vs_stock directly
# -----------------------------------------------------------------------------

class TestValidateDepthVsStock:
    """Direct tests for _validate_depth_vs_stock function."""

    def test_no_stock_thickness_skips(self):
        """Missing stock_thickness produces warning and skips."""
        bounds = Bounds(min_z=-10.0, max_z=5.0)
        errors, warnings = [], []
        _validate_depth_vs_stock(
            bounds=bounds,
            stock_thickness_mm=None,
            max_depth_margin_mm=1.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 0
        assert "Stock thickness not specified" in warnings[0]

    def test_no_z_movements_skips(self):
        """No Z movements produces warning and skips."""
        bounds = Bounds(min_z=None, max_z=None)
        errors, warnings = [], []
        _validate_depth_vs_stock(
            bounds=bounds,
            stock_thickness_mm=25.0,
            max_depth_margin_mm=1.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 0
        assert "No Z movements detected" in warnings[0]

    def test_depth_exceeds_stock_error(self):
        """Depth exceeding stock produces error."""
        bounds = Bounds(min_z=-30.0, max_z=5.0)
        errors, warnings = [], []
        _validate_depth_vs_stock(
            bounds=bounds,
            stock_thickness_mm=25.0,
            max_depth_margin_mm=1.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 1
        assert "CRITICAL" in errors[0]
        assert "exceeds stock thickness" in errors[0]

    def test_depth_within_safe_margin(self):
        """Depth within safe margin produces no errors or warnings."""
        bounds = Bounds(min_z=-20.0, max_z=5.0)
        errors, warnings = [], []
        _validate_depth_vs_stock(
            bounds=bounds,
            stock_thickness_mm=25.0,
            max_depth_margin_mm=1.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 0
        assert len(warnings) == 0


# -----------------------------------------------------------------------------
# Test 6: Additional critical paths
# -----------------------------------------------------------------------------

class TestValidateToolVsBounds:
    """Direct tests for _validate_tool_vs_bounds function."""

    def test_no_tool_diameter_skips(self):
        """Missing tool_diameter skips validation."""
        bounds = Bounds(min_x=0, max_x=10, min_y=0, max_y=10)
        errors, warnings = [], []
        _validate_tool_vs_bounds(
            bounds=bounds,
            tool_diameter_mm=None,
            min_feature_size_mm=5.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_tool_larger_than_feature_error(self):
        """Tool larger than min feature produces error."""
        bounds = Bounds(min_x=0, max_x=50, min_y=0, max_y=50)
        errors, warnings = [], []
        _validate_tool_vs_bounds(
            bounds=bounds,
            tool_diameter_mm=10.0,
            min_feature_size_mm=5.0,
            errors=errors,
            warnings=warnings,
        )
        assert len(errors) == 1
        assert "exceeds minimum feature size" in errors[0]

    def test_x_range_smaller_than_tool_warning(self):
        """X range smaller than tool produces warning."""
        bounds = Bounds(min_x=0, max_x=3, min_y=0, max_y=50)
        errors, warnings = [], []
        _validate_tool_vs_bounds(
            bounds=bounds,
            tool_diameter_mm=6.0,
            min_feature_size_mm=None,
            errors=errors,
            warnings=warnings,
        )
        assert len(warnings) == 1
        assert "X range" in warnings[0]

    def test_y_range_smaller_than_tool_warning(self):
        """Y range smaller than tool produces warning."""
        bounds = Bounds(min_x=0, max_x=50, min_y=0, max_y=3)
        errors, warnings = [], []
        _validate_tool_vs_bounds(
            bounds=bounds,
            tool_diameter_mm=6.0,
            min_feature_size_mm=None,
            errors=errors,
            warnings=warnings,
        )
        assert len(warnings) == 1
        assert "Y range" in warnings[0]


class TestPreflightGate:
    """Tests for preflight_gate blocking function."""

    def test_gate_passes_on_ok(self, clean_gcode, mock_validate_ok):
        """Gate passes without raising when validation ok."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_ok,
        ):
            # Should not raise
            preflight_gate(
                gcode_text=clean_gcode,
                config=PreflightConfig(stock_thickness_mm=25.0),
            )

    def test_gate_raises_on_error(self, clean_gcode, mock_validate_with_errors):
        """Gate raises PreflightBlockedError on validation failure."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_with_errors,
        ):
            with pytest.raises(PreflightBlockedError) as exc_info:
                preflight_gate(
                    gcode_text=clean_gcode,
                    config=PreflightConfig(),
                )
            assert len(exc_info.value.errors) >= 1


class TestPreflightSummary:
    """Tests for preflight metadata in summary."""

    def test_summary_contains_preflight_metadata(self, clean_gcode, mock_validate_ok):
        """Summary includes preflight configuration metadata."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_ok,
        ):
            result = preflight_validate(
                gcode_text=clean_gcode,
                config=PreflightConfig(
                    stock_thickness_mm=25.0,
                    tool_diameter_mm=6.0,
                    strict_mode=True,
                ),
            )
            assert "preflight" in result.summary
            assert result.summary["preflight"]["stock_thickness_mm"] == 25.0
            assert result.summary["preflight"]["tool_diameter_mm"] == 6.0
            assert result.summary["preflight"]["strict_mode"] is True


class TestBaseValidationErrors:
    """Tests for base G-code validation errors propagation."""

    def test_base_errors_propagate(self, clean_gcode, mock_validate_with_errors):
        """Errors from base validation propagate to result."""
        with patch(
            "app.cam.preflight_gate.validate_gcode_static",
            return_value=mock_validate_with_errors,
        ):
            result = preflight_validate(gcode_text=clean_gcode)
            assert result.ok is False
            assert "Missing feed rate" in result.errors[0]
