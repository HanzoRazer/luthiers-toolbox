"""
Pass 2 — Blueprint geometry dedupe wiring tests.

Covers the flag-gated, post-selection / pre-export wiring without invoking the
full numpy/cv2 cleanup pipeline (blocked locally by the Python 3.14 / numpy
issue, and requiring real raster fixtures). These tests lock:

1. Feature-flag parsing/defaults on BlueprintLimits (off by default).
2. The export-invariant contract on the dedupe -> write_selected_chains path:
   R12 + LINE-only, no LWPOLYLINE, entity count does not increase, geometry
   survives.
3. Flag-gate semantics: disabled -> chains pass through untouched (identical
   export); enabled -> dedupe runs and emits stats.

Full real-fixture regression (Gibson Explorer / El Cuatro / Melody Maker through
the live pipeline) is intentionally NOT claimed here — see the handoff report.
"""
from __future__ import annotations

import importlib
import os

import ezdxf

from app.cam.unified_dxf_cleaner import (
    Chain,
    DXFCleaner,
    Point,
    deduplicate_chains,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _square(x0=0.0, y0=0.0, side=200.0):
    """A closed square contour as a Chain (4 corners)."""
    return Chain(points=[
        Point(x0, y0),
        Point(x0 + side, y0),
        Point(x0 + side, y0 + side),
        Point(x0, y0 + side),
    ])


def _entity_types(path):
    doc = ezdxf.readfile(str(path))
    return doc.dxfversion, [e.dxftype() for e in doc.modelspace()]


# ─── 1. Feature flag config ───────────────────────────────────────────────────

def _reload_limits():
    import app.services.blueprint_limits as limits_mod
    return importlib.reload(limits_mod)


def _set_env(monkeypatch_value):
    if monkeypatch_value is None:
        os.environ.pop("BLUEPRINT_ENABLE_GEOMETRY_DEDUPE", None)
    else:
        os.environ["BLUEPRINT_ENABLE_GEOMETRY_DEDUPE"] = monkeypatch_value


def test_flag_default_is_off_when_unset():
    _set_env(None)
    mod = _reload_limits()
    assert mod.LIMITS.enable_geometry_dedupe is False


def test_flag_truthy_values_enable():
    for val in ["1", "true", "TRUE", "Yes", "on", " on "]:
        _set_env(val)
        mod = _reload_limits()
        assert mod.LIMITS.enable_geometry_dedupe is True, f"{val!r} should enable"


def test_flag_falsey_or_garbage_disables():
    for val in ["0", "false", "no", "off", "", "maybe", "2"]:
        _set_env(val)
        mod = _reload_limits()
        assert mod.LIMITS.enable_geometry_dedupe is False, f"{val!r} should disable"


def test_env_bool_helper_directly():
    mod = _reload_limits()
    _set_env(None)
    assert mod._env_bool("BLUEPRINT_ENABLE_GEOMETRY_DEDUPE", False) is False
    assert mod._env_bool("BLUEPRINT_ENABLE_GEOMETRY_DEDUPE", True) is True  # unset -> default
    os.environ["BLUEPRINT_ENABLE_GEOMETRY_DEDUPE"] = "yes"
    assert mod._env_bool("BLUEPRINT_ENABLE_GEOMETRY_DEDUPE", False) is True
    _set_env(None)


# ─── 2. Export invariants on the dedupe -> write path ─────────────────────────

def test_export_is_r12_line_only_after_dedupe(tmp_path):
    # Two identical closed squares (exact duplicate) + a reversed duplicate edge.
    chains = [_square(), _square()]
    deduped, stats = deduplicate_chains(
        chains,
        endpoint_tol_mm=0.05,
        overlap_tol_mm=0.05,
        angle_tol_deg=1.0,
        preserve_layers=False,
        debug=False,
    )

    out = tmp_path / "deduped.dxf"
    DXFCleaner().write_selected_chains(out, deduped, polyline_pts=None)

    version, types = _entity_types(out)
    assert version == "AC1009", f"expected R12 (AC1009), got {version}"
    assert types, "geometry must not disappear"
    assert set(types) == {"LINE"}, f"R12 LINE-only policy violated: {set(types)}"
    assert "LWPOLYLINE" not in types
    assert "SPLINE" not in types
    assert "ARC" not in types


def test_dedupe_does_not_increase_entity_count(tmp_path):
    chains = [_square(), _square(), _square()]  # 3 identical copies

    # Baseline export (flag-off equivalent: chains written as-is).
    base = tmp_path / "base.dxf"
    DXFCleaner().write_selected_chains(base, chains, polyline_pts=None)
    _, base_types = _entity_types(base)

    # Deduped export (flag-on path).
    deduped, stats = deduplicate_chains(
        chains,
        endpoint_tol_mm=0.05,
        overlap_tol_mm=0.05,
        angle_tol_deg=1.0,
        preserve_layers=False,
        debug=False,
    )
    out = tmp_path / "deduped.dxf"
    DXFCleaner().write_selected_chains(out, deduped, polyline_pts=None)
    _, out_types = _entity_types(out)

    assert len(out_types) <= len(base_types)
    assert len(out_types) < len(base_types), "identical copies should be collapsed"
    assert stats.exact_duplicates_removed > 0


def test_distinct_geometry_survives_dedupe(tmp_path):
    # Two contours in different locations: nothing should be removed, and the
    # deduped export must match the flag-off (write-as-is) export entity count.
    chains = [_square(x0=0.0), _square(x0=500.0)]

    base = tmp_path / "base.dxf"
    DXFCleaner().write_selected_chains(base, chains, polyline_pts=None)
    _, base_types = _entity_types(base)

    deduped, stats = deduplicate_chains(
        chains,
        endpoint_tol_mm=0.05,
        overlap_tol_mm=0.05,
        angle_tol_deg=1.0,
        preserve_layers=False,
        debug=False,
    )
    out = tmp_path / "distinct.dxf"
    DXFCleaner().write_selected_chains(out, deduped, polyline_pts=None)
    _, types = _entity_types(out)

    # Real invariant: distinct geometry is conserved through dedupe.
    assert stats.output_segments == stats.input_segments
    assert (
        stats.exact_duplicates_removed
        + stats.reversed_duplicates_removed
        + stats.near_duplicates_removed
        + stats.overlap_duplicates_removed
    ) == 0
    assert set(types) == {"LINE"}
    assert "LWPOLYLINE" not in types
    # Deduped export carries the same entity count as writing the chains as-is.
    assert len(types) == len(base_types)
    assert len(types) > 0


# ─── 3. Flag-gate semantics (mirrors the wired branch) ────────────────────────

def _wired_branch(final_chains, enabled):
    """Exact replica of the gating logic inserted into the three cleanup paths,
    used to lock its off/on contract independent of the numpy pipeline."""
    geometry_dedupe_stats = None
    if final_chains and enabled:
        final_chains, _stats = deduplicate_chains(
            final_chains,
            endpoint_tol_mm=0.05,
            overlap_tol_mm=0.05,
            angle_tol_deg=1.0,
            preserve_layers=False,
            debug=False,
        )
        from dataclasses import asdict
        geometry_dedupe_stats = asdict(_stats)
    return final_chains, geometry_dedupe_stats


def test_gate_off_passes_chains_through_untouched():
    chains = [_square(), _square()]
    out_chains, stats = _wired_branch(chains, enabled=False)
    assert out_chains is chains, "flag off must not touch the chains list"
    assert stats is None, "no dedupe stats when flag off"


def test_gate_on_runs_dedupe_and_emits_stats():
    chains = [_square(), _square()]
    out_chains, stats = _wired_branch(chains, enabled=True)
    assert stats is not None, "flag on must emit dedupe stats"
    assert stats["exact_duplicates_removed"] >= 1
    assert "input_segments" in stats and "output_segments" in stats
    assert stats["output_segments"] < stats["input_segments"]
    assert len(out_chains) < len(chains) or out_chains != chains


def test_wiring_present_and_gated_in_all_three_paths():
    """Static guard: the flag-gated call exists once per cleanup path and is
    gated on LIMITS.enable_geometry_dedupe."""
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "app" / "services" / "blueprint_clean.py"
    text = src.read_text(encoding="utf-8")
    assert text.count("LIMITS.enable_geometry_dedupe") == 3
    assert text.count("deduplicate_chains(") >= 3
    assert text.count("geometry_deduplication=geometry_dedupe_stats") == 3
