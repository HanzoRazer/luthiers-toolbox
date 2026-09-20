"""VEC-ROOT-001 section 8 -- first measurements any eligibility fix must not break.

These tests are EXPECTED TO FAIL against the current gate. That is the point:
they are the bookmark for the finding in
``docs/audit/VEC-ROOT-001_eligibility_body_definition.md``. They pass only when
the eligibility block in ``edge_to_dxf._build_hierarchy_nodes`` stops defining
"body" in photograph terms (``edge_to_dxf.py:963-976`` at main blob c847c043;
ROOT-001 cites 941-950, measured at ffd155e4, and its section 0a maps that to
main -- the ladder is byte-identical, only its position moved).

The criteria are OUTCOME criteria, so they survive whatever replaces
``cv2.contourArea``. Regions below are pixel coordinates on the pinned rasters
declared in ``corpus.py``.

Baseline reproduced 2026-09-20 on the pinned corpus:
  cuatro  3 eligible | too_small 7,328, child_contour 1 | winner 0.7323 = fret table
  L-00    0 eligible | too_small 3,034, child_contour 15, too_large 4 | run fails
"""

from __future__ import annotations

import inspect
import os

import pytest

from . import corpus, harness
from .conftest import skip_not_run

# --- pinned regions on the cuatro raster (2232 x 4000) ----------------------
# The lower bout, generously bounded. ROOT-001 section 2a: 1,437 contours are
# present here and 0 are eligible -- the perimeter is traced and then discarded.
CUATRO_LOWER_BOUT = (950, 2250, 2100, 3800)  # x0, y0, x1, y1

# The fret-interval table: the block the gate currently certifies at s=0.7323.
CUATRO_FRET_TABLE = (888, 286, 1134, 837)  # x0, y0, x1, y1


def _plan(request, plan_key: str):
    plan = corpus.PLANS[plan_key]
    path, reason = corpus.resolve(plan)
    if reason:
        skip_not_run(request, reason)
    actual = corpus.sha256_of(path)
    assert actual == plan.sha256, (
        f"corpus file {plan.filename!r} does not match the raster VEC-ROOT-001 "
        f"was measured against.\n  expected {plan.sha256}\n  found    {actual}\n"
        f"The section 8 numbers are not comparable against a different raster."
    )
    return path


# --------------------------------------------------------------------------
# Always runs. Needs no corpus. Guarantees this directory can never report
# "green" because nothing executed.
# --------------------------------------------------------------------------
def test_harness_is_wired():
    import edge_to_dxf as etd

    for name in ("_build_hierarchy_nodes", "_score_contour_group", "HierarchyNode"):
        assert hasattr(etd, name), (
            f"edge_to_dxf lost {name}; the harness no longer observes the gate"
        )

    sig = inspect.signature(etd._build_hierarchy_nodes)
    assert sig.parameters["min_area_ratio"].default == 0.005, (
        "the area floor moved; section 8 recorded counts are no longer comparable"
    )
    assert sig.parameters["max_area_ratio"].default == 0.95

    node_fields = getattr(etd.HierarchyNode, "__dataclass_fields__", {})
    for field_name in ("is_eligible_root", "reject_reason", "area_ratio", "bbox"):
        assert field_name in node_fields, f"HierarchyNode lost {field_name}"

    assert set(corpus.PLANS) == {"cuatro", "l00", "archtop"}
    for plan in corpus.PLANS.values():
        assert len(plan.sha256) == 64, f"{plan.key} is not hash-pinned"


# --------------------------------------------------------------------------
# Criterion 1 -- cuatro
# --------------------------------------------------------------------------
def test_criterion_1_cuatro_eligible_count_exceeds_three(request):
    src = _plan(request, "cuatro")
    result = harness.run_plan_cached("cuatro", src)
    assert result.eligible_count > 3, (
        f"cuatro: {result.eligible_count} eligible (ROOT-001 recorded 3). "
        f"rejects={result.rejects}"
    )


