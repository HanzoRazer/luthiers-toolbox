"""
Serialization durability test for retry diagnostics.

Proves that retry_attempts survives JSON round-trip after a coached extraction,
closing the loop: stage diagnostics → extraction result → serialized replay artifact.
"""
from __future__ import annotations

import json
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


class _BodyRegionStub:
    def __init__(
        self,
        *,
        x_px: int = 10,
        y_px: int = 10,
        width_px: int = 100,
        height_px: int = 200,
        confidence: float = 0.8,
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
        self.height_mm = None
        self.width_mm = None


class _ContourStageResultStub:
    def __init__(
        self,
        *,
        best_score: float = 0.75,
        export_blocked: bool = False,
        export_block_reason: str | None = None,
        feature_contours_post_grid=None,
        body_contour_final=None,
        elected_source: str = "post_merge",
        diagnostics: dict | None = None,
        ownership_score: float | None = None,
        ownership_ok: bool | None = None,
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
        self.elected_source = elected_source
        self.diagnostics = diagnostics if diagnostics is not None else {}
        self.ownership_score = ownership_score
        self.ownership_ok = ownership_ok


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


# ── Serialization helper ───────────────────────────────────────────────────


def _json_safe(obj):
    """
    Minimal serializer for replay-oriented tests.

    Converts nested objects into JSON-safe dict/list/scalar structures
    without depending on the production serializer implementation.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {
            k: _json_safe(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    return repr(obj)


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
    from photo_vectorizer_v2 import InputType

    img = np.full((32, 32, 3), 255, dtype=np.uint8)
    alpha = np.ones((32, 32), dtype=np.uint8) * 255

    pv = PhotoVectorizerV2.__new__(PhotoVectorizerV2)

    monkeypatch.setattr(
        PhotoVectorizerV2, "_load_image",
        staticmethod(lambda _: img),
    )
    monkeypatch.setattr(
        "photo_vectorizer_v2.compute_rough_mpp",
        lambda body_region, spec_name=None: 1.0,
    )
    monkeypatch.setattr(
        "photo_vectorizer_v2.emit_calibration_guidance",
        lambda calibration, spec_name, body_h_px, result: None,
    )

    pv.bg_method = types.SimpleNamespace(value="none")
    pv.simplify_tolerance_mm = 0.1
    pv.default_unit = None
    pv.enable_body_isolation_coach = True

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
    pv.family_classifier = types.SimpleNamespace(
        classify=lambda *a, **kw: types.SimpleNamespace(
            family="dreadnought", confidence=0.8,
        ),
    )
    pv.calibrator = types.SimpleNamespace(
        calibrate=lambda *a, **kw: types.SimpleNamespace(
            mm_per_px=1.0, confidence=0.8, message="ok",
            source=types.SimpleNamespace(value="instrument_spec"),
        ),
    )
    pv.body_isolation_stage = types.SimpleNamespace(
        run=lambda *a, **kw: _make_body_isolation_result(),
    )
    pv.contour_stage = types.SimpleNamespace(
        run=lambda *a, **kw: _ContourStageResultStub(best_score=0.55),
    )

    from geometry_authority import GeometryAuthority
    pv.geometry_authority = GeometryAuthority()

    pv.geometry_coach_v2 = types.SimpleNamespace(
        evaluate=lambda **kw: (
            _make_body_isolation_result(),
            _ContourStageResultStub(best_score=0.55),
            CoachDecisionV2(action="accept", reason="default stub"),
        ),
    )

    return pv


# ── Test ────────────────────────────────────────────────────────────────────


def test_retry_attempts_survive_json_serialization_of_photo_extraction_result(
    monkeypatch, vectorizer: PhotoVectorizerV2, tiny_image: Path,
):
    """
    After a coached extraction, retry_attempts must survive JSON round-trip.

    Proves: stage diagnostics → extraction result → serialized replay artifact
    → recovered payload still contains retry provenance.
    """
    improved_body = _make_body_isolation_result(completeness_score=0.62)
    improved_contour = _ContourStageResultStub(
        best_score=0.71,
        diagnostics={
            "retry_attempts": [
                {
                    "retry_reason": "Body isolation likely under-captured lower bout.",
                    "retry_profile_used": "lower_bout_recovery",
                    "retry_iteration": 1,
                    "score_before": 0.56,
                    "score_after": 0.71,
                    "score_delta": 0.15,
                }
            ]
        },
    )

    coach_decision = CoachDecisionV2(
        action="rerun_body_isolation",
        reason="Body isolation likely under-captured lower bout.",
        retry_count=0,
        original_body_score=0.40,
        original_contour_score=0.56,
        candidate_body_score=0.62,
        candidate_contour_score=0.71,
        notes=["Accepted improved retry."],
    )

    def fake_evaluate(**kwargs):
        return improved_body, improved_contour, coach_decision

    monkeypatch.setattr(
        vectorizer, "geometry_coach_v2",
        types.SimpleNamespace(evaluate=fake_evaluate),
    )

    photo_result = vectorizer.extract(str(tiny_image))

    # Serialize + deserialize through JSON-safe replay structure
    payload = _json_safe(photo_result)
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    retry_attempts = (
        decoded.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    assert len(retry_attempts) == 1
    attempt = retry_attempts[0]
    assert attempt["retry_reason"] == "Body isolation likely under-captured lower bout."
    assert attempt["retry_profile_used"] == "lower_bout_recovery"
    assert attempt["retry_iteration"] == 1
    assert attempt["score_delta"] > 0


def test_ownership_failure_cause_survives_json_serialization(
    monkeypatch, vectorizer: PhotoVectorizerV2, tiny_image: Path,
):
    """
    When ownership failure triggers a retry, the cause
    (ownership_score, retry_profile body_region_expansion) must
    survive JSON round-trip so replay trajectories preserve
    why the retry was forced.
    """
    improved_body = _make_body_isolation_result(completeness_score=0.68)
    improved_contour = _ContourStageResultStub(
        best_score=0.66,
        ownership_score=0.72,
        ownership_ok=True,
        diagnostics={
            "retry_attempts": [
                {
                    "retry_reason": (
                        "Contour body ownership is too low (0.39 < 0.60)."
                    ),
                    "retry_profile_used": "body_region_expansion",
                    "retry_iteration": 1,
                    "score_before": 0.58,
                    "score_after": 0.66,
                    "score_delta": 0.08,
                    "ownership_score_before": 0.39,
                    "ownership_score_after": 0.72,
                }
            ]
        },
    )

    coach_decision = CoachDecisionV2(
        action="rerun_body_isolation",
        reason="Contour body ownership is too low (0.39 < 0.60).",
        retry_count=0,
        original_body_score=0.69,
        original_contour_score=0.58,
        candidate_body_score=0.68,
        candidate_contour_score=0.66,
        notes=["Rule 0 fired: force body-region expansion retry."],
    )

    def fake_evaluate(**kwargs):
        return improved_body, improved_contour, coach_decision

    monkeypatch.setattr(
        vectorizer, "geometry_coach_v2",
        types.SimpleNamespace(evaluate=fake_evaluate),
    )

    photo_result = vectorizer.extract(str(tiny_image))

    payload = _json_safe(photo_result)
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    retry_attempts = (
        decoded.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    assert len(retry_attempts) == 1
    attempt = retry_attempts[0]
    assert attempt["retry_profile_used"] == "body_region_expansion"
    assert "ownership" in attempt["retry_reason"].lower()
    assert attempt["ownership_score_before"] == 0.39
    assert attempt["ownership_score_after"] == 0.72

    # Ownership score itself must appear on the contour_stage
    contour_stage_data = decoded.get("contour_stage", {})
    assert contour_stage_data.get("ownership_score") == 0.72
    assert contour_stage_data.get("ownership_ok") is True
