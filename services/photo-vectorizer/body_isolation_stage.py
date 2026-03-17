from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from body_isolation_result import (
    BodyIsolationResult,
    BodyIsolationSignalBreakdown,
)


@dataclass
class BodyIsolationParams:
    """
    Tunable knobs for body isolation retries.

    Start conservative. These can be widened later as coaching learns.
    Default values reproduce the baseline pipeline behavior.
    Retry profiles modify these values conservatively.
    """
    body_width_min_pct: float = 0.40
    smooth_window: int = 15
    use_adaptive: bool = False

    # Retry-oriented controls
    lower_bound_expand_pct: float = 0.00
    upper_bound_expand_pct: float = 0.00
    border_ignore_px: int = 0
    dark_threshold: int = 150
    min_fg_coverage_pct: float = 0.05

    # Border trim (used by border_suppression profile)
    border_trim_px: int = 0

    # Region expansion / recovery controls (used by body_region_expansion)
    bbox_expand_ratio: float = 0.0
    allow_vertical_growth: bool = False
    allow_lower_bout_growth: bool = False

    # Export / review hints
    review_threshold: float = 0.45

    # Named retry profile (None = baseline behavior)
    profile: Optional[str] = None


# -------------------------------------------------------------------------
# Retry profile definitions
# -------------------------------------------------------------------------

RETRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "lower_bout_recovery": {
        "lower_bound_expand_pct": 0.15,
        "body_width_min_pct": 0.35,
        "smooth_window": 15,
        "use_adaptive": True,
        "border_ignore_px": 6,
        "border_trim_px": 0,
    },
    "border_suppression": {
        "body_width_min_pct": 0.32,
        "smooth_window": 21,
        "use_adaptive": True,
        "border_ignore_px": 10,
        "border_trim_px": 8,
        "upper_bound_expand_pct": 0.02,
    },
    "body_region_expansion": {
        "lower_bound_expand_pct": 0.18,
        "upper_bound_expand_pct": 0.06,
        "body_width_min_pct": 0.30,
        "smooth_window": 17,
        "use_adaptive": True,
        "border_ignore_px": 6,
        "border_trim_px": 0,
        "bbox_expand_ratio": 0.10,
        "allow_vertical_growth": True,
        "allow_lower_bout_growth": True,
    },
}


def _apply_retry_profile(params: BodyIsolationParams) -> BodyIsolationParams:
    """
    Return modified params if a retry profile is requested.

    Baseline behavior remains unchanged when profile is None.
    """
    if not params.profile:
        return params

    profile = RETRY_PROFILES.get(params.profile)
    if not profile:
        return params

    overrides = {k: v for k, v in profile.items() if hasattr(params, k)}
    return replace(params, **overrides)