def test_criterion_1b_cuatro_lower_bout_perimeter_is_eligible(request):
    """The geometric clause. This is the criterion that survives a rewrite."""
    src = _plan(request, "cuatro")
    result = harness.run_plan_cached("cuatro", src)
    in_bout = [n for n in result.eligible
               if harness.overlaps(n.bbox, CUATRO_LOWER_BOUT)]
    assert in_bout, (
        "cuatro: no eligible contour reaches the lower bout "
        f"{CUATRO_LOWER_BOUT}. The gate cuts the body in half at the waist. "
        f"eligible bboxes={[n.bbox for n in result.eligible]}"
    )


# --------------------------------------------------------------------------
# Criterion 2 -- L-00
# --------------------------------------------------------------------------
def test_criterion_2_l00_eligible_count_exceeds_zero(request):
    src = _plan(request, "l00")
    result = harness.run_plan_cached("l00", src)
    assert result.eligible_count > 0, (
        f"L-00: 0 eligible, run failed={result.failed!r} ({result.error}). "
        f"rejects={result.rejects}. The body encloses 27.6% of the raster and is "
        f"refused as child_contour: rejecting the page border does not unparent it."
    )


# --------------------------------------------------------------------------
# Criterion 3 -- neither plan may certify a text block
# --------------------------------------------------------------------------
def test_criterion_3_cuatro_does_not_certify_the_fret_table(request):
    src = _plan(request, "cuatro")
    result = harness.run_plan_cached("cuatro", src)
    winner = result.winner
    assert winner is not None, "cuatro: nothing scored; cannot judge the winner"
    assert not harness.contained_in(winner.bbox, CUATRO_FRET_TABLE), (
        f"cuatro: the certified winner s={winner.score:.4f} bbox={winner.bbox} "
        f"({winner.member_count} members) is the fret-interval table. A confident "
        f"wrong answer with a score is the failure mode that survives review."
    )


def test_criterion_3b_l00_does_not_certify_a_text_block(request):
    src = _plan(request, "l00")
    result = harness.run_plan_cached("l00", src)
    if result.winner is None:
        # L-00 currently returns nothing at all; criterion 2 owns that failure.
        # Recorded, not silently skipped: every skip in this directory is visible.
        skip_not_run(
            request,
            "NOT_RUN_SUBSUMED: L-00 certified nothing at all, so there is no "
            "winner to judge; criterion 2 is the live failure for this plan",
        )
    assert result.winner.member_count > 1, (
        f"L-00: certified a single-contour group {result.winner.bbox}"
    )


# --------------------------------------------------------------------------
# Criterion 4 -- text masking must not land alone
# --------------------------------------------------------------------------
def test_criterion_4_text_masking_alone_is_not_sufficient(request):
    """Opt-in: easyocr is heavy and is absent from production requirements.

    ROOT-001 section 8.4: masking deletes the cuatro winner and promotes the
    *partial body* at 0.702 -- a more plausible wrong answer. This is a tripwire
    against landing masking and declaring the lane fixed.
    """
    if os.environ.get("VEC_ROOT_001_RUN_MASKING") != "1":
        skip_not_run(
            request,
            f"{corpus.OPT_IN_REQUIRED}: set VEC_ROOT_001_RUN_MASKING=1 to measure "
            f"criterion 4 (requires easyocr, which production does not install)",
        )
    pytest.importorskip("easyocr")
    src = _plan(request, "cuatro")
    result = harness.run_plan_cached("cuatro", src)
    in_bout = [n for n in result.eligible
               if harness.overlaps(n.bbox, CUATRO_LOWER_BOUT)]
    assert in_bout, (
        "cuatro with text masking: still no eligible contour in the lower bout. "
        "Masking alone does not fix the lane -- it only changes which wrong "
        "answer is certified."
    )


# --------------------------------------------------------------------------
# Section 11 control -- the only case that currently passes. A fix must not
# break it. Listed beyond section 8 four criteria because a "must not break"
# suite with no passing case has no regression arm.
# --------------------------------------------------------------------------
def test_control_archtop_still_yields_an_eligible_root(request):
    src = _plan(request, "archtop")
    result = harness.run_plan_cached("archtop", src)
    assert result.eligible_count >= 1, (
        f"archtop control regressed: {result.eligible_count} eligible "
        f"(ROOT-001 section 11 recorded 1). rejects={result.rejects}"
    )
