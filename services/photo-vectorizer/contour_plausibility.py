from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def body_ownership_score(
    *,
    completeness: float,
    border_contact: float,
    vertical_coverage: float,
    neck_inclusion: float,
) -> float:
    """
    Score whether a contour plausibly owns the instrument body rather than
    a partial fragment, neck-heavy silhouette, or over-cropped region.

    Inputs are normalized to [0, 1]:
      - completeness: how fully the contour explains the expected body region
      - border_contact: fraction of contour touching image/body-region borders
      - vertical_coverage: normalized body-height coverage within region
      - neck_inclusion: fraction of contour mass likely attributable to neck area

    The function is intentionally conservative:
      - completeness is the dominant positive term
      - heavy border contact is penalized
      - poor vertical coverage is penalized
      - neck inclusion is penalized hardest
    """
    completeness = _clamp01(completeness)
    border_contact = _clamp01(border_contact)
    vertical_coverage = _clamp01(vertical_coverage)
    neck_inclusion = _clamp01(neck_inclusion)

    score = (
        0.50 * completeness
        + 0.25 * vertical_coverage
        + 0.10 * (1.0 - border_contact)
        + 0.15 * (1.0 - neck_inclusion)
    )

    # Hard penalties for the exact failure modes now observed in live images.
    if vertical_coverage < 0.45:
        score -= 0.15
    if border_contact > 0.30:
        score -= 0.10
    if neck_inclusion > 0.25:
        score -= 0.20
    if completeness < 0.55:
        score -= 0.10

    return _clamp01(score)


@dataclass(frozen=True)
class ContourPlausibilityBreakdown:
    completeness_score: float
    border_contact_score: float
    vertical_coverage_score: float
    neck_inclusion_score: float
    ownership_score: float
    total_score: float
    ownership_threshold: float
    ownership_ok: bool


