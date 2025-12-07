# services/api/app/tests/test_saw_bridge_profiles_integration.py

"""
Saw Bridge integration tests (Wave 5/6).

Tests that:
- The bridge uses tool and material profiles
- Physics results include profile data
"""

from __future__ import annotations

import pytest

from app.calculators.saw_bridge import evaluate_operation_feasibility
from app.data.tool_library import reset_cache


@pytest.fixture(autouse=True)
def reset_library_cache():
    """Reset the library cache before each test."""
    reset_cache()
    yield
    reset_cache()


def test_saw_bridge_returns_physics_result():
    """Test that saw bridge returns a valid physics result."""
    result = evaluate_operation_feasibility(
        operation="rosette_vcarve",
        material_id="Ebony",
        tool_id="vbit_60",
        spindle_rpm=16000.0,
        feed_mm_min=1200.0,
        path_length_mm=500.0,
    )

    assert result is not None
    assert "chipload_mm" in result
    assert "heat_index" in result
    assert "deflection_index" in result
    assert "risk_flags" in result


def test_saw_bridge_includes_tool_profile_data():
    """Test that saw bridge includes tool profile metadata."""
    result = evaluate_operation_feasibility(
        operation="rosette_vcarve",
        material_id="Ebony",
        tool_id="vbit_60",
        spindle_rpm=16000.0,
        feed_mm_min=1200.0,
        path_length_mm=500.0,
    )

    assert result is not None
    # Should include resolved profile data
    assert "flutes" in result
    assert "ideal_chipload_min_mm" in result
    assert "ideal_chipload_max_mm" in result
    assert result["flutes"] == 2  # vbit_60 has 2 flutes


def test_saw_bridge_invalid_params_returns_none():
    """Test that invalid parameters return None."""
    result = evaluate_operation_feasibility(
        operation="test",
        material_id="Ebony",
        tool_id="vbit_60",
        spindle_rpm=0,  # Invalid
        feed_mm_min=1200.0,
        path_length_mm=500.0,
    )

    assert result is None


def test_saw_bridge_heat_deflection_in_range():
    """Test that heat and deflection indices are in [0, 1]."""
    result = evaluate_operation_feasibility(
        operation="relief_outline",
        material_id="Spruce",
        tool_id="ball_3.0",
        spindle_rpm=18000.0,
        feed_mm_min=1000.0,
        path_length_mm=1000.0,
    )

    assert result is not None
    assert 0.0 <= result["heat_index"] <= 1.0
    assert 0.0 <= result["deflection_index"] <= 1.0


def test_saw_bridge_unknown_tool_uses_defaults():
    """Test that unknown tools use default values."""
    result = evaluate_operation_feasibility(
        operation="test",
        material_id="Ebony",
        tool_id="unknown_tool_xyz",
        spindle_rpm=16000.0,
        feed_mm_min=800.0,
        path_length_mm=500.0,
    )

    assert result is not None
    # Should use default 2 flutes
    assert result["flutes"] == 2
    # Should use default chipload band
    assert result["ideal_chipload_min_mm"] == 0.01
    assert result["ideal_chipload_max_mm"] == 0.04
