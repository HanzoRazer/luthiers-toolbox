"""
Merge guard tests for ContourStage.

Proves:
1. When pre-merge beats post-merge by > epsilon → elected_source == "pre_merge_guarded"
2. When difference is within epsilon → baseline election unchanged

Uses monkeypatching to control scorer output without depending on the
full OpenCV contour pipeline.
"""
from __future__ import annotations

import numpy as np
import cv2
import pytest

import contour_stage as cs_mod
from contour_stage import ContourStage, StageParams
from photo_vectorizer_v2 import (
    BodyRegion,
    CalibrationResult,
    ContourScore,
    FeatureContour,
    FeatureType,
    ScaleSource,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_body_region():
    return BodyRegion(
        x=50, y=100, width=300, height=500,
        confidence=0.9, neck_end_row=100, max_body_width_px=300,
    )


def _make_calibration():
    return CalibrationResult(
        mm_per_px=0.5,
        source=ScaleSource.INSTRUMENT_SPEC,
        confidence=0.8,
        message="test",
    )


def _make_fc(name, area=10000.0, bbox=(50, 100, 300, 500)):
    """Minimal FeatureContour stub with real numpy points."""
    x, y, w, h = bbox
    pts = np.array([
        [[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]
    ], dtype=np.int32)
    return FeatureContour(
        points_px=pts,
        feature_type=FeatureType.BODY_OUTLINE,
        confidence=0.85,
        area_px=area,
        bbox_px=bbox,
        hash_id=name,
    )


def _make_score(contour_index, score, issues=None):
    return ContourScore(
        contour_index=contour_index,
        score=score,
        completeness=0.8,
        includes_neck=False,
        border_contact=False,
        dimension_plausibility=score,
        symmetry_score=0.7,
        aspect_ratio_ok=True,
        issues=issues or [],
    )


def _make_edges_and_mask(shape=(800, 600)):
    h, w = shape
    edges = np.zeros((h, w), dtype=np.uint8)
    mask = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2 + 50)
    axes = (120, 200)
    cv2.ellipse(edges, center, axes, 0, 0, 360, 255, 2)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return edges, mask


def _fake_scorer_class(pre_score, post_score, pre_issues=None, post_issues=None):
    """Return a class that, when instantiated, returns controlled scores.

    First call to score_all_candidates → pre-merge scores.
    Second call → post-merge scores.
    """
    class _FakeScorer:
        def __init__(self, **kwargs):
            self._call_count = 0

        def score_all_candidates(self, contours, body_region, family, mpp, image_shape, **kw):
            self._call_count += 1
            if self._call_count == 1:
                return [_make_score(0, pre_score, pre_issues)]
            return [_make_score(0, post_score, post_issues)]

        def elect_best(self, pre_scores, post_scores):
            best_pre = max(pre_scores, key=lambda s: s.score) if pre_scores else None
            best_post = max(post_scores, key=lambda s: s.score) if post_scores else None
            if best_pre is None and best_post is None:
                return -1, "none", 0.0
            if best_post and (not best_pre or best_post.score >= best_pre.score - 0.05):
                return best_post.contour_index, "post_merge", best_post.score
            return best_pre.contour_index, "pre_merge", best_pre.score

    return _FakeScorer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_merge_guard_prefers_pre_merge_when_better_than_post_by_epsilon(monkeypatch):
    """Pre-merge score 0.80 > post-merge 0.72 + ε 0.03 → guard triggers."""
    edges, mask = _make_edges_and_mask()

    # Patch scorer to return controlled scores
    monkeypatch.setattr(
        cs_mod, "ContourPlausibilityScorer",
        _fake_scorer_class(0.80, 0.72, ["pre is good"], ["post widened"]),
    )

    stage = ContourStage()
    result = stage.run(
        edges=edges,
        alpha_mask=mask,
        body_region=_make_body_region(),
        calibration=_make_calibration(),
        family="archtop",
        image_shape=(800, 600),
        params=StageParams(merge_guard_epsilon=0.03),
    )

    assert result.elected_source == "pre_merge_guarded"
    assert result.best_score == pytest.approx(0.80)
    assert result.pre_merge_best_contour is not None
    assert result.body_contour_final is result.pre_merge_best_contour
    assert result.diagnostics["merge_guard_triggered"] is True
    assert "pre-merge best score" in result.diagnostics["merge_guard_reason"]


def test_merge_guard_does_not_trigger_when_difference_within_epsilon(monkeypatch):
    """Pre-merge 0.80 − post-merge 0.78 = 0.02 < ε 0.03 → no guard."""
    edges, mask = _make_edges_and_mask()

    monkeypatch.setattr(
        cs_mod, "ContourPlausibilityScorer",
        _fake_scorer_class(0.80, 0.78, ["pre slightly better"], ["post close"]),
    )

    stage = ContourStage()
    result = stage.run(
        edges=edges,
        alpha_mask=mask,
        body_region=_make_body_region(),
        calibration=_make_calibration(),
        family="archtop",
        image_shape=(800, 600),
        params=StageParams(merge_guard_epsilon=0.03),
    )

    assert result.elected_source != "pre_merge_guarded"
    assert result.diagnostics["merge_guard_triggered"] is False
    assert result.diagnostics["merge_guard_reason"] is None
