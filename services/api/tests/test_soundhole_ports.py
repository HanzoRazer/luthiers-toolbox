"""Tests for soundhole_ports.py (DECOMP-002 Phase 3 — side port / inverse solvers)."""

from __future__ import annotations

import math

import pytest

from app.calculators.soundhole_physics import PortSpec
from app.calculators.soundhole_ports import (
    SIDE_PORT_POSITIONS,
    SIDE_PORT_TYPES,
    SidePortSpec,
    analyze_side_port,
    solve_for_diameter_mm,
    solve_for_diameter_with_side_port_mm,
)


def test_side_port_spec_from_circle_mm_applies_perim_factor():
    sp = SidePortSpec.from_circle_mm(40, port_type="oval", position="upper_bass")
    pf = SIDE_PORT_TYPES["oval"]["perim_factor"]
    r = (40 / 2) / 1000.0
    expected_perim = 2 * math.pi * r * pf
    assert abs(sp.perim_m - expected_perim) < 1e-9
    assert sp.area_m2 == pytest.approx(math.pi * r * r)


def test_side_port_spec_to_port_spec_adds_tube_length():
    sp = SidePortSpec(
        area_m2=0.001,
        perim_m=0.15,
        thickness_m=0.0023,
        tube_length_mm=5.0,
    )
    ps = sp.to_port_spec()
    assert ps.location == "side"
    assert ps.thickness_m == pytest.approx(0.0023 + 0.005)


def test_analyze_side_port_shift_and_warnings():
    main = [PortSpec.from_circle_mm(100, location="top", label="Main")]
    # Large waist port vs 80mm rim depth → structural warning; 30mm also trips waist >25 rule
    port = SidePortSpec.from_circle_mm(70, position="waist", label="Side")
    res = analyze_side_port(port, body_volume_m3=0.0175, main_ports=main, rim_depth_at_position_mm=80.0)
    assert isinstance(res.f_H_shift_hz, float)
    assert res.coupling_level == SIDE_PORT_POSITIONS["waist"]["coupling"]
    assert len(res.warnings) >= 1


def test_solve_for_diameter_mm_near_target():
    vol = 0.0175
    target = 108.0
    out = solve_for_diameter_mm(target, vol, thickness_m=0.0025, min_mm=50.0, max_mm=120.0)
    assert "diameter_mm" in out
    assert abs(out["achieved_f_hz"] - target) < 2.0


def test_solve_for_diameter_with_side_port_mm_returns_keys():
    out = solve_for_diameter_with_side_port_mm(
        target_f_hz=110.0,
        volume_m3=0.0175,
        side_port_diameter_mm=30.0,
    )
    assert set(out.keys()) == {"main_diameter_mm", "side_port_diameter_mm", "achieved_f_hz"}
    assert out["side_port_diameter_mm"] == 30.0


def test_side_port_positions_and_types_have_expected_keys():
    assert "upper_bass" in SIDE_PORT_POSITIONS
    assert "radiation" in SIDE_PORT_POSITIONS["upper_bass"]
    assert "round" in SIDE_PORT_TYPES
    assert SIDE_PORT_TYPES["round"]["perim_factor"] == 1.0
