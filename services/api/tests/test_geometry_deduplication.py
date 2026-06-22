"""Unit tests for geometry deduplication (Pass 1 — utility only).

Covers the post-selection, pre-export dedup pass in
``app.cam.unified_dxf_cleaner``. These tests exercise the utility in isolation;
they do NOT touch scoring, selection, orchestration, the live blueprint
pipeline, or DXF export. The dedup pass is not wired anywhere yet.

Layer-preservation is verified against the internal ``Segment`` model directly
(chains carry no layer attribute in this codebase), which is the agreed-upon
synthetic-test approach for Pass 1.
"""

from __future__ import annotations

import math

from app.cam.unified_dxf_cleaner import (
    Chain,
    DeduplicationStats,
    Point,
    Segment,
    SegmentKey,
    build_duplicate_debug_svg,
    deduplicate_chains,
    _dedupe_segments,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _chain(*coords: tuple[float, float]) -> Chain:
    return Chain(points=[Point(x, y) for x, y in coords])


def _seg(ax: float, ay: float, bx: float, by: float, layer: str = "") -> Segment:
    return Segment(layer=layer, start=Point(ax, ay), end=Point(bx, by))


def _dedupe(segments, **kw):
    defaults = dict(
        endpoint_tol_mm=0.05,
        overlap_tol_mm=0.05,
        angle_tol_deg=1.0,
        preserve_layers=True,
    )
    defaults.update(kw)
    return _dedupe_segments(segments, **defaults)


# --------------------------------------------------------------------------- #
# 1. Exact duplicate
# --------------------------------------------------------------------------- #

def test_exact_duplicate_keeps_one():
    segs = [_seg(0, 0, 10, 0), _seg(0, 0, 10, 0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 1
    assert stats.exact_duplicates_removed == 1
    assert stats.reversed_duplicates_removed == 0
    assert stats.near_duplicates_removed == 0
    assert stats.overlap_duplicates_removed == 0
    assert stats.output_segments == 1


# --------------------------------------------------------------------------- #
# 2. Reversed duplicate
# --------------------------------------------------------------------------- #

def test_reversed_duplicate_keeps_one():
    segs = [_seg(0, 0, 10, 0), _seg(10, 0, 0, 0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 1
    assert stats.reversed_duplicates_removed == 1
    assert stats.exact_duplicates_removed == 0


# --------------------------------------------------------------------------- #
# 3. Near duplicate (endpoints within endpoint_tol_mm)
# --------------------------------------------------------------------------- #

def test_near_duplicate_keeps_one():
    # Second segment drifts 0.02mm (< 0.05mm tol) at both ends.
    segs = [_seg(0, 0, 10, 0), _seg(0.02, 0.0, 10.02, 0.0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 1
    assert stats.near_duplicates_removed == 1
    assert stats.exact_duplicates_removed == 0


def test_near_duplicate_outside_tol_is_kept():
    # 0.2mm drift (> 0.05mm tol) is a distinct segment, not a near-duplicate.
    segs = [_seg(0, 0, 10, 0), _seg(0.2, 0.0, 10.2, 0.0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 2
    assert stats.near_duplicates_removed == 0


# --------------------------------------------------------------------------- #
# 4. Different layer preserved (synthetic Segment model)
# --------------------------------------------------------------------------- #

def test_same_geometry_different_layers_both_preserved():
    segs = [
        _seg(0, 0, 10, 0, layer="BODY_OUTLINE"),
        _seg(0, 0, 10, 0, layer="NECK_POCKET"),
    ]
    kept, stats = _dedupe(segs, preserve_layers=True)
    assert len(kept) == 2
    assert {s.layer for s in kept} == {"BODY_OUTLINE", "NECK_POCKET"}
    assert stats.exact_duplicates_removed == 0


def test_same_geometry_layer_agnostic_when_not_preserving():
    segs = [
        _seg(0, 0, 10, 0, layer="BODY_OUTLINE"),
        _seg(0, 0, 10, 0, layer="NECK_POCKET"),
    ]
    kept, stats = _dedupe(segs, preserve_layers=False)
    assert len(kept) == 1
    assert stats.exact_duplicates_removed == 1


# --------------------------------------------------------------------------- #
# 5. Overlap duplicate (one segment fully on top of another)
# --------------------------------------------------------------------------- #

def test_overlap_contained_segment_removed():
    # Short segment lies fully on top of the long one (collinear, contained).
    segs = [_seg(0, 0, 100, 0), _seg(20, 0, 60, 0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 1
    assert kept[0].length() == 100  # the long host survives
    assert stats.overlap_duplicates_removed == 1


# --------------------------------------------------------------------------- #
# 6. Non-overlap collinear (same line, separate positions) — both preserved
# --------------------------------------------------------------------------- #

def test_collinear_but_separate_both_preserved():
    segs = [_seg(0, 0, 10, 0), _seg(50, 0, 60, 0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 2
    assert stats.overlap_duplicates_removed == 0


# --------------------------------------------------------------------------- #
# 7. Closed contour remains closed
# --------------------------------------------------------------------------- #

def test_closed_contour_remains_closed_through_dedupe():
    # A closed square, with one edge duplicated. Dedup must not break closure.
    square = _chain((0, 0), (10, 0), (10, 10), (0, 10), (0, 0))
    dup_edge = _chain((0, 0), (10, 0))  # duplicate of the first edge
    out, stats = deduplicate_chains([square, dup_edge])

    assert stats.input_segments > stats.output_segments  # something was removed
    assert any(c.is_closed(1.0) for c in out), "expected a closed chain to survive"
    # The closed survivor should still be a 4-sided loop.
    closed = next(c for c in out if c.is_closed(1.0))
    assert len(closed.points) >= 4


# --------------------------------------------------------------------------- #
# deduplicate_chains: feature separation + multiple-chain output
# --------------------------------------------------------------------------- #

def test_distinct_features_stay_separate():
    # Two non-touching closed loops (e.g. body outline + a cavity). Neither is a
    # duplicate; output must remain two valid chains, not one merged contour.
    body = _chain((0, 0), (100, 0), (100, 100), (0, 100), (0, 0))
    cavity = _chain((200, 0), (210, 0), (210, 10), (200, 10), (200, 0))
    out, stats = deduplicate_chains([body, cavity])
    assert len(out) == 2
    assert stats.exact_duplicates_removed == 0


def test_returns_stats_dataclass():
    out, stats = deduplicate_chains([_chain((0, 0), (10, 0))])
    assert isinstance(stats, DeduplicationStats)
    assert isinstance(out, list)


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #

def test_zero_length_segment_dropped():
    segs = [_seg(5, 5, 5, 5), _seg(0, 0, 10, 0)]
    kept, stats = _dedupe(segs)
    assert len(kept) == 1
    assert kept[0].length() == 10


def test_segment_key_is_hashable_and_canonical():
    # SegmentKey is a frozen dataclass usable as a dict key.
    k1 = SegmentKey(layer="x", ax=0, ay=0, bx=10, by=0)
    k2 = SegmentKey(layer="x", ax=0, ay=0, bx=10, by=0)
    d = {k1: 1}
    assert d[k2] == 1


# --------------------------------------------------------------------------- #
# Debug SVG overlay
# --------------------------------------------------------------------------- #

def test_build_duplicate_debug_svg_colors_by_category():
    retained = [_seg(0, 0, 10, 0)]
    dups = [
        Segment(layer="", start=Point(0, 0), end=Point(10, 0), category="exact"),
        Segment(layer="", start=Point(0, 0), end=Point(0, 10), category="near"),
        Segment(layer="", start=Point(0, 0), end=Point(5, 5), category="overlap"),
    ]
    svg = build_duplicate_debug_svg(retained, dups, width_mm=50.0, height_mm=50.0)
    assert svg.startswith("<svg")
    assert "#000000" in svg          # retained = black
    assert "#e11d48" in svg          # exact/reversed = red
    assert "#f97316" in svg          # near = orange
    assert "#a21caf" in svg          # overlap = purple
    assert 'width="50.0000mm"' in svg
