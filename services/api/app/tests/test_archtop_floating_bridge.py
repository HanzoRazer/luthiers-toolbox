"""Archtop floating bridge sagitta and DXF smoke test."""

from __future__ import annotations

import math

from app.woodworking.archtop_floating_bridge import (
    build_archtop_bridge_report,
    compute_foot_arch_geometry,
    generate_dxf,
    resolve_arch_radius_from_sagitta,
)


def test_sagitta_radius_formula():
    s = 1000.0
    h = 10.0
    r = resolve_arch_radius_from_sagitta(s, h)
    expected = (s * s) / (8.0 * h) + (h / 2.0)
    assert abs(r - expected) < 1e-6


def test_foot_geometry():
    foot = compute_foot_arch_geometry(2000.0, 155.0)
    assert foot.sagitta_mm > 0
    assert foot.center_xy[1] < 0


def test_build_report():
    rep = build_archtop_bridge_report(span_mm=1200.0, sagitta_mm=8.0)
    assert rep.arch_radius_mm > 0
    assert len(rep.saddle_slots) == 6


def test_generate_dxf_smoke():
    r = resolve_arch_radius_from_sagitta(1200.0, 8.0)
    try:
        raw = generate_dxf(arch_radius_mm=r)
    except ImportError:
        return
    assert b"SECTION" in raw or b"EOF" in raw
