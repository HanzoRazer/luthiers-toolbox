from types import SimpleNamespace

import numpy as np

from contour_plausibility import ContourPlausibilityScorer


def _rect(x, y, w, h):
    return np.array(
        [[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]],
        dtype=np.int32,
    )


def test_scorer_caps_total_score_when_ownership_fails():
    scorer = ContourPlausibilityScorer(ownership_threshold=0.60)
    contour = _rect(10, 0, 15, 100)
    result = SimpleNamespace(
        best_score=0.92,
        diagnostics={
            "completeness_score": 0.75,
            "border_contact_score": 0.05,
            "vertical_coverage_score": 0.40,
            "neck_inclusion_score": 0.55,
        },
        export_block_issues=[],
        export_blocked=False,
        export_block_reason=None,
    )

    scorer.annotate_result(result, contour=contour, image_shape=(120, 80))

    assert result.ownership_score < 0.60
    assert result.ownership_ok is False
    assert result.best_score <= 0.59
    assert result.export_blocked is True
    assert "body_ownership_failed" in result.export_block_issues


def test_scorer_preserves_exportability_for_owned_body():
    scorer = ContourPlausibilityScorer(ownership_threshold=0.60)
    contour = _rect(10, 10, 50, 80)
    result = SimpleNamespace(
        best_score=0.80,
        diagnostics={
            "completeness_score": 0.88,
            "border_contact_score": 0.02,
            "vertical_coverage_score": 0.91,
            "neck_inclusion_score": 0.04,
        },
        export_block_issues=[],
        export_blocked=False,
        export_block_reason=None,
    )

    scorer.annotate_result(result, contour=contour, image_shape=(120, 100))

    assert result.ownership_score >= 0.60
    assert result.ownership_ok is True
    assert result.export_blocked is False
