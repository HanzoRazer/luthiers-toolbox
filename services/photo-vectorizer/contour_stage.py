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

from photo_vectorizer_v2 import (
    BodyRegion,
    CalibrationResult,
    ContourAssembler,
    ContourMerger,
    ContourPlausibilityScorer,
    ContourScore,
    ContourStageResult,
    EXPORT_BLOCK_THRESHOLD,
    FeatureClassifier,
    FeatureContour,
    FeatureType,
    InstrumentFamily,
    MergeResult,
    elect_body_contour_v2,
)

logger = logging.getLogger(__name__)


# ── Stage parameters (tunable by coach) ────────────────────────────────────

@dataclass
class StageParams:
    """Tunable parameters for contour stage — the knobs a coach can adjust."""
    # ContourMerger knobs
    merge_max_close_px: int = 120
    merge_min_fragment_area: float = 2000.0
    merge_max_fragments: int = 8
    merge_body_overlap_min: float = 0.40
    # Body election knobs
    elect_min_overlap: float = 0.50
    elect_max_width_factor: float = 1.30
    # Assembler knobs
    min_contour_area_px: int = 3000
    # Scorer knobs
    scorer_border_margin_px: int = 5
    scorer_neck_height_factor: float = 1.35
    scorer_min_solidity: float = 0.55
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

        Returns
        -------
        ContourStageResult
            Complete typed record of the stage execution.
        """
        p = params or StageParams()
        mpp = calibration.mm_per_px
        img_h, img_w = image_shape

        # ── 8a: Contour assembly ────────────────────────────────────────
        classifier = FeatureClassifier()
        assembler = ContourAssembler(classifier, p.min_contour_area_px)
        feature_contours = assembler.assemble(edges, alpha_mask, mpp)

        if not feature_contours:
            logger.warning("ContourStage: no contours found")
            return ContourStageResult(
                diagnostics={"error": "no_contours_found"},
            )

        # Snapshot pre-merge
        pre_merge_contours = list(feature_contours)

        # ── 8b: Score pre-merge candidates ──────────────────────────────
        scorer = ContourPlausibilityScorer(
            border_margin_px=p.scorer_border_margin_px,
            neck_height_factor=p.scorer_neck_height_factor,
            min_solidity=p.scorer_min_solidity,
        )
        scores_pre = scorer.score_all_candidates(
            pre_merge_contours, body_region, family, mpp, image_shape)

        # ── 8c: Merge fragmented bodies ─────────────────────────────────
        merger = ContourMerger(
            max_close_px=p.merge_max_close_px,
            min_fragment_area=p.merge_min_fragment_area,
            max_fragments=p.merge_max_fragments,
            body_overlap_min=p.merge_body_overlap_min,
        )
        merge_result = merger.merge(
            feature_contours, image_shape,
            body_region=body_region, mpp=mpp)

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
            post_merge_contours, body_region, family, mpp, image_shape)

        # ── 8e: Diagnostic plausibility election (logged only) ──────────
        best_idx, elected_source, best_score = \
            scorer.elect_best(scores_pre, scores_post)
        logger.info(
            f"ContourStage diagnostic: best={elected_source} "
            f"idx={best_idx} score={best_score:.3f}")

        # ── 8f: Actual body election (proven X-extent guard) ────────────
        body_idx = elect_body_contour_v2(
            feature_contours, body_region,
            min_overlap=p.elect_min_overlap,
            max_width_factor=p.elect_max_width_factor)

        if body_idx >= 0:
            body_fc = feature_contours[body_idx]
            if body_fc.feature_type != FeatureType.BODY_OUTLINE:
                body_fc.feature_type = FeatureType.BODY_OUTLINE
                body_fc.confidence = 0.7
        else:
            body_fc = max(feature_contours, key=lambda c: c.area_px)
            body_fc.feature_type = FeatureType.BODY_OUTLINE
            body_fc.confidence = 0.7

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
            diagnostics={
                "n_pre_merge": len(pre_merge_contours),
                "n_post_merge": len(post_merge_contours),
                "n_scored_pre": len(scores_pre),
                "n_scored_post": len(scores_post),
                "family": family,
                "merge_warnings": merge_warnings,
            },
        )

        # ── 8h: Enriched export blocking ────────────────────────────────
        elected_scores = scores_post if elected_source == "post_merge" \
            else scores_pre
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
            }
            contour_stage.export_block_issues = list(best_cs.issues)

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
