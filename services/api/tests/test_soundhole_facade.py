"""Tests for soundhole_facade.py (DECOMP-002 Phase 6 — public router API)."""

import pytest

from app.calculators.soundhole_facade import (
    SoundholeSpec,
    analyze_soundhole,
    check_soundhole_position,
    compute_soundhole_spec,
    get_standard_diameter,
    list_body_styles,
)
from app.calculators.soundhole_calc import PortSpec


def test_analyze_soundhole_returns_soundhole_result_with_expected_fields():
    """Main entry wires Helmholtz, ring, and placement into SoundholeResult."""
    port = PortSpec.from_circle_mm(100.0, label="Main")
    result = analyze_soundhole(
        volume_m3=0.02,
        ports=[port],
        ring_width_mm=10.0,
        x_from_neck_mm=200.0,
        body_length_mm=500.0,
    )
    assert result.f_helmholtz_hz > 0
    assert result.f_helmholtz_note != "—"
    assert len(result.port_details) == 1
    assert result.ring_width.status in ("GREEN", "YELLOW", "RED")
    assert result.placement.valid is True


def test_compute_soundhole_spec_matches_dreadnought_standard():
    spec = compute_soundhole_spec("dreadnought", body_length_mm=500.0)
    assert isinstance(spec, SoundholeSpec)
    assert spec.diameter_mm == 100.0
    assert spec.gate == "GREEN"


def test_check_soundhole_position_green_and_red():
    assert (
        check_soundhole_position(
            diameter_mm=100.0,
            position_mm=250.0,
            body_length_mm=500.0,
        )
        == "GREEN"
    )
    assert (
        check_soundhole_position(
            diameter_mm=100.0,
            position_mm=100.0,
            body_length_mm=500.0,
        )
        == "RED"
    )


def test_list_body_styles_and_get_standard_diameter_delegate_to_presets():
    styles = list_body_styles()
    assert "archtop" not in styles
    assert "dreadnought" in styles
    assert get_standard_diameter("dreadnought") == pytest.approx(100.0)
