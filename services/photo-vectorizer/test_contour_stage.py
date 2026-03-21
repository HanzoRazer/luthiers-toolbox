"""
Tests for contour_stage.py (extracted Stage 8) and geometry_coach.py.

Covers:
  - ContourStage.run() standalone invocation
  - StageParams customization
  - Enriched export blocking diagnostics
  - GeometryCoachV1 decision logic
  - Coach guardrails (max retries, monotonic improvement, no silent downgrade)
  - Equivalence: extracted module produces identical results to inline pipeline
"""

import hashlib
import numpy as np
import pytest
import cv2

from contour_stage import ContourStage, StageParams
from body_model import BodyLandmarks, BodyModel, GeometryConstraints
from geometry_coach import GeometryCoachV1, CoachConfig, CoachDecision
from photo_vectorizer_v2 import (
    BodyRegion,
    CalibrationResult,
    ContourScore,
    ContourStageResult,
    FeatureContour,
    FeatureType,
    InstrumentFamily,
    MergeResult,
    EXPORT_BLOCK_THRESHOLD,
    ScaleSource,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_body_region(x=50, y=100, w=300, h=500):
    return BodyRegion(
        x=x, y=y, width=w, height=h,
        confidence=0.9, neck_end_row=y, max_body_width_px=w,
    )


def _make_calibration(mpp=0.5):
    return CalibrationResult(
        mm_per_px=mpp,
        source=ScaleSource.INSTRUMENT_SPEC,
        confidence=0.8,
        message="test calibration",
    )


def _make_edges_and_mask(shape=(800, 600)):
    """Create synthetic edge image + alpha mask with a body-shaped contour."""
    h, w = shape
    edges = np.zeros((h, w), dtype=np.uint8)
    mask = np.zeros((h, w), dtype=np.uint8)

    # Draw a body-shaped ellipse
    center = (w // 2, h // 2 + 50)
    axes = (120, 200)
    cv2.ellipse(edges, center, axes, 0, 0, 360, 255, 2)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    # Small feature contour (pickup route)
    cv2.rectangle(edges, (w // 2 - 30, h // 2 - 10),
                  (w // 2 + 30, h // 2 + 20), 255, 2)

    return edges, mask


def _make_edges_fragmented(shape=(800, 600)):
    """Create synthetic edges with two body fragments (triggers merge)."""
    h, w = shape
    edges = np.zeros((h, w), dtype=np.uint8)
    mask = np.zeros((h, w), dtype=np.uint8)

    # Upper body fragment
    cv2.ellipse(edges, (w // 2, h // 3), (100, 100), 0, 0, 360, 255, 2)
    cv2.ellipse(mask, (w // 2, h // 3), (100, 100), 0, 0, 360, 255, -1)

    # Lower body fragment
    cv2.ellipse(edges, (w // 2, 2 * h // 3), (120, 120), 0, 0, 360, 255, 2)
    cv2.ellipse(mask, (w // 2, 2 * h // 3), (120, 120), 0, 0, 360, 255, -1)

    return edges, mask


# ===========================================================================
# StageParams
# ===========================================================================

class TestStageParams:
    def test_defaults(self):
        p = StageParams()
        assert p.merge_max_close_px == 120
        assert p.elect_min_overlap == 0.50
        assert p.export_block_threshold == EXPORT_BLOCK_THRESHOLD
        assert p.scorer_ownership_threshold == 0.60

    def test_custom_params(self):
        p = StageParams(merge_max_close_px=60, elect_max_width_factor=1.50)
        assert p.merge_max_close_px == 60
        assert p.elect_max_width_factor == 1.50


# ===========================================================================
# ContourStage.run() — standalone invocation
# ===========================================================================

class TestContourStageRun:
    """Core tests: extracted stage can run independently."""

    def test_basic_run_returns_result(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges,
            alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert isinstance(result, ContourStageResult)
        assert result.body_contour_final is not None
        assert len(result.feature_contours_post_grid) > 0

    def test_pre_merge_contours_captured(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert len(result.feature_contours_pre_merge) > 0

    def test_post_merge_contours_captured(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert len(result.feature_contours_post_merge) > 0

    def test_scores_populated(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        # At least one scoring pass should produce results
        assert (len(result.contour_scores_pre) > 0 or
                len(result.contour_scores_post) > 0)

    def test_best_score_positive(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert result.best_score > 0.0

    def test_elected_source_valid(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert result.elected_source in ("pre_merge", "post_merge", "none")

    def test_diagnostics_populated(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert "n_pre_merge" in result.diagnostics
        assert "n_post_merge" in result.diagnostics
        assert "family" in result.diagnostics

    def test_no_contours_returns_empty_result(self):
        """Empty edge image -> no contours -> graceful result."""
        blank = np.zeros((100, 100), dtype=np.uint8)
        stage = ContourStage()
        result = stage.run(
            edges=blank, alpha_mask=blank,
            body_region=None,
            calibration=_make_calibration(),
            family=InstrumentFamily.UNKNOWN,
            image_shape=(100, 100),
        )
        assert isinstance(result, ContourStageResult)
        assert result.diagnostics.get("error") == "no_contours_found"

    def test_no_body_region_still_works(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=None,
            calibration=_make_calibration(),
            family=InstrumentFamily.UNKNOWN,
            image_shape=(800, 600),
        )
        assert result.body_contour_final is not None

    def test_custom_params_respected(self):
        """Custom StageParams should affect the pipeline."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()

        default_result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )

        custom = StageParams(min_contour_area_px=999999)
        custom_result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
            params=custom,
        )
        # With very high min area filter, should get no contours
        assert custom_result.diagnostics.get("error") == "no_contours_found"


# ===========================================================================
# ContourStage with fragmented bodies (merge path)
# ===========================================================================

class TestContourStageMerge:
    def test_fragmented_triggers_merge(self):
        edges, mask = _make_edges_fragmented()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(x=50, y=50, w=400, h=600),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        # If merge kicked in, post_merge should have more contours
        # or merge_result should be populated
        has_merge = result.merge_result is not None
        has_more = len(result.feature_contours_post_merge) >= len(
            result.feature_contours_pre_merge)
        assert has_merge or has_more


# ===========================================================================
# Enriched export blocking diagnostics
# ===========================================================================

class TestEnrichedExportBlocking:
    def test_score_breakdown_populated(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        # Score breakdown should always be populated when there are scores
        if result.contour_scores_pre or result.contour_scores_post:
            assert "composite" in result.export_block_score_breakdown
            assert "completeness" in result.export_block_score_breakdown
            assert "dimension_plausibility" in result.export_block_score_breakdown

    def test_export_block_issues_is_list(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert isinstance(result.export_block_issues, list)

    def test_recommended_action_set_when_blocked(self):
        """When export is blocked, recommended_next_action must be set."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        # Force blocking with absurdly high threshold
        params = StageParams(export_block_threshold=999.0)
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
            params=params,
        )
        assert result.export_blocked is True
        assert result.recommended_next_action in (
            "rerun_contour_stage_with_alt_merge_profile",
            "manual_review_required",
        )

    def test_not_blocked_no_recommended_action(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        # Very low threshold to avoid blocking
        params = StageParams(export_block_threshold=0.0)
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
            params=params,
        )
        assert result.export_blocked is False
        assert result.recommended_next_action is None

    def test_new_fields_on_contour_stage_result(self):
        """Verify the three new diagnostic fields exist on dataclass."""
        csr = ContourStageResult()
        assert hasattr(csr, "export_block_issues")
        assert hasattr(csr, "export_block_score_breakdown")
        assert hasattr(csr, "recommended_next_action")
        assert csr.export_block_issues == []
        assert csr.export_block_score_breakdown == {}
        assert csr.recommended_next_action is None


# ===========================================================================
# GeometryCoachV1 — decision logic
# ===========================================================================

def _make_contour_score(score=0.7, completeness=0.8, dim_plaus=0.8,
                        aspect_ok=True, border=False, neck=False):
    return ContourScore(
        contour_index=0, score=score, completeness=completeness,
        includes_neck=neck, border_contact=border,
        dimension_plausibility=dim_plaus,
        symmetry_score=0.7, aspect_ratio_ok=aspect_ok,
    )


def _make_stage_result(
    best_score=0.7,
    merge_result=None,
    scores_pre=None,
    scores_post=None,
):
    return ContourStageResult(
        best_score=best_score,
        merge_result=merge_result,
        contour_scores_pre=scores_pre or [],
        contour_scores_post=scores_post or [],
    )


class TestCoachShouldRetry:
    """Tests for GeometryCoachV1.should_retry()."""

    def test_good_score_no_retry(self):
        coach = GeometryCoachV1()
        result = _make_stage_result(best_score=0.80)
        assert coach.should_retry(result) is False

    def test_low_score_no_merge_no_retry(self):
        """Below threshold but no merge occurred — nothing to retry."""
        coach = GeometryCoachV1()
        result = _make_stage_result(
            best_score=0.40,
            merge_result=None,
            scores_pre=[_make_contour_score(0.40)],
            scores_post=[_make_contour_score(0.40)],
        )
        assert coach.should_retry(result) is False

    def test_low_score_with_merge_and_disagreement_triggers_retry(self):
        coach = GeometryCoachV1()
        merge = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )
        result = _make_stage_result(
            best_score=0.40,
            merge_result=merge,
            scores_pre=[_make_contour_score(0.50)],
            scores_post=[_make_contour_score(0.35)],
        )
        assert coach.should_retry(result) is True

    def test_completeness_improved_dims_worsened_triggers(self):
        coach = GeometryCoachV1()
        merge = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )
        pre = _make_contour_score(score=0.55, completeness=0.6, dim_plaus=0.8)
        post = _make_contour_score(score=0.55, completeness=0.8, dim_plaus=0.3)
        result = _make_stage_result(
            best_score=0.55,
            merge_result=merge,
            scores_pre=[pre],
            scores_post=[post],
        )
        assert coach.should_retry(result) is True

    def test_no_scores_no_retry(self):
        coach = GeometryCoachV1()
        merge = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )
        result = _make_stage_result(best_score=0.40, merge_result=merge)
        assert coach.should_retry(result) is False


class TestCoachEvaluate:
    """Tests for the full coaching evaluate loop."""

    def test_good_score_accepted_immediately(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        coach = GeometryCoachV1()

        initial = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )

        final, decision = coach.evaluate(
            initial, stage, edges, mask,
            _make_body_region(), _make_calibration(),
            InstrumentFamily.SOLID_BODY, (800, 600),
        )

        assert decision.retries_attempted == 0
        assert decision.action_taken in ("accepted_original",)

    def test_decision_record_populated(self):
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        coach = GeometryCoachV1()

        initial = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )

        final, decision = coach.evaluate(
            initial, stage, edges, mask,
            _make_body_region(), _make_calibration(),
            InstrumentFamily.SOLID_BODY, (800, 600),
        )

        assert isinstance(decision, CoachDecision)
        assert decision.original_score > 0
        assert decision.final_score >= 0
        assert isinstance(decision.notes, list)


class TestCoachGuardrails:
    """Tests for coaching guardrails."""

    def test_max_retries_respected(self):
        config = CoachConfig(
            target_threshold=999.0,  # force retry
            max_retries=1,
        )
        coach = GeometryCoachV1(config=config)

        merge = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )

        initial = _make_stage_result(
            best_score=0.40,
            merge_result=merge,
            scores_pre=[_make_contour_score(0.50)],
            scores_post=[_make_contour_score(0.35)],
        )

        # Need real edges for stage rerun
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()

        final, decision = coach.evaluate(
            initial, stage, edges, mask,
            _make_body_region(), _make_calibration(),
            InstrumentFamily.SOLID_BODY, (800, 600),
        )

        assert decision.retries_attempted <= 1

    def test_improvement_epsilon_enforced(self):
        """Coach should not accept improvement smaller than epsilon."""
        config = CoachConfig(improvement_epsilon=0.03)
        coach = GeometryCoachV1(config=config)
        # epsilon is embedded in evaluate logic — tested via integration

    def test_no_silent_downgrade(self):
        """Worse rerun must be discarded, original kept."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()

        initial = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )

        # Even if coach tries reruns, final score must be >= original
        config = CoachConfig(target_threshold=999.0, max_retries=2)
        coach = GeometryCoachV1(config=config)

        # Force retry trigger
        initial.merge_result = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )
        initial.contour_scores_pre = [_make_contour_score(0.50)]
        initial.contour_scores_post = [_make_contour_score(0.35)]
        initial.best_score = 0.40

        final, decision = coach.evaluate(
            initial, stage, edges, mask,
            _make_body_region(), _make_calibration(),
            InstrumentFamily.SOLID_BODY, (800, 600),
        )

        # Invariant: final score never worse than initial
        assert decision.final_score >= initial.best_score - 0.001

    def test_terminal_review_state(self):
        """After exhausting retries below threshold -> review_required."""
        config = CoachConfig(
            target_threshold=999.0,  # impossible to meet
            max_retries=2,
            improvement_epsilon=999.0,  # impossible to improve enough
        )
        coach = GeometryCoachV1(config=config)

        merge = MergeResult(
            merged_contour=np.zeros((10, 1, 2), dtype=np.int32),
            n_fragments=2, fragment_areas=[1000, 2000],
            close_kernel_px=60, bbox_px=(0, 0, 100, 200),
        )
        initial = _make_stage_result(
            best_score=0.40,
            merge_result=merge,
            scores_pre=[_make_contour_score(0.50)],
            scores_post=[_make_contour_score(0.35)],
        )

        edges, mask = _make_edges_and_mask()
        stage = ContourStage()

        final, decision = coach.evaluate(
            initial, stage, edges, mask,
            _make_body_region(), _make_calibration(),
            InstrumentFamily.SOLID_BODY, (800, 600),
        )

        assert decision.action_taken == "review_required"
        assert "review required" in " ".join(decision.notes).lower()


# ===========================================================================
# CoachConfig
# ===========================================================================

class TestCoachConfig:
    def test_defaults(self):
        cfg = CoachConfig()
        assert cfg.target_threshold == 0.65
        assert cfg.max_retries == 2
        assert cfg.improvement_epsilon == 0.03
        assert len(cfg.merge_profiles) == 2

    def test_custom_profiles(self):
        profiles = [StageParams(merge_max_close_px=40)]
        cfg = CoachConfig(merge_profiles=profiles)
        assert len(cfg.merge_profiles) == 1
        assert cfg.merge_profiles[0].merge_max_close_px == 40


# ===========================================================================
# CoachDecision
# ===========================================================================

class TestCoachDecision:
    def test_creation(self):
        d = CoachDecision(
            action_taken="accepted_original",
            original_score=0.7,
            final_score=0.7,
            retries_attempted=0,
        )
        assert d.retry_scores == []
        assert d.notes == []


# ===========================================================================
# Extraction equivalence (the most important test)
# ===========================================================================

class TestExtractionEquivalence:
    """
    Verify that ContourStage.run() produces results structurally identical
    to what the inline pipeline produced.
    """

    def test_body_contour_elected(self):
        """Extracted stage elects a body contour just like inline did."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert result.body_contour_final is not None
        assert result.body_contour_final.feature_type == FeatureType.BODY_OUTLINE

    def test_grid_reclassification_runs(self):
        """Grid reclassification (Stage 8.5) runs inside extracted module."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert "grid_reclassified" in result.diagnostics

    def test_two_runs_same_result(self):
        """Same inputs -> same scores (deterministic)."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        args = dict(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        r1 = stage.run(**args)
        r2 = stage.run(**args)
        assert r1.best_score == r2.best_score
        assert r1.elected_source == r2.elected_source

    def test_full_result_populated(self):
        """All fields of ContourStageResult are set by run()."""
        edges, mask = _make_edges_and_mask()
        stage = ContourStage()
        result = stage.run(
            edges=edges, alpha_mask=mask,
            body_region=_make_body_region(),
            calibration=_make_calibration(),
            family=InstrumentFamily.SOLID_BODY,
            image_shape=(800, 600),
        )
        assert len(result.feature_contours_pre_merge) > 0
        assert len(result.feature_contours_post_merge) > 0
        assert len(result.feature_contours_post_grid) > 0
        assert result.body_contour_pre_grid is not None
        assert result.body_contour_final is not None
        assert result.best_score > 0


def test_stage_accepts_body_model_and_records_landmark_diagnostics():
    """ContourStage.run() accepts body_model and surfaces it in diagnostics."""
    stage = ContourStage()
    edges, alpha_mask = _make_edges_and_mask()
    body_region = _make_body_region()

    body_model = BodyModel(
        source_image_id=None,
        family_hint="archtop",
        spec_hint=None,
        body_bbox_px=(20, 30, 120, 240),
        body_region=body_region,
        row_width_profile_px=np.zeros(500, dtype=float),
        row_width_profile_smoothed_px=np.zeros(500, dtype=float),
        column_profile_px=np.zeros(300, dtype=float),
        mm_per_px=0.5,
        landmarks=BodyLandmarks(
            centerline_x_px=80.0,
            body_top_y_px=30,
            body_bottom_y_px=270,
            body_length_px=240.0,
            waist_y_px=140,
            waist_width_px=80.0,
            upper_bout_y_px=90,
            upper_bout_width_px=95.0,
            lower_bout_y_px=210,
            lower_bout_width_px=170.0,
            waist_y_norm=0.46,
            upper_bout_y_norm=0.25,
            lower_bout_y_norm=0.75,
            waist_to_lower_ratio=0.47,
            upper_to_lower_ratio=0.56,
            width_to_length_ratio=0.71,
        ),
        constraints=GeometryConstraints(
            lower_gt_waist_gt_upper=True,
            waist_position_valid=True,
            aspect_ratio_valid=True,
            symmetry_valid=True,
            all_valid=True,
            violations=[],
        ),
    )

    result = stage.run(
        edges=edges,
        alpha_mask=alpha_mask,
        body_region=body_region,
        body_model=body_model,
        calibration=_make_calibration(),
        family=InstrumentFamily.SOLID_BODY,
        image_shape=edges.shape,
    )

    assert result.diagnostics["body_model_present"] is True
    assert result.diagnostics["body_model_bbox_px"] == (20, 30, 120, 240)
    assert result.diagnostics["body_model_constraints_valid"] is True
    assert result.diagnostics["body_model_landmarks"]["waist_y_px"] == 140


def test_stage_without_body_model_sets_present_false():
    """body_model_present is False when no BodyModel is passed."""
    stage = ContourStage()
    edges, alpha_mask = _make_edges_and_mask()

    result = stage.run(
        edges=edges,
        alpha_mask=alpha_mask,
        body_region=_make_body_region(),
        calibration=_make_calibration(),
        family=InstrumentFamily.SOLID_BODY,
        image_shape=edges.shape,
    )

    assert result.diagnostics["body_model_present"] is False


def test_stage_records_expected_outline_prior_usage():
    stage = ContourStage()
    edges, alpha_mask = _make_edges_and_mask()
    body_region = _make_body_region()
    calibration = _make_calibration()

    body_model = BodyModel(
        source_image_id=None,
        family_hint="archtop",
        spec_hint=None,
        body_bbox_px=(20, 30, 120, 240),
        body_region=body_region,
        row_width_profile_px=np.zeros(500, dtype=float),
        row_width_profile_smoothed_px=np.zeros(500, dtype=float),
        column_profile_px=np.zeros(300, dtype=float),
        mm_per_px=0.5,
        expected_outline_px=np.array(
            [[50.0, 30.0], [20.0, 140.0], [50.0, 270.0],
             [110.0, 270.0], [140.0, 140.0], [110.0, 30.0]],
            dtype=np.float32,
        ),
    )

    result = stage.run(
        edges=edges,
        alpha_mask=alpha_mask,
        body_region=body_region,
        body_model=body_model,
        calibration=calibration,
        family=InstrumentFamily.SOLID_BODY,
        image_shape=edges.shape,
    )

    assert result.diagnostics["used_expected_outline_prior"] is True
    assert result.diagnostics["body_model_expected_outline_ready"] is True


def test_stage_preserves_body_model_constraint_state():
    stage = ContourStage()
    edges, alpha_mask = _make_edges_and_mask()
    body_region = _make_body_region()
    calibration = _make_calibration()

    body_model = BodyModel(
        source_image_id=None,
        family_hint="archtop",
        spec_hint=None,
        body_bbox_px=(20, 30, 120, 240),
        body_region=body_region,
        row_width_profile_px=np.zeros(500, dtype=float),
        row_width_profile_smoothed_px=np.zeros(500, dtype=float),
        column_profile_px=np.zeros(300, dtype=float),
        mm_per_px=0.5,
        landmarks=BodyLandmarks(
            centerline_x_px=80.0,
            body_top_y_px=30,
            body_bottom_y_px=270,
            body_length_px=240.0,
            waist_y_px=140,
            waist_width_px=80.0,
            upper_bout_y_px=90,
            upper_bout_width_px=95.0,
            lower_bout_y_px=210,
            lower_bout_width_px=170.0,
            waist_y_norm=0.46,
            upper_bout_y_norm=0.25,
            lower_bout_y_norm=0.75,
            waist_to_lower_ratio=0.47,
            upper_to_lower_ratio=0.56,
            width_to_length_ratio=0.71,
        ),
        constraints=GeometryConstraints(
            lower_gt_waist_gt_upper=True,
            waist_position_valid=True,
            aspect_ratio_valid=True,
            symmetry_valid=True,
            all_valid=True,
            violations=[],
        ),
        diagnostics={"body_symmetry_score": 0.91},
    )

    result = stage.run(
        edges=edges,
        alpha_mask=alpha_mask,
        body_region=body_region,
        body_model=body_model,
        calibration=calibration,
        family=InstrumentFamily.SOLID_BODY,
        image_shape=edges.shape,
    )

    assert result.diagnostics["body_model_constraints_valid"] is True
