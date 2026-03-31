"""Tests for woodworking calculators and Bandsaw."""

from __future__ import annotations

import math

from app.cam_core.saw_lab.bandsaw import Bandsaw
from app.woodworking.joinery import compute_box_joint, compute_dovetail_angle_from_slope
from app.woodworking.wooden_floating_bridge import compute_saddle_height_from_twelfth_action
from app.woodworking.archtop_floating_bridge import (
    BENEDETTO_17,
    build_archtop_bridge_report,
    compute_foot_arch_geometry,
    compute_post_hole_positions,
    resolve_arch_radius_from_sagitta,
)
from app.woodworking.panels import compute_floating_panel_gaps, compute_panel_blank_oversize


def test_bandsaw_blade_length_and_sfpm():
    # 350 mm wheels, 400 mm center distance
    bs = Bandsaw(wheel_diameter_mm=350.0, wheel_center_distance_mm=400.0)
    expected_len = math.pi * 350.0 + 2.0 * 400.0
    assert abs(bs.nominal_blade_length_mm() - expected_len) < 0.01

    # 1725 RPM typical ~14" saw: SFPM = pi * D_in * rpm * 12 / 60 ... use mm path
    mps = bs.surface_speed_m_per_s(1725.0)
    assert mps > 15.0
    sfpm = bs.surface_speed_sfpm(1725.0)
    rpm_back = bs.rpm_for_sfpm(sfpm)
    assert abs(rpm_back - 1725.0) < 0.1


def test_dovetail_1_6():
    r = compute_dovetail_angle_from_slope(6.0)
    expect_half = math.degrees(math.atan(1.0 / 6.0))
    assert abs(r.half_angle_from_vertical_deg - expect_half) < 1e-6
    assert abs(r.angle_deg - 2.0 * expect_half) < 1e-6


def test_box_joint():
    r = compute_box_joint(stock_width_mm=100.0, num_fingers=5, kerf_mm=3.0)
    # usable = 100 - 4*3 = 88, finger = 88/5 = 17.6
    assert abs(r.finger_width_mm - 17.6) < 1e-6


def test_floating_bridge_action():
    r = compute_saddle_height_from_twelfth_action(650.0, 2.0)
    assert abs(r.saddle_height_above_plane_mm - 4.0) < 1e-6
    assert abs(r.distance_12th_to_bridge_mm - 325.0) < 1e-6


def test_bandsaw_from_inches():
    bs = Bandsaw.from_wheel_inches(diameter_in=14.0, center_distance_in=15.0)
    assert abs(bs.wheel_diameter_mm - 14 * 25.4) < 1e-6

def test_archtop_bridge_nominal():
    """Uses 3048 mm nominal top-arch radius; foot chord = Benedetto base length."""
    r_nom = 3048.0
    foot = compute_foot_arch_geometry(r_nom, BENEDETTO_17.base_length_mm)
    posts = compute_post_hole_positions(BENEDETTO_17.post_spacing_mm)

    assert foot.arch_radius_mm == r_nom
    assert foot.chord_length_mm == BENEDETTO_17.base_length_mm
    expected_h = r_nom - math.sqrt(r_nom**2 - (BENEDETTO_17.base_length_mm / 2) ** 2)
    assert abs(foot.sagitta_mm - expected_h) < 1e-6

    assert len(posts.positions_mm) == 2
    half = BENEDETTO_17.post_spacing_mm / 2.0
    assert posts.positions_mm[0][0] == -half
    assert posts.positions_mm[1][0] == half
    assert posts.diameter_mm == BENEDETTO_17.post_hole_diameter_mm


def test_archtop_bridge_measured():
    """Measured span + sagitta resolve arch radius; report matches."""
    span_mm = 300.0
    sagitta_mm = 10.0
    expected_r = resolve_arch_radius_from_sagitta(span_mm, sagitta_mm)
    assert abs(expected_r - 1130.0) < 0.01

    rep = build_archtop_bridge_report(span_mm=span_mm, sagitta_mm=sagitta_mm)
    assert abs(rep.arch_radius_mm - 1130.0) < 0.01
    assert rep.foot["arch_radius_mm"] == rep.arch_radius_mm


def test_floating_panel_gaps():
    """Wider RH swing ⇒ larger tangential movement and larger gap per edge."""
    narrow = compute_floating_panel_gaps(
        400.0, "maple", rh_from=35.0, rh_to=40.0, num_capture_edges=4
    )
    wide = compute_floating_panel_gaps(
        400.0, "maple", rh_from=30.0, rh_to=50.0, num_capture_edges=4
    )
    assert wide.gap_per_edge_mm > narrow.gap_per_edge_mm
    assert wide.total_movement_mm > narrow.total_movement_mm


def test_panel_blank_oversize():
    """Rough blank extends past opening by trim allowance on each side."""
    r = compute_panel_blank_oversize(200.0, 300.0, oversize_mm_each_side=3.0)
    assert r.blank_width_mm > r.opening_width_mm
    assert r.blank_height_mm > r.opening_height_mm
    assert r.blank_width_mm == r.opening_width_mm + 6.0
    assert r.blank_height_mm == r.opening_height_mm + 6.0
