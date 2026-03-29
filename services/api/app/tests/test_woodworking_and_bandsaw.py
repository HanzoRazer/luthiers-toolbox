"""Tests for woodworking calculators and Bandsaw."""

from __future__ import annotations

import math

from app.cam_core.saw_lab.bandsaw import Bandsaw
from app.woodworking.joinery import compute_box_joint, compute_dovetail_angle_from_slope
from app.woodworking.floating_bridge import compute_saddle_height_from_twelfth_action


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
