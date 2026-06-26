"""
Junction / topology executable specs for geometry deduplication — ENABLEMENT BLOCKER.

These tests assert the CORRECT future topology behavior of `_reconstruct_chains`
at degree > 2 nodes. They are `xfail` on purpose: the current greedy,
input-order-dependent reconstruction corrupts topology at junctions (it strands
arms into separate chains, and fuses distinct loops that share a snapped node).
They are NOT a lock of current behavior and they do NOT fix the algorithm — they
document the gate that must be cleared before `BLUEPRINT_ENABLE_GEOMETRY_DEDUPE`
is enabled. Each xfail flips to pass once reconstruction is hardened.

Confirmed against the real implementation (see PR #159 enablement gate):
  * a `+` cross reconstructs to two lines whose pairing flips with input order
  * two closed squares sharing one corner merge into a single chain
Both produce valid R12 LINE-only DXF, so the existing suite passes through the
bug — none of those tests feed a > 2-degree node.
"""
from __future__ import annotations

import pytest

from app.cam.unified_dxf_cleaner import Chain, Point, deduplicate_chains

XFAIL_REASON = (
    "Known enablement blocker: current segment reconstruction is "
    "greedy/input-order-dependent at degree > 2 junctions (_reconstruct_chains). "
    "Asserts correct future topology; expected to pass once reconstruction is hardened."
)


def _dedupe(chains):
    out, _stats = deduplicate_chains(
        chains,
        endpoint_tol_mm=0.05,
        overlap_tol_mm=0.05,
        angle_tol_deg=1.0,
        preserve_layers=False,
    )
    return out


def _sig(chains):
    """Order-independent topology signature: a sorted multiset of chains, each
    chain represented as a sorted tuple of undirected (rounded) edges. Two
    reconstructions with the same signature are topologically identical."""
    out = []
    for c in chains:
        edges = []
        p = c.points
        for i in range(len(p) - 1):
            a = (round(p[i].x, 3), round(p[i].y, 3))
            b = (round(p[i + 1].x, 3), round(p[i + 1].y, 3))
            edges.append(tuple(sorted((a, b))))
        out.append(tuple(sorted(edges)))
    return sorted(out)


def _closed_loops(chains):
    return [c for c in chains if c.is_closed()]


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
def test_t_junction_reconstruction_is_order_invariant():
    """A T-junction (3 arms meeting at C) must reconstruct identically regardless
    of the order its arms are fed in."""
    A, B, D, C = Point(-10, 0), Point(10, 0), Point(0, -10), Point(0, 0)
    order1 = _dedupe([Chain([A, C]), Chain([C, B]), Chain([C, D])])
    order2 = _dedupe([Chain([C, D]), Chain([A, C]), Chain([C, B])])
    assert _sig(order1) == _sig(order2), (
        "T-junction reconstruction depends on input order"
    )


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
def test_plus_cross_reconstruction_is_order_invariant():
    """A 4-way cross must reconstruct identically regardless of arm input order
    (ideally collinear straight-through: N-O-S and E-O-W)."""
    N, S, E, W, O = Point(0, 10), Point(0, -10), Point(10, 0), Point(-10, 0), Point(0, 0)
    order1 = _dedupe([Chain([N, O]), Chain([O, S]), Chain([E, O]), Chain([O, W])])
    order2 = _dedupe([Chain([N, O]), Chain([E, O]), Chain([O, S]), Chain([O, W])])
    assert _sig(order1) == _sig(order2), (
        "cross reconstruction pairing flips with input order"
    )


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
def test_shared_corner_loops_stay_two_closed_features():
    """Two distinct closed squares touching at a single shared corner must remain
    two separate closed loops, not merge into one chain."""
    sq_a = [Point(0, 0), Point(-5, 0), Point(-5, -5), Point(0, -5), Point(0, 0)]
    sq_b = [Point(0, 0), Point(5, 0), Point(5, 5), Point(0, 5), Point(0, 0)]
    out = _dedupe([Chain(sq_a), Chain(sq_b)])
    assert len(_closed_loops(out)) == 2, (
        "corner-touching loops fused into one feature"
    )


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
def test_figure_eight_recovers_two_loops():
    """A figure-eight (one stroke that passes through a crossing node O twice)
    must recover its two closed lobes, not a single mangled chain."""
    O, A, B, C, D = Point(0, 0), Point(5, 0), Point(5, 5), Point(-5, 0), Point(-5, -5)
    # upper lobe O->A->B->O, then lower lobe O->C->D->O, as one self-touching chain
    fig8 = Chain([O, A, B, O, C, D, O])
    out = _dedupe([fig8])
    assert len(_closed_loops(out)) == 2, (
        "figure-eight lobes were not recovered as two closed loops"
    )
