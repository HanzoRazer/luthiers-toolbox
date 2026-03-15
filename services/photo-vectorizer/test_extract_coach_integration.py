"""
Extraction-loop proof: verify extract() adopts GeometryCoachV2 tuple results.

Two tests only:
  1. Accepted retry → result surfaces improved body + contour + decision
  2. Rejected retry → result preserves originals + warning present

These monkeypatch the heavy CV stages and test control flow only.
No real images, no CV fidelity — just tuple-adoption proof.
"""

from __future__ import annotations

import types
from pathlib import Path

import numpy as np
import pytest

from photo_vectorizer_v2 import PhotoVectorizerV2
from body_isolation_result import (
    BodyIsolationResult,
    BodyIsolationSignalBreakdown,
)
from geometry_coach_v2 import CoachDecisionV2


# ── Stubs ───────────────────────────────────────────────────────────────────


class _ContourStageResultStub:
    def __init__(
        self,
        *,
        best_score: float = 0.75,
        export_blocked: bool = False,
        export_block_reason: str | None = None,
        feature_contours_post_grid=None,
        body_contour_final=None,
    ):
        self.best_score = best_score
        self.contour_scores_pre = []
        self.contour_scores_post = []
        self.export_block_issues = []
        self.export_blocked = export_blocked
        self.export_block_reason = export_block_reason
        self.block_reason = export_block_reason
        self.recommended_next_action = None
        self.feature_contours_post_grid = feature_contours_post_grid or []
        self.body_contour_final = body_contour_final


class _BodyRegionStub:
    def __init__(
        self,
        *,
        x_px: int = 10,
        y_px: int = 10,
        width_px: int = 100,
        height_px: int = 200,
        confidence: float = 0.8,
        height_mm: float | None = None,
        width_mm: float | None = None,
    ):
        self.x = x_px
        self.y = y_px
        self.width = width_px
        self.height = height_px
        self.x_px = x_px
        self.y_px = y_px
        self.width_px = width_px
        self.height_px = height_px
        self.confidence = confidence
        self.height_mm = height_mm
        self.width_mm = width_mm


def _make_body_isolation_result(
    *,
    completeness_score: float = 0.6,
    review_required: bool = False,
) -> BodyIsolationResult:
    return BodyIsolationResult(
        body_bbox_px=(10, 10, 100, 200),
        body_region=_BodyRegionStub(),
        confidence=0.8,
        completeness_score=completeness_score,
        review_required=review_required,
        score_breakdown=BodyIsolationSignalBreakdown(
            hull_coverage=0.8,
            vertical_extent_ratio=0.8,
            width_stability=0.8,
            border_contact_penalty=0.0,
            center_alignment=0.8,
            lower_bout_presence=0.8,
        ),
    )


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def tiny_image(tmp_path: Path) -> Path:
    import cv2

    img = np.full((32, 32, 3), 255, dtype=np.uint8)
    path = tmp_path / "tiny.png"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture
def vectorizer(monkeypatch) -> PhotoVectorizerV2:
    """
    Build a PhotoVectorizerV2 with expensive CV internals stubbed out so we can
    prove the extract() adoption/rejection control flow cleanly.
    """
    from photo_vectorizer_v2 import InputType

    img = np.full((32, 32, 3), 255, dtype=np.uint8)
    alpha = np.ones((32, 32), dtype=np.uint8) * 255

    # Skip __init__ to avoid loading SAM / heavy models
    pv = PhotoVectorizerV2.__new__(PhotoVectorizerV2)

    # Stub _load_image (staticmethod)
    monkeypatch.setattr(
        PhotoVectorizerV2, "_load_image",
        staticmethod(lambda _: img),
    )

    # Module-level helpers called during extract()
    monkeypatch.setattr(
        "photo_vectorizer_v2.compute_rough_mpp",
        lambda body_region, spec_name=None: 1.0,
    )
    monkeypatch.setattr(
        "photo_vectorizer_v2.emit_calibration_guidance",
        lambda calibration, spec_name, body_h_px, result: None,
    )

    # Wire required scalar attributes
    pv.bg_method = types.SimpleNamespace(value="none")
    pv.simplify_tolerance_mm = 0.1
    pv.default_unit = None
    pv.enable_body_isolation_coach = True

    # --- Stage component stubs ---
    pv.splitter = types.SimpleNamespace(
        detect_and_split=lambda image: types.SimpleNamespace(is_multi=False, crops=[]),
    )
    pv.orientation_detector = types.SimpleNamespace(
        detect_and_correct=lambda image, is_dark_bg=False: types.SimpleNamespace(
            total_rotation=0, rotated_image=None, orientation="upright",
        ),
    )
    pv.exif = types.SimpleNamespace(get_dpi=lambda source: None)
    pv.input_classifier = types.SimpleNamespace(
        classify=lambda image: (InputType.PHOTO, 0.9, {}),
    )
    pv.perspective = types.SimpleNamespace(correct=lambda image: (image, False))
    pv.bg_remover = types.SimpleNamespace(
        remove=lambda image, method, is_dark_bg=False: (image, alpha, "none"),
    )
    pv.body_isolator = types.SimpleNamespace(use_adaptive=False)
    pv.edge_detector = types.SimpleNamespace(
        detect=lambda *a, **kw: np.zeros((32, 32), dtype=np.uint8),
    )

    # Family classifier — returns object with .family and .confidence
    pv.family_classifier = types.SimpleNamespace(
        classify=lambda *a, **kw: types.SimpleNamespace(
            family="dreadnought", confidence=0.8,
        ),
    )

    # Calibrator — returns object with .mm_per_px, .source.value, .message, .confidence
    pv.calibrator = types.SimpleNamespace(
        calibrate=lambda *a, **kw: types.SimpleNamespace(
            mm_per_px=1.0, confidence=0.8, message="ok",
            source=types.SimpleNamespace(value="instrument_spec"),
        ),
    )

    # Body isolation stage (default — tests override per-case)
    pv.body_isolation_stage = types.SimpleNamespace(
        run=lambda *a, **kw: _make_body_isolation_result(),
    )

    # Contour stage (default — tests override per-case)
    contour_original = _ContourStageResultStub(best_score=0.55, export_blocked=False)
    pv.contour_stage = types.SimpleNamespace(
        run=lambda *a, **kw: contour_original,
    )

    # Geometry authority (lightweight, real)
    from geometry_authority import GeometryAuthority
    pv.geometry_authority = GeometryAuthority()

    # Coach placeholder (tests override per-case)
    pv.geometry_coach_v2 = types.SimpleNamespace(
        evaluate=lambda **kw: (
            _make_body_isolation_result(),
            contour_original,
            CoachDecisionV2(action="accept", reason="default stub"),
        ),
    )

    return pv


