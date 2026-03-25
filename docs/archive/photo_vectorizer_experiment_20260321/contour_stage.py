"""
Contour Stage — Extracted Stage 8 Pipeline Module
==================================================

Encapsulates the full contour decision pipeline:
  - Contour assembly from edges
  - Body fragment merging (Patch 17)
  - Plausibility scoring (pre/post merge)
  - Body election (X-extent guard)
  - Grid zone reclassification
  - Export blocking with enriched diagnostics

This is the seam the future GeometryCoach inspects and can request reruns on.

Usage:
    from contour_stage import ContourStage
    stage = ContourStage()
    result = stage.run(
        edges=edge_image,
        alpha_mask=alpha_mask,
        body_region=body_region,
        calibration=calibration,
        family=family_str,
        image_shape=(h, w),
        image=original_image,   # needed for grid overlay debug
        params=StageParams(),
    )
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from grid_classify import PhotoGridClassifier, merge_classifications
from body_model import BodyModel

# Optional: scipy Hausdorff for fast distance computation; pure-numpy fallback
try:
    from scipy.spatial.distance import directed_hausdorff as _scipy_directed_hausdorff
    _SCIPY_HAUSDORFF = True
except ImportError:
    _SCIPY_HAUSDORFF = False

from photo_vectorizer_v2 import (
    BodyRegion,
    CalibrationResult,
    ContourAssembler,
    ContourMerger,
    ContourPlausibilityScorer,
    ContourScore,
    ContourStageResult,
    EXPORT_BLOCK_THRESHOLD,
    elect_body_contour_against_expected_outline,
    elect_body_contour_v2,
    FeatureClassifier,
    FeatureContour,
    FeatureType,
    InstrumentFamily,
    INSTRUMENT_SPECS,
    MergeResult,
    ScaleSource,
)

logger = logging.getLogger(__name__)


# ── Hausdorff distance helper (Diff 3) ─────────────────────────────────────

def _hausdorff_distance(pts_a: np.ndarray, pts_b: np.ndarray) -> float:
    """
    Compute the symmetric Hausdorff distance between two point sets.

    Uses scipy if available (faster), otherwise falls back to a pure-numpy
    implementation that sub-samples both arrays to keep runtime bounded.

    Both inputs should be (N, 2) float arrays in pixel space.
    Returns the maximum directed Hausdorff in pixels.
    """
    if pts_a is None or pts_b is None or len(pts_a) < 3 or len(pts_b) < 3:
        return float("inf")

    a = pts_a.reshape(-1, 2).astype(np.float32)
    b = pts_b.reshape(-1, 2).astype(np.float32)

    if _SCIPY_HAUSDORFF:
        d_ab = _scipy_directed_hausdorff(a, b)[0]
        d_ba = _scipy_directed_hausdorff(b, a)[0]
        return float(max(d_ab, d_ba))

    # Pure-numpy fallback: sub-sample to ≤200 points each side to cap O(N²)
    max_pts = 200
    if len(a) > max_pts:
        idx = np.round(np.linspace(0, len(a) - 1, max_pts)).astype(int)
        a = a[idx]
    if len(b) > max_pts:
        idx = np.round(np.linspace(0, len(b) - 1, max_pts)).astype(int)
        b = b[idx]

    # directed: for each point in a, min distance to any point in b
    def _directed(src: np.ndarray, dst: np.ndarray) -> float:
        diff = src[:, None, :] - dst[None, :, :]          # (M, N, 2)
        dist = np.sqrt((diff ** 2).sum(axis=2))            # (M, N)
        return float(dist.min(axis=1).max())

    return max(_directed(a, b), _directed(b, a))

@dataclass
class StageParams:
    """Tunable parameters for contour stage — the knobs a coach can adjust."""
    # ContourMerger knobs
    merge_max_close_px: int = 120
    merge_min_fragment_area: float = 2000.0
    merge_max_fragments: int = 8
    merge_body_overlap_min: float = 0.40
    merge_guard_epsilon: float = 0.03
    # Body election knobs
    elect_min_overlap: float = 0.50
    elect_max_width_factor: float = 1.30
    # Assembler knobs
    min_contour_area_px: int = 3000
    # Scorer knobs
    scorer_border_margin_px: int = 5
    scorer_neck_height_factor: float = 1.35
    scorer_min_solidity: float = 0.55
    scorer_ownership_threshold: float = 0.60
    # Export threshold
    export_block_threshold: float = EXPORT_BLOCK_THRESHOLD


# ── The extracted stage ────────────────────────────────────────────────────

class ContourStage:
    """
    Standalone Stage 8 pipeline.

    Can be invoked independently for testing, replaying failure cases,
    or coaching-loop reruns with alternate parameters.
    """

    def run(
        self,
        edges: np.ndarray,
        alpha_mask: np.ndarray,
        body_region: Optional[BodyRegion],
        calibration: CalibrationResult,
        family: str,
        image_shape: Tuple[int, int],
        image: Optional[np.ndarray] = None,
        params: Optional[StageParams] = None,
        debug_images: bool = False,
        spec_name: Optional[str] = None,  # For two-pass calibration
        body_model: Optional[BodyModel] = None,  # Diff 2: typed geometry handoff
    ) -> ContourStageResult:
        """
        Execute the full contour decision pipeline.

        Parameters
        ----------
        edges : np.ndarray
            Binary edge image from Stage 5.
        alpha_mask : np.ndarray
            Foreground mask from Stage 4.
        body_region : BodyRegion or None
            Isolated body bounding box from Stage 6.
        calibration : CalibrationResult
            Scale calibration from Stage 7.
        family : str
            Instrument family string (InstrumentFamily constant).
        image_shape : (int, int)
            (height, width) of the original image.
        image : np.ndarray or None
            Original image (needed only for grid overlay debug).
        params : StageParams or None
            Tunable parameters. Defaults used if None.
        debug_images : bool
            Whether to generate debug overlay images.
        body_model : BodyModel or None
            Typed geometry handoff from Diff 2. When present, its body_region
            takes precedence over the bare body_region argument. Landmarks and
            constraints are surfaced in diagnostics. Diff 3 will use
            body_model.expected_outline_px to rewrite election.

        Returns
        -------
        ContourStageResult
            Complete typed record of the stage execution.
        """
        p = params or StageParams()
        mpp = calibration.mm_per_px
        img_h, img_w = image_shape

        # When a BodyModel is present, prefer its typed body_region over the
        # bare argument. This is the backward-compatible Diff 2 wire-up.
        effective_body_region = (
            body_model.body_region
            if body_model is not None and body_model.body_region is not None
            else body_region
        )

        # ── 8a: Contour assembly (TWO-PASS when scale is uncertain) ─────
        # Pass 1: Assemble contours with current mm_per_px
        # Ownership pre-filter applied when effective_body_region is available.
        classifier = FeatureClassifier()
        assembler = ContourAssembler(classifier, p.min_contour_area_px)
        feature_contours = assembler.assemble(
            edges, alpha_mask, mpp, body_region=effective_body_region
        )

        if not feature_contours:
            logger.warning("ContourStage: no contours found")
            return ContourStageResult(
                diagnostics={"error": "no_contours_found"},
            )

        # ── TWO-PASS CALIBRATION ────────────────────────────────────────
        # If scale source is unreliable (ASSUMED_DPI, ESTIMATED_RENDER_DPI)
        # and spec_name is provided, recalibrate using actual body contour height
        # and re-classify all contours with the corrected mm_per_px.
        low_confidence_sources = (ScaleSource.ASSUMED_DPI, ScaleSource.ESTIMATED_RENDER_DPI)
        if (calibration.source in low_confidence_sources
                and spec_name and spec_name in INSTRUMENT_SPECS):
            # Find body contour (largest)
            body_candidate = max(feature_contours, key=lambda c: c.area_px)
            body_height_px = body_candidate.bbox_px[3]  # h from (x, y, w, h)

            if body_height_px > 0:
                spec_body_mm = INSTRUMENT_SPECS[spec_name]["body"][0]
                corrected_mpp = spec_body_mm / body_height_px

                logger.info(
                    f"Two-pass calibration: {calibration.source.value} -> INSTRUMENT_SPEC "
                    f"(body {spec_body_mm}mm / {body_height_px}px = {corrected_mpp:.4f} mm/px)")

                # Pass 2: Re-classify all contours with corrected scale.
                # Update body_model.mm_per_px so spec fitting reflects the
                # corrected measurement.
                mpp = corrected_mpp
                if body_model is not None:
                    body_model.mm_per_px = corrected_mpp
                    logger.info(
                        "Two-pass: updated body_model.mm_per_px to corrected value"
                    )
                feature_contours = assembler.assemble(
                    edges, alpha_mask, mpp, body_region=effective_body_region
                )

                if not feature_contours:
                    logger.warning("ContourStage: no contours after recalibration")
                    return ContourStageResult(
                        diagnostics={"error": "no_contours_after_recalibration"},
                    )

        # Snapshot pre-merge
        pre_merge_contours = list(feature_contours)

        # ── 8b: Score pre-merge candidates ──────────────────────────────
        scorer = ContourPlausibilityScorer(
            border_margin_px=p.scorer_border_margin_px,
            neck_height_factor=p.scorer_neck_height_factor,
            min_solidity=p.scorer_min_solidity,
            ownership_threshold=p.scorer_ownership_threshold,
        )
        scores_pre = scorer.score_all_candidates(
            pre_merge_contours, effective_body_region, family, mpp, image_shape)
        pre_best = max(scores_pre, key=lambda s: s.score) if scores_pre else None
        pre_best_fc = pre_merge_contours[pre_best.contour_index] if pre_best is not None else None

        # ── 8c: Merge fragmented bodies ─────────────────────────────────
        merger = ContourMerger(
            max_close_px=p.merge_max_close_px,
            min_fragment_area=p.merge_min_fragment_area,
            max_fragments=p.merge_max_fragments,
            body_overlap_min=p.merge_body_overlap_min,
        )
        merge_result = merger.merge(
            feature_contours, image_shape,
            body_region=effective_body_region, mpp=mpp)

        merge_warnings: List[str] = []
        if merge_result is not None:
            merged_fc = FeatureContour(
                points_px=merge_result.merged_contour,
                feature_type=FeatureType.BODY_OUTLINE,
                confidence=0.85,
                area_px=float(cv2.contourArea(merge_result.merged_contour)),
                bbox_px=merge_result.bbox_px,
                hash_id=hashlib.md5(
                    merge_result.merged_contour.tobytes()).hexdigest()[:12],
            )
            feature_contours.append(merged_fc)
            merge_warnings.append(
                f"Body fragmented into {merge_result.n_fragments} parts "
                f"-- merged with {merge_result.close_kernel_px}x"
                f"{merge_result.close_kernel_px}px kernel")

        # Snapshot post-merge
        post_merge_contours = list(feature_contours)

        # ── 8d: Score post-merge candidates ─────────────────────────────
        scores_post = scorer.score_all_candidates(
            post_merge_contours, effective_body_region, family, mpp, image_shape)
        post_best = max(scores_post, key=lambda s: s.score) if scores_post else None
        post_best_fc = post_merge_contours[post_best.contour_index] if post_best is not None else None

        # ── 8e: Diagnostic plausibility election (logged only) ──────────
        best_idx, elected_source, best_score = \
            scorer.elect_best(scores_pre, scores_post)
        logger.info(
            f"ContourStage diagnostic: best={elected_source} "
            f"idx={best_idx} score={best_score:.3f}")

        # ── 8f: Actual body election ─────────────────────────────────────
        # Diff 3: if a BodyModel with a generated expected outline is
        # present, rank ownership-passing candidates by Hausdorff distance
        # to the expected outline ("closest to expected" election).
        # Fall back to the proven ownership-area election otherwise.
        post_ownership_scores = {
            cs.contour_index: float(cs.ownership_score)
            for cs in scores_post
        }

        election_method = "ownership_area"  # default

        expected_outline = (
            body_model.expected_outline_px
            if body_model is not None
            else None
        )

        if expected_outline is not None and len(feature_contours) > 0:
            body_idx = elect_body_contour_against_expected_outline(
                feature_contours,
                expected_outline,
                ownership_scores=post_ownership_scores,
                ownership_threshold=p.scorer_ownership_threshold,
            )
            if body_idx >= 0:
                election_method = "expected_outline_prior"
                spec_name = (
                    body_model.spec_delta.spec_name
                    if body_model is not None and body_model.spec_delta is not None
                    else "landmark_only"
                )
                logger.info(
                    f"Expected-outline election: elected idx={body_idx} "
                    f"(spec={spec_name})"
                )
            else:
                # No ownership-passing candidate — fall back
                body_idx = elect_body_contour_v2(
                    feature_contours, effective_body_region,
                    min_overlap=p.elect_min_overlap,
                    max_width_factor=p.elect_max_width_factor,
                    ownership_scores=post_ownership_scores,
                    ownership_threshold=p.scorer_ownership_threshold,
                )
                election_method = "ownership_area_fallback"
                logger.info(
                    "Expected-outline election: no ownership-passing candidates — "
                    "falling back to ownership-area election"
                )
        else:
            # No expected outline available — standard election
            body_idx = elect_body_contour_v2(
                feature_contours, effective_body_region,
                min_overlap=p.elect_min_overlap,
                max_width_factor=p.elect_max_width_factor,
                ownership_scores=post_ownership_scores,
                ownership_threshold=p.scorer_ownership_threshold,
            )

        if body_idx >= 0:
            body_fc = feature_contours[body_idx]
            if body_fc.feature_type != FeatureType.BODY_OUTLINE:
                body_fc.feature_type = FeatureType.BODY_OUTLINE
                body_fc.confidence = 0.7
        else:
            body_fc = max(feature_contours, key=lambda c: c.area_px)
            body_fc.feature_type = FeatureType.BODY_OUTLINE
            body_fc.confidence = 0.7

        # ── Merge guard ─────────────────────────────────────────────────
        # If the best pre-merge candidate materially outperforms the best
        # post-merge candidate, prefer the pre-merge body candidate.
        pre_best_score = float(pre_best.score) if pre_best is not None else 0.0
        post_best_score = float(post_best.score) if post_best is not None else 0.0

        merge_guard_diag: Dict[str, Any] = {}
        if (
            pre_best is not None
            and pre_best_fc is not None
            and pre_best_score > (post_best_score + p.merge_guard_epsilon)
        ):
            body_fc = pre_best_fc
            elected_source = "pre_merge_guarded"
            best_score = pre_best_score
            merge_guard_diag["merge_guard_triggered"] = True
            merge_guard_diag["merge_guard_reason"] = (
                f"pre-merge best score {pre_best_score:.3f} "
                f"> post-merge best score {post_best_score:.3f} "
                f"+ \u03b5 {p.merge_guard_epsilon:.3f}"
            )
            logger.info(
                f"Merge guard triggered: pre-merge {pre_best_score:.3f} "
                f"> post-merge {post_best_score:.3f} "
                f"+ \u03b5 {p.merge_guard_epsilon:.3f}")
        else:
            merge_guard_diag["merge_guard_triggered"] = False
            merge_guard_diag["merge_guard_reason"] = None

        # ── 8g: Build stage result ──────────────────────────────────────
        contour_stage = ContourStageResult(
            feature_contours_pre_merge=pre_merge_contours,
            merge_result=merge_result,
            feature_contours_post_merge=post_merge_contours,
            body_contour_pre_grid=body_fc,
            contour_scores_pre=scores_pre,
            contour_scores_post=scores_post,
            elected_source=elected_source,
            best_score=best_score,
            pre_merge_best_contour=pre_best_fc,
            post_merge_best_contour=post_best_fc,
            diagnostics={
                "n_pre_merge": len(pre_merge_contours),
                "n_post_merge": len(post_merge_contours),
                "n_scored_pre": len(scores_pre),
                "n_scored_post": len(scores_post),
                "family": family,
                "merge_warnings": merge_warnings,
                "body_ownership_gate_failed": body_idx < 0,
                **merge_guard_diag,
            },
        )

        # ── Diff 2: surface BodyModel geometry in diagnostics ───────────
        if body_model is not None:
            contour_stage.diagnostics["body_model_present"] = True
            contour_stage.diagnostics["body_model_bbox_px"] = tuple(body_model.body_bbox_px)
            contour_stage.diagnostics["body_model_constraints_valid"] = (
                None if body_model.constraints is None
                else body_model.constraints.all_valid
            )
            if body_model.landmarks is not None:
                contour_stage.diagnostics["body_model_landmarks"] = {
                    "waist_y_px": body_model.landmarks.waist_y_px,
                    "waist_width_px": body_model.landmarks.waist_width_px,
                    "upper_bout_y_px": body_model.landmarks.upper_bout_y_px,
                    "upper_bout_width_px": body_model.landmarks.upper_bout_width_px,
                    "lower_bout_y_px": body_model.landmarks.lower_bout_y_px,
                    "lower_bout_width_px": body_model.landmarks.lower_bout_width_px,
                }
            if body_model.constraints is not None:
                contour_stage.diagnostics["body_model_constraint_violations"] = list(
                    body_model.constraints.violations
                )
            # ── Diff 3: spec-prior election diagnostics ──────────────────
            contour_stage.diagnostics["election_method"] = election_method
            contour_stage.diagnostics["used_expected_outline_prior"] = (
                election_method == "expected_outline_prior"
            )
            contour_stage.diagnostics["body_model_expected_outline_ready"] = (
                body_model.expected_outline_px is not None
            )
            if body_model.spec_delta is not None:
                contour_stage.diagnostics["spec_fit_name"] = body_model.spec_delta.spec_name
                contour_stage.diagnostics["spec_fit_score"] = body_model.spec_delta.fit_score
        else:
            contour_stage.diagnostics["body_model_present"] = False
            contour_stage.diagnostics["election_method"] = election_method
            contour_stage.diagnostics["used_expected_outline_prior"] = False

        # ── 8h: Enriched export blocking ────────────────────────────────
        elected_scores = scores_pre if elected_source in ("pre_merge", "pre_merge_guarded") \
            else scores_post
        best_cs = max(elected_scores, key=lambda s: s.score) \
            if elected_scores else None

        if best_cs is not None:
            contour_stage.export_block_score_breakdown = {
                "composite": best_cs.score,
                "completeness": best_cs.completeness,
                "dimension_plausibility": best_cs.dimension_plausibility,
                "symmetry": best_cs.symmetry_score,
                "aspect_ratio_ok": 1.0 if best_cs.aspect_ratio_ok else 0.0,
                "border_contact": 0.0 if best_cs.border_contact else 1.0,
                "includes_neck": 0.0 if best_cs.includes_neck else 1.0,
                "ownership_score": best_cs.ownership_score,
                "vertical_coverage": best_cs.vertical_coverage,
                "neck_inclusion_score": 1.0 - best_cs.neck_inclusion_score,
            }
            contour_stage.export_block_issues = list(best_cs.issues)
            contour_stage.ownership_score = float(best_cs.ownership_score)
            contour_stage.ownership_ok = bool(
                best_cs.ownership_score >= p.scorer_ownership_threshold
            )

        if body_idx < 0:
            contour_stage.export_blocked = True
            contour_stage.block_reason = (
                f"No contour passed body ownership threshold "
                f"{p.scorer_ownership_threshold:.2f}"
            )
            contour_stage.recommended_next_action = "rerun_body_isolation"
            if "body_ownership_failed" not in contour_stage.export_block_issues:
                contour_stage.export_block_issues.append("body_ownership_failed")

        if best_score < p.export_block_threshold:
            contour_stage.export_blocked = True
            contour_stage.block_reason = (
                f"Best plausibility score {best_score:.3f} below threshold "
                f"{p.export_block_threshold}")

            # Determine recommended next action
            pre_post_disagree = (
                scores_pre and scores_post
                and abs(max(s.score for s in scores_pre)
                        - max(s.score for s in scores_post)) > 0.05
            )
            if pre_post_disagree and merge_result is not None:
                contour_stage.recommended_next_action = \
                    "rerun_contour_stage_with_alt_merge_profile"
            else:
                contour_stage.recommended_next_action = \
                    "manual_review_required"

            logger.warning(
                f"ContourStage export blocked: {contour_stage.block_reason}")

        # ── 8.5: Grid zone reclassification ─────────────────────────────
        grid_reclassified = 0
        grid_overlay_path: Optional[str] = None
        body_bbox_px = body_fc.bbox_px if body_fc else None

        if body_bbox_px:
            grid_clf = PhotoGridClassifier()
            for fc in feature_contours:
                if fc is body_fc:
                    fc.grid_zone = "BODY_OUTLINE"
                    fc.grid_confidence = 1.0
                    continue
                gc = grid_clf.classify_contour_px(fc.bbox_px, body_bbox_px)
                fc.grid_zone = gc.primary_category
                fc.grid_notes = gc.notes

                final_feat, final_conf, reason = merge_classifications(
                    fc.feature_type.value, fc.confidence, gc)
                try:
                    new_type = FeatureType(final_feat)
                except ValueError:
                    new_type = fc.feature_type

                if new_type != fc.feature_type:
                    logger.info(
                        f"Grid reclassify: {fc.feature_type.value} -> "
                        f"{new_type.value} ({reason})")
                    fc.feature_type = new_type
                    grid_reclassified += 1
                fc.confidence = final_conf
                fc.grid_confidence = gc.grid_confidence

            logger.info(
                f"Grid re-classification: {grid_reclassified}/"
                f"{len(feature_contours)} changed")

            if debug_images and image is not None:
                contour_bboxes = [
                    fc.bbox_px for fc in feature_contours if fc is not body_fc]
                classifications = [
                    grid_clf.classify_contour_px(fc.bbox_px, body_bbox_px)
                    for fc in feature_contours if fc is not body_fc]
                grid_overlay_path = "__grid_overlay__"  # caller writes file
                contour_stage.diagnostics["grid_overlay_data"] = {
                    "contour_bboxes": contour_bboxes,
                    "n_classifications": len(classifications),
                }

        # ── Finalize ────────────────────────────────────────────────────
        contour_stage.feature_contours_post_grid = list(feature_contours)
        contour_stage.body_contour_final = body_fc
        contour_stage.diagnostics["grid_reclassified"] = grid_reclassified

        return contour_stage