class BodyIsolationStage:
    """
    Stage 4.5 wrapper around the existing BodyIsolator.

    This is intentionally a wrapper, not a rewrite, so we can:
      1. preserve existing behavior
      2. emit typed diagnostics
      3. support coach-driven retries with alternate params
    """

    def __init__(self, body_isolator: Any):
        self.body_isolator = body_isolator

    def run(
        self,
        image: np.ndarray,
        *,
        fg_mask: Optional[np.ndarray] = None,
        original_image: Optional[np.ndarray] = None,
        instrument_family: Optional[Any] = None,
        geometry_authority: Optional[Any] = None,
        params: Optional[BodyIsolationParams] = None,
    ) -> BodyIsolationResult:
        params = params or BodyIsolationParams()

        # Apply retry profile adjustments (no-op for default run)
        params = _apply_retry_profile(params)

        # Configure the existing BodyIsolator instance temporarily
        prev_body_width_min = getattr(self.body_isolator, "body_width_min", None)
        prev_smooth_window = getattr(self.body_isolator, "smooth_window", None)
        prev_use_adaptive = getattr(self.body_isolator, "use_adaptive", None)

        try:
            self.body_isolator.body_width_min = params.body_width_min_pct
            self.body_isolator.smooth_window = params.smooth_window
            self.body_isolator.use_adaptive = params.use_adaptive

            # Apply border trim to fg_mask if profile requests it
            trimmed_mask = fg_mask
            if params.border_trim_px > 0 and fg_mask is not None:
                trimmed_mask = fg_mask.copy()
                trim = params.border_trim_px
                trimmed_mask[:trim, :] = 0
                trimmed_mask[-trim:, :] = 0
                trimmed_mask[:, :trim] = 0
                trimmed_mask[:, -trim:] = 0

            body_region = self.body_isolator.isolate(
                image,
                fg_mask=trimmed_mask,
                original_image=original_image,
            )
        finally:
            # Restore previous values to avoid global side-effects
            if prev_body_width_min is not None:
                self.body_isolator.body_width_min = prev_body_width_min
            if prev_smooth_window is not None:
                self.body_isolator.smooth_window = prev_smooth_window
            if prev_use_adaptive is not None:
                self.body_isolator.use_adaptive = prev_use_adaptive

        # BodyRegion attributes: x, y, width, height (not x_px/y_px/width_px)
        body_bbox_px = (
            int(getattr(body_region, "x", 0)),
            int(getattr(body_region, "y", 0)),
            int(getattr(body_region, "width", 0)),
            int(getattr(body_region, "height", 0)),
        )
        raw_body_bbox_px = body_bbox_px
        expanded_body_bbox_px = self._expand_body_bbox(
            image_shape=image.shape[:2],
            bbox=raw_body_bbox_px,
            params=params,
        )

        result = BodyIsolationResult(
            body_bbox_px=expanded_body_bbox_px,
            body_region=body_region,
            confidence=float(getattr(body_region, "confidence", 0.0)),
        )

        # Build an ownership-aware isolation mask.
        # For body_region_expansion retries this must materially differ from the
        # baseline bbox rectangle or the retry cannot change downstream geometry.
        result.isolation_mask = self._make_isolation_mask(
            image_shape=image.shape[:2],
            bbox=expanded_body_bbox_px,
            fg_mask=trimmed_mask,
            params=params,
        )

        # Collect profiles / diagnostics
        profile_mask = (
            result.isolation_mask
            if (
                params.bbox_expand_ratio > 0.0
                or params.allow_vertical_growth
                or params.allow_lower_bout_growth
            )
            else trimmed_mask
        )
        profiles = self._compute_profiles(
            image=image,
            fg_mask=profile_mask,
            original_image=original_image,
            body_bbox_px=expanded_body_bbox_px,
            params=params,
        )
        result.row_width_profile = profiles["row_width_profile"]
        result.row_width_profile_smoothed = profiles["row_width_profile_smoothed"]
        result.column_profile = profiles["column_profile"]
        result.source = profiles["source"]
        result.detected_body_center_px = profiles["detected_body_center_px"]
        result.diagnostics.update(profiles["diagnostics"])
        result.diagnostics.update(
            {
                "retry_profile_used": params.profile,
                "raw_body_bbox_px": raw_body_bbox_px,
                "expanded_body_bbox_px": expanded_body_bbox_px,
                "bbox_expand_ratio": float(params.bbox_expand_ratio),
                "allow_vertical_growth": bool(params.allow_vertical_growth),
                "allow_lower_bout_growth": bool(params.allow_lower_bout_growth),
            }
        )

        # Score body ownership
        self._score_body_isolation(
            result,
            image_shape=image.shape[:2],
            instrument_family=instrument_family,
            geometry_authority=geometry_authority,
            params=params,
        )

        # Apply review guidance
        if result.completeness_score < params.review_threshold:
            result.review_required = True
            result.recommended_next_action = "rerun_body_isolation"

        return result

    def _compute_profiles(
        self,
        *,
        image: np.ndarray,
        fg_mask: Optional[np.ndarray],
        original_image: Optional[np.ndarray],
        body_bbox_px: Tuple[int, int, int, int],
        params: BodyIsolationParams,
    ) -> Dict[str, Any]:
        h, w = image.shape[:2]
        x, y, bw, bh = body_bbox_px

        source = "unknown"
        diagnostics: Dict[str, Any] = {}

        if fg_mask is not None and np.sum(fg_mask > 0) > (h * w * params.min_fg_coverage_pct):
            row_widths = np.sum(fg_mask > 0, axis=1).astype(float)
            source = "fg_mask"
        elif original_image is not None:
            gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY) if original_image.ndim == 3 else original_image
            row_widths = np.sum(gray < params.dark_threshold, axis=1).astype(float)
            source = "original_image"
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
            row_widths = np.sum(gray < params.dark_threshold, axis=1).astype(float)
            source = "image_raw"

        kernel = np.ones(max(1, params.smooth_window), dtype=np.float32) / max(1, params.smooth_window)
        smoothed = np.convolve(row_widths, kernel, mode="same")

        # Column profile inside body bbox (best-effort)
        x0 = max(0, x)
        x1 = min(w, x + bw)
        y0 = max(0, y)
        y1 = min(h, y + bh)

        if fg_mask is not None and y1 > y0 and x1 > x0:
            strip = fg_mask[y0:y1, x0:x1]
            column_profile = np.sum(strip > 0, axis=0).astype(float)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
            strip = (gray[y0:y1, x0:x1] < params.dark_threshold).astype(np.uint8)
            column_profile = np.sum(strip > 0, axis=0).astype(float)

        diagnostics["row_width_max"] = float(smoothed.max()) if len(smoothed) else 0.0
        diagnostics["row_width_mean"] = float(smoothed.mean()) if len(smoothed) else 0.0
        diagnostics["column_profile_mean"] = float(column_profile.mean()) if len(column_profile) else 0.0

        return {
            "row_width_profile": row_widths,
            "row_width_profile_smoothed": smoothed,
            "column_profile": column_profile,
            "source": source,
            "detected_body_center_px": (x + bw // 2, y + bh // 2),
            "diagnostics": diagnostics,
        }

    def _score_body_isolation(
        self,
        result: BodyIsolationResult,
        *,
        image_shape: Tuple[int, int],
        instrument_family: Optional[Any],
        geometry_authority: Optional[Any],
        params: BodyIsolationParams,
    ) -> None:
        img_h, img_w = image_shape
        x, y, bw, bh = result.body_bbox_px

        signals = BodyIsolationSignalBreakdown()

        # 1) Vertical extent
        vertical_extent_ratio = bh / max(1.0, img_h)
        signals.vertical_extent_ratio = float(min(1.0, vertical_extent_ratio / 0.55))

        # 2) Width stability
        if result.column_profile is not None and len(result.column_profile) > 0:
            col = result.column_profile.astype(np.float32)
            if float(col.mean()) > 0:
                coeff_var = float(col.std() / max(1e-6, col.mean()))
                signals.width_stability = float(max(0.0, 1.0 - min(1.0, coeff_var)))
            else:
                signals.width_stability = 0.0

        # 3) Border penalty
        border_hits = 0
        if x <= params.border_ignore_px:
            border_hits += 1
        if y <= params.border_ignore_px:
            border_hits += 1
        if x + bw >= img_w - params.border_ignore_px:
            border_hits += 1
        if y + bh >= img_h - params.border_ignore_px:
            border_hits += 1
        signals.border_contact_penalty = float(min(1.0, border_hits / 2.0))
        result.border_contact_likely = border_hits > 0

        # 4) Center alignment
        cx = x + bw / 2.0
        img_cx = img_w / 2.0
        center_offset = abs(cx - img_cx) / max(1.0, img_w / 2.0)
        signals.center_alignment = float(max(0.0, 1.0 - center_offset))

        # 5) Lower bout presence (simple first-pass)
        if result.row_width_profile_smoothed is not None and len(result.row_width_profile_smoothed) > 0:
            rp = result.row_width_profile_smoothed
            by0 = max(0, y)
            by1 = min(len(rp), y + bh)
            if by1 > by0 + 6:
                segment = rp[by0:by1]
                n = len(segment)
                upper = float(segment[: max(1, n // 3)].mean())
                middle = float(segment[max(1, n // 3): max(2, 2 * n // 3)].mean())
                lower = float(segment[max(2, 2 * n // 3):].mean())
                if middle > 0:
                    lower_ratio = lower / middle
                    signals.lower_bout_presence = float(min(1.0, lower_ratio / 0.8))
                    result.lower_bout_missing_likely = lower_ratio < 0.55
                else:
                    signals.lower_bout_presence = 0.0

        # 6) Hull coverage proxy (bbox area occupancy as cheap approximation)
        bbox_area = max(1, bw * bh)
        mask_area = int(np.sum(result.isolation_mask > 0)) if result.isolation_mask is not None else bbox_area
        signals.hull_coverage = float(min(1.0, mask_area / bbox_area))

        # 7) Family-aware expectations if available
        if geometry_authority is not None and instrument_family is not None:
            fam_name = getattr(instrument_family, "family", instrument_family)
            profile = geometry_authority.get_expected_body_profile(fam_name)
            if profile:
                h_min, h_max, w_min, w_max = profile
                est_h_mm = getattr(result.body_region, "height_mm", None)
                est_w_mm = getattr(result.body_region, "width_mm", None)

                if est_h_mm is not None and h_max > h_min:
                    if est_h_mm < h_min:
                        result.expected_height_ratio = est_h_mm / h_min
                    elif est_h_mm > h_max:
                        result.expected_height_ratio = h_max / est_h_mm
                    else:
                        result.expected_height_ratio = 1.0

                if est_w_mm is not None and w_max > w_min:
                    if est_w_mm < w_min:
                        result.expected_width_ratio = est_w_mm / w_min
                    elif est_w_mm > w_max:
                        result.expected_width_ratio = w_max / est_w_mm
                    else:
                        result.expected_width_ratio = 1.0

        # Composite completeness
        penalties = 1.0 - min(1.0, signals.border_contact_penalty)
        result.score_breakdown = signals
        result.completeness_score = float(
            max(
                0.0,
                min(
                    1.0,
                    (
                        0.22 * signals.hull_coverage
                        + 0.22 * signals.vertical_extent_ratio
                        + 0.18 * signals.width_stability
                        + 0.12 * signals.center_alignment
                        + 0.16 * signals.lower_bout_presence
                        + 0.10 * penalties
                    ),
                ),
            )
        )

        # Issues
        if result.lower_bout_missing_likely:
            result.add_issue(
                "lower_bout_missing_likely",
                "Body isolation likely under-captured the lower bout.",
            )

        if result.border_contact_likely:
            result.add_issue(
                "border_contact_likely",
                "Body isolation touches image border; page edge or crop contamination possible.",
            )

        if result.completeness_score < 0.45:
            result.add_issue(
                "body_isolation_low_completeness",
                f"Body isolation completeness score is low ({result.completeness_score:.2f}).",
                severity="error",
            )

    @staticmethod
    def _make_bbox_mask(image_shape: Tuple[int, int], bbox: Tuple[int, int, int, int]) -> np.ndarray:
        h, w = image_shape
        x, y, bw, bh = bbox
        mask = np.zeros((h, w), dtype=np.uint8)
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(w, x + bw)
        y1 = min(h, y + bh)
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = 255
        return mask

    @staticmethod
    def _expand_body_bbox(
        *,
        image_shape: Tuple[int, int],
        bbox: Tuple[int, int, int, int],
        params: BodyIsolationParams,
    ) -> Tuple[int, int, int, int]:
        """
        Expand the isolator bbox so ownership retries can recover missing body.

        Expansion is conservative by default and only becomes active for
        body_region_expansion or other future retry profiles that set the knobs.
        """
        img_h, img_w = image_shape
        x, y, bw, bh = bbox

        if bw <= 0 or bh <= 0:
            return bbox

        pad_x = int(round(bw * max(0.0, float(params.bbox_expand_ratio))))
        pad_y = int(round(bh * max(0.0, float(params.bbox_expand_ratio))))

        top_extra = 0
        bottom_extra = 0

        if params.allow_vertical_growth:
            top_extra += int(round(bh * max(0.0, float(params.upper_bound_expand_pct))))
            bottom_extra += int(round(bh * max(0.0, float(params.lower_bound_expand_pct))))

        if params.allow_lower_bout_growth:
            bottom_extra += int(round(bh * 0.10))

        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y - top_extra)
        x1 = min(img_w, x + bw + pad_x)
        y1 = min(img_h, y + bh + pad_y + bottom_extra)

        return (x0, y0, max(0, x1 - x0), max(0, y1 - y0))

    def _make_isolation_mask(
        self,
        image_shape: Tuple[int, int],
        bbox: Tuple[int, int, int, int],
        fg_mask: Optional[np.ndarray],
        params: BodyIsolationParams,
    ) -> np.ndarray:
        """
        Build the effective Stage 4.5 isolation mask.

        Baseline behavior remains bbox-only.
        body_region_expansion materially changes the mask by:
          1. using the expanded bbox
          2. recovering FG pixels inside that ROI
          3. applying vertical continuity repair
          4. applying lower-bout recovery in the lower band
        """
        mask = self._make_bbox_mask(image_shape, bbox)

        if fg_mask is None:
            return mask

        if not (
            params.bbox_expand_ratio > 0.0
            or params.allow_vertical_growth
            or params.allow_lower_bout_growth
        ):
            return mask

        h, w = image_shape
        x, y, bw, bh = bbox
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(w, x + bw)
        y1 = min(h, y + bh)
        if x1 <= x0 or y1 <= y0:
            return mask

        roi_fg = np.zeros((h, w), dtype=np.uint8)
        roi_fg[y0:y1, x0:x1] = np.where(fg_mask[y0:y1, x0:x1] > 0, 255, 0).astype(np.uint8)

        if params.allow_vertical_growth:
            roi_fg = self._recover_vertical_continuity(roi_fg, bbox)

        if params.allow_lower_bout_growth:
            roi_fg = self._recover_lower_bout(roi_fg, bbox)

        return np.maximum(mask, roi_fg)

    @staticmethod
    def _recover_vertical_continuity(
        mask: np.ndarray,
        bbox: Tuple[int, int, int, int],
    ) -> np.ndarray:
        x, y, bw, bh = bbox
        out = mask.copy()
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(mask.shape[1], x + bw)
        y1 = min(mask.shape[0], y + bh)
        if x1 <= x0 or y1 <= y0:
            return out

        roi = out[y0:y1, x0:x1]
        kernel_h = max(5, ((bh // 12) // 2) * 2 + 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, kernel_h))
        roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, kernel)
        out[y0:y1, x0:x1] = roi
        return out

    @staticmethod
    def _recover_lower_bout(
        mask: np.ndarray,
        bbox: Tuple[int, int, int, int],
    ) -> np.ndarray:
        x, y, bw, bh = bbox
        out = mask.copy()
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(mask.shape[1], x + bw)
        y1 = min(mask.shape[0], y + bh)
        if x1 <= x0 or y1 <= y0:
            return out

        band_start = y0 + int(round(0.55 * max(1, y1 - y0)))
        lower = out[band_start:y1, x0:x1]
        if lower.size == 0:
            return out

        kernel_w = max(5, ((bw // 10) // 2) * 2 + 1)
        kernel_h = max(5, ((bh // 14) // 2) * 2 + 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_w, kernel_h))
        lower = cv2.dilate(lower, kernel, iterations=1)
        lower = cv2.morphologyEx(lower, cv2.MORPH_CLOSE, kernel)
        out[band_start:y1, x0:x1] = lower
        return out
