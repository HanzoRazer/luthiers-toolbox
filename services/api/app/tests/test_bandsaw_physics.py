"""Bandsaw package: physics, blade library, machine."""

from __future__ import annotations

from app.cam_core.saw_lab.bandsaw import (
    Bandsaw,
    BandsawBladeSpec,
    compute_blade_tension,
    compute_drift_angle,
    compute_feed_rate,
    get_blade_by_id,
    load_blade_library,
    plan_curve_cut,
    plan_resaw_cut,
    validate_resaw_setup,
)


def test_blade_library_loads():
    blades = load_blade_library()
    assert len(blades) >= 1
    b = get_blade_by_id("bs-3-8-14tpi-carbon")
    assert b is not None
    assert b.width_mm > 0


def test_tension_positive():
    b = BandsawBladeSpec(id="t", width_mm=19.0, thickness_mm=0.9, tpi=14)
    r = compute_blade_tension(b)
    assert r["tension_n"] > 0


def test_drift_angle_range():
    r = compute_drift_angle(19.0, 350.0, 1725.0, 14.0)
    assert 0.05 <= r["drift_angle_deg"] <= 4.0


def test_validate_resaw():
    m = Bandsaw(350.0, 400.0, max_resaw_height_mm=200.0)
    b = BandsawBladeSpec(id="t", width_mm=19.0, thickness_mm=0.9, tpi=14)
    r = validate_resaw_setup(m, b, 50.0, 1725.0)
    assert "warnings" in r
    assert "sfpm" in r


def test_plan_curve():
    b = BandsawBladeSpec(id="t", width_mm=12.7, thickness_mm=0.65, tpi=3, min_curve_radius_mm=80.0)
    r = plan_curve_cut(b, 100.0)
    assert r["feasible"] is True


def test_plan_resaw_bookmatch():
    r = plan_resaw_cut(400.0, 8.0, 0.65, 3.5, bookmatch=True)
    assert r["halves_per_plate"] == 2
    assert r["half_width_mm"] == 200.0


def test_feed_rate():
    b = BandsawBladeSpec(id="t", width_mm=19.0, thickness_mm=0.9, tpi=14)
    r = compute_feed_rate(b, 3500.0, 40.0)
    assert r["feed_mm_s"] > 0