class ContourPlausibilityScorer:
    """
    Scores whether a contour candidate is geometrically plausible as the body.

    This is the ownership-aware scorer that augments the existing
    photo_vectorizer_v2.ContourPlausibilityScorer with a hard body-ownership
    gate.  It operates on raw numpy contours + optional masks/bboxes, not on
    the FeatureContour type used by the V1 scorer.
    """

    def __init__(self, ownership_threshold: float = 0.60) -> None:
        self.ownership_threshold = float(ownership_threshold)

    def score_candidate(
        self,
        contour: np.ndarray,
        *,
        body_region_mask: Optional[np.ndarray] = None,
        image_shape: Optional[tuple[int, int]] = None,
        expected_body_bbox: Optional[tuple[int, int, int, int]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
    ) -> ContourPlausibilityBreakdown:
        diagnostics = diagnostics or {}

        completeness = _clamp01(
            diagnostics.get(
                "completeness_score",
                self._estimate_completeness(
                    contour,
                    body_region_mask=body_region_mask,
                    expected_body_bbox=expected_body_bbox,
                ),
            )
        )
        border_contact = _clamp01(
            diagnostics.get(
                "border_contact_score",
                self._estimate_border_contact(
                    contour,
                    image_shape=image_shape,
                    body_region_mask=body_region_mask,
                ),
            )
        )
        vertical_coverage = _clamp01(
            diagnostics.get(
                "vertical_coverage_score",
                self._estimate_vertical_coverage(
                    contour,
                    body_region_mask=body_region_mask,
                    expected_body_bbox=expected_body_bbox,
                ),
            )
        )
        neck_inclusion = _clamp01(
            diagnostics.get(
                "neck_inclusion_score",
                self._estimate_neck_inclusion(
                    contour,
                    body_region_mask=body_region_mask,
                    expected_body_bbox=expected_body_bbox,
                ),
            )
        )

        ownership = body_ownership_score(
            completeness=completeness,
            border_contact=border_contact,
            vertical_coverage=vertical_coverage,
            neck_inclusion=neck_inclusion,
        )
        ownership_ok = ownership >= self.ownership_threshold

        # Completeness remains part of the full score, but ownership now becomes
        # a first-class hard decision signal.
        total_score = _clamp01(
            0.55 * completeness
            + 0.20 * vertical_coverage
            + 0.10 * (1.0 - border_contact)
            + 0.15 * (1.0 - neck_inclusion)
        )

        # If the contour does not convincingly own the body, cap the total score
        # so high local plausibility cannot override obvious body-misownership.
        if not ownership_ok:
            total_score = min(total_score, 0.59)

        return ContourPlausibilityBreakdown(
            completeness_score=completeness,
            border_contact_score=border_contact,
            vertical_coverage_score=vertical_coverage,
            neck_inclusion_score=neck_inclusion,
            ownership_score=ownership,
            total_score=total_score,
            ownership_threshold=self.ownership_threshold,
            ownership_ok=ownership_ok,
        )

    def annotate_result(
        self,
        result: Any,
        *,
        contour: np.ndarray,
        body_region_mask: Optional[np.ndarray] = None,
        image_shape: Optional[tuple[int, int]] = None,
        expected_body_bbox: Optional[tuple[int, int, int, int]] = None,
    ) -> Any:
        """
        Attach ownership-aware diagnostics to an existing contour-stage result.
        """
        breakdown = self.score_candidate(
            contour,
            body_region_mask=body_region_mask,
            image_shape=image_shape,
            expected_body_bbox=expected_body_bbox,
            diagnostics=getattr(result, "diagnostics", {}) or {},
        )

        diagnostics = dict(getattr(result, "diagnostics", {}) or {})
        diagnostics.update(
            {
                "completeness_score": breakdown.completeness_score,
                "border_contact_score": breakdown.border_contact_score,
                "vertical_coverage_score": breakdown.vertical_coverage_score,
                "neck_inclusion_score": breakdown.neck_inclusion_score,
                "ownership_score": breakdown.ownership_score,
                "ownership_ok": breakdown.ownership_ok,
                "ownership_threshold": breakdown.ownership_threshold,
            }
        )

        export_block_issues = list(getattr(result, "export_block_issues", []) or [])
        if not breakdown.ownership_ok and "body_ownership_failed" not in export_block_issues:
            export_block_issues.append("body_ownership_failed")

        result.diagnostics = diagnostics
        result.ownership_score = breakdown.ownership_score
        result.ownership_ok = breakdown.ownership_ok
        result.export_block_issues = export_block_issues
        result.best_score = min(
            float(getattr(result, "best_score", breakdown.total_score)),
            breakdown.total_score,
        )
        result.export_blocked = bool(
            getattr(result, "export_blocked", False) or not breakdown.ownership_ok
        )
        if not breakdown.ownership_ok:
            result.export_block_reason = "Contour candidate failed body ownership gate."
        return result

    @staticmethod
    def _estimate_completeness(
        contour: np.ndarray,
        *,
        body_region_mask: Optional[np.ndarray],
        expected_body_bbox: Optional[tuple[int, int, int, int]],
    ) -> float:
        if body_region_mask is not None and body_region_mask.size:
            ys, xs = np.where(body_region_mask > 0)
            if len(xs) and len(ys):
                region_area = float(len(xs))
                contour_mask = np.zeros_like(body_region_mask, dtype=np.uint8)
                import cv2

                cv2.drawContours(
                    contour_mask, [contour.astype(np.int32)], -1, 255, thickness=-1
                )
                overlap = float(
                    np.count_nonzero((contour_mask > 0) & (body_region_mask > 0))
                )
                return overlap / max(region_area, 1.0)

        if expected_body_bbox is not None:
            _, _, w, h = expected_body_bbox
            bbox_area = float(max(w, 1) * max(h, 1))
            import cv2

            x, y, cw, ch = cv2.boundingRect(contour.astype(np.int32))
            contour_bbox_area = float(max(cw, 1) * max(ch, 1))
            return min(contour_bbox_area / bbox_area, 1.0)

        return 0.5

    @staticmethod
    def _estimate_border_contact(
        contour: np.ndarray,
        *,
        image_shape: Optional[tuple[int, int]],
        body_region_mask: Optional[np.ndarray],
    ) -> float:
        pts = contour.reshape(-1, 2)
        if pts.size == 0:
            return 1.0

        if image_shape is None and body_region_mask is not None:
            image_shape = body_region_mask.shape[:2]
        if image_shape is None:
            return 0.0

        h, w = image_shape[:2]
        x = pts[:, 0]
        y = pts[:, 1]
        on_border = (x <= 1) | (y <= 1) | (x >= (w - 2)) | (y >= (h - 2))
        return float(np.mean(on_border.astype(np.float32)))

    @staticmethod
    def _estimate_vertical_coverage(
        contour: np.ndarray,
        *,
        body_region_mask: Optional[np.ndarray],
        expected_body_bbox: Optional[tuple[int, int, int, int]],
    ) -> float:
        import cv2

        _, cy, _, ch = cv2.boundingRect(contour.astype(np.int32))
        contour_h = float(max(ch, 1))

        if body_region_mask is not None and body_region_mask.size:
            ys, _ = np.where(body_region_mask > 0)
            if len(ys):
                region_h = float(max(int(ys.max()) - int(ys.min()) + 1, 1))
                return min(contour_h / region_h, 1.0)

        if expected_body_bbox is not None:
            _, _, _, h = expected_body_bbox
            return min(contour_h / float(max(h, 1)), 1.0)

        return 0.5

    @staticmethod
    def _estimate_neck_inclusion(
        contour: np.ndarray,
        *,
        body_region_mask: Optional[np.ndarray],
        expected_body_bbox: Optional[tuple[int, int, int, int]],
    ) -> float:
        """
        Heuristic: upper slender extension above the expected body centroid region
        is treated as likely neck inclusion.
        """
        import cv2

        x, y, w, h = cv2.boundingRect(contour.astype(np.int32))
        if h <= 0:
            return 1.0

        pts = contour.reshape(-1, 2)
        y_cut = y + int(0.28 * h)
        upper_pts = pts[pts[:, 1] <= y_cut]
        if len(upper_pts) == 0:
            return 0.0

        upper_width = float(upper_pts[:, 0].max() - upper_pts[:, 0].min() + 1)
        full_width = float(max(w, 1))
        narrowness = 1.0 - min(upper_width / full_width, 1.0)
        upper_fraction = float(len(upper_pts)) / float(max(len(pts), 1))

        score = 0.65 * narrowness + 0.35 * min(upper_fraction * 2.0, 1.0)
        return _clamp01(score)