# ── Test 1: accepted retry result is adopted ────────────────────────────────


def test_extract_adopts_accepted_coach_results(
    monkeypatch, vectorizer: PhotoVectorizerV2, tiny_image: Path,
):
    """
    When the coach returns an improved body + contour, extract() must
    surface those as result.body_isolation and result.contour_stage.
    """
    original_body = _make_body_isolation_result(
        completeness_score=0.40, review_required=True,
    )
    improved_body = _make_body_isolation_result(
        completeness_score=0.78, review_required=False,
    )
    original_contour = _ContourStageResultStub(best_score=0.55, export_blocked=False)
    accepted_contour = _ContourStageResultStub(best_score=0.81, export_blocked=False)

    coach_decision = CoachDecisionV2(
        action="rerun_body_isolation",
        reason="Body isolation likely under-captured lower bout.",
        retry_count=0,
        original_body_score=original_body.completeness_score,
        original_contour_score=original_contour.best_score,
        candidate_body_score=improved_body.completeness_score,
        candidate_contour_score=accepted_contour.best_score,
        notes=["Accepted improved retry."],
    )

    # Stage 4.5 returns the original body
    monkeypatch.setattr(
        vectorizer, "body_isolation_stage",
        types.SimpleNamespace(run=lambda *a, **kw: original_body),
    )
    # Stage 8 returns the original contour
    monkeypatch.setattr(
        vectorizer, "contour_stage",
        types.SimpleNamespace(run=lambda *a, **kw: original_contour),
    )
    # Coach returns the improved tuple
    def fake_evaluate(**kwargs):
        return improved_body, accepted_contour, coach_decision

    monkeypatch.setattr(
        vectorizer, "geometry_coach_v2",
        types.SimpleNamespace(evaluate=fake_evaluate),
    )

    result = vectorizer.extract(str(tiny_image))

    assert result.body_isolation is improved_body
    assert result.contour_stage is accepted_contour
    assert result.geometry_coach_v2 is coach_decision
    assert result.geometry_coach_v2.action == "rerun_body_isolation"


# ── Test 2: rejected retry preserves original result ────────────────────────


def test_extract_preserves_original_results_on_manual_review(
    monkeypatch, vectorizer: PhotoVectorizerV2, tiny_image: Path,
):
    """
    When the coach returns manual_review_required, extract() must keep the
    original body/contour and surface a warning.
    """
    original_body = _make_body_isolation_result(
        completeness_score=0.38, review_required=True,
    )
    original_contour = _ContourStageResultStub(
        best_score=0.22,
        export_blocked=True,
        export_block_reason="low contour plausibility",
    )

    coach_decision = CoachDecisionV2(
        action="manual_review_required",
        reason="Scores remain too low for safe autonomous correction.",
        retry_count=2,
        original_body_score=original_body.completeness_score,
        original_contour_score=original_contour.best_score,
        notes=["No safe retry path selected."],
    )

    monkeypatch.setattr(
        vectorizer, "body_isolation_stage",
        types.SimpleNamespace(run=lambda *a, **kw: original_body),
    )
    monkeypatch.setattr(
        vectorizer, "contour_stage",
        types.SimpleNamespace(run=lambda *a, **kw: original_contour),
    )

    def fake_evaluate(**kwargs):
        return original_body, original_contour, coach_decision

    monkeypatch.setattr(
        vectorizer, "geometry_coach_v2",
        types.SimpleNamespace(evaluate=fake_evaluate),
    )

    result = vectorizer.extract(str(tiny_image))

    assert result.body_isolation is original_body
    assert result.contour_stage is original_contour
    assert result.geometry_coach_v2 is coach_decision
    assert result.geometry_coach_v2.action == "manual_review_required"
    assert any(
        "manual review" in w.lower() or "scores remain too low" in w.lower()
        for w in result.warnings
    )
