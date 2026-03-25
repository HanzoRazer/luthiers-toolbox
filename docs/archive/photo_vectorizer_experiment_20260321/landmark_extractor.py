from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import numpy as np

from body_isolation_result import BodyIsolationResult
from body_model import BodyLandmarks, BodyModel, GeometryConstraints


def build_body_model_from_isolation(
    body_result: BodyIsolationResult,
    *,
    source_image_id: Optional[str] = None,
    family_hint: Optional[str] = None,
    spec_hint: Optional[str] = None,
    mm_per_px: Optional[float] = None,
) -> BodyModel:
    """
    Build the initial BodyModel directly from the existing BodyIsolationResult.

    The current tree already persists:
      - row_width_profile
      - row_width_profile_smoothed
      - column_profile

    So this is a handoff-layer transformation, not a Stage 4 rewrite.

    Note: BodyIsolationResult does not yet own contour-stage ownership fields,
    so ownership_score / ownership_ok will be None here. They are populated
    later by ContourStage.
    """
    return BodyModel(
        source_image_id=source_image_id,
        family_hint=family_hint,
        spec_hint=spec_hint,
        body_bbox_px=body_result.body_bbox_px,
        body_region=body_result.body_region,
        row_width_profile_px=getattr(body_result, "row_width_profile", None),
        row_width_profile_smoothed_px=getattr(body_result, "row_width_profile_smoothed", None),
        column_profile_px=getattr(body_result, "column_profile", None),
        mm_per_px=mm_per_px,
        ownership_score=getattr(body_result, "ownership_score", None),
        ownership_ok=getattr(body_result, "ownership_ok", None),
        manual_review_required=bool(getattr(body_result, "review_required", False)),
        recommended_next_action=getattr(body_result, "recommended_next_action", None),
        diagnostics=dict(getattr(body_result, "diagnostics", {}) or {}),
    )


def extract_landmarks_from_profile(model: BodyModel) -> BodyModel:
    """
    Extract the five primary body landmarks from the existing smoothed W(y) profile.

    Landmark positions are derived from three body band slices:
      - Upper third  (0%–35%): argmax → upper bout
      - Middle third (30%–70%): argmin → waist
      - Lower half   (50%–100%): argmax → lower bout

    All failures set manual_review_required and a diagnostic key rather than
    raising, so the pipeline can continue to the export-block path.
    """
    w = model.row_width_profile_smoothed_px
    if w is None:
        model.manual_review_required = True
        model.recommended_next_action = "rerun_body_isolation"
        model.diagnostics["landmark_extraction_failed"] = "missing_row_width_profile_smoothed"
        return model

    arr = np.asarray(w, dtype=float)
    if arr.size == 0:
        model.manual_review_required = True
        model.recommended_next_action = "rerun_body_isolation"
        model.diagnostics["landmark_extraction_failed"] = "empty_row_width_profile_smoothed"
        return model

    x, y, bw, bh = model.body_bbox_px
    if bw <= 0 or bh <= 0:
        model.manual_review_required = True
        model.recommended_next_action = "rerun_body_isolation"
        model.diagnostics["landmark_extraction_failed"] = "degenerate_body_bbox"
        return model

    y0 = max(0, int(y))
    y1 = min(len(arr), int(y + bh))
    if y1 <= y0:
        model.manual_review_required = True
        model.recommended_next_action = "rerun_body_isolation"
        model.diagnostics["landmark_extraction_failed"] = "body_bbox_outside_profile"
        return model

    body_band = arr[y0:y1]
    body_length = float(max(1, y1 - y0))

    upper_end = max(1, int(0.35 * len(body_band)))
    mid_start = int(0.30 * len(body_band))
    mid_end = max(mid_start + 1, int(0.70 * len(body_band)))
    lower_start = int(0.50 * len(body_band))

    upper_local = int(np.argmax(body_band[:upper_end]))
    waist_local = int(np.argmin(body_band[mid_start:mid_end])) + mid_start
    lower_local = int(np.argmax(body_band[lower_start:])) + lower_start

    upper_y = y0 + upper_local
    waist_y = y0 + waist_local
    lower_y = y0 + lower_local

    upper_w = float(body_band[upper_local])
    waist_w = float(body_band[waist_local])
    lower_w = float(body_band[lower_local])
    centerline_x = float(x + bw / 2.0)

    model.landmarks = BodyLandmarks(
        centerline_x_px=centerline_x,
        body_top_y_px=y0,
        body_bottom_y_px=y1,
        body_length_px=body_length,
        waist_y_px=waist_y,
        waist_width_px=waist_w,
        upper_bout_y_px=upper_y,
        upper_bout_width_px=upper_w,
        lower_bout_y_px=lower_y,
        lower_bout_width_px=lower_w,
        waist_y_norm=(waist_y - y0) / body_length,
        upper_bout_y_norm=(upper_y - y0) / body_length,
        lower_bout_y_norm=(lower_y - y0) / body_length,
        waist_to_lower_ratio=waist_w / max(lower_w, 1e-6),
        upper_to_lower_ratio=upper_w / max(lower_w, 1e-6),
        width_to_length_ratio=lower_w / max(body_length, 1e-6),
    )
    return model


def validate_body_constraints(
    model: BodyModel,
    *,
    symmetry_score: float,
    has_cutaway: bool = False,
) -> BodyModel:
    """
    Encode hard geometric invariants rather than post-hoc contour-only penalties.

    The four invariants (from the senior engineer's specification):
      1. lower_bout > waist > upper_bout
      2. waist y-position between 35% and 55% of body length
      3. width-to-length ratio between 0.70 and 0.95
      4. bilateral symmetry > 0.80 (bypassed when has_cutaway=True)

    Violations are first-class signals, not scoring penalties.
    """
    lm = model.landmarks
    if lm is None:
        model.constraints = GeometryConstraints(
            lower_gt_waist_gt_upper=False,
            waist_position_valid=False,
            aspect_ratio_valid=False,
            symmetry_valid=False,
            all_valid=False,
            violations=["missing_landmarks"],
        )
        return model

    violations: list[str] = []

    c1 = (
        lm.lower_bout_width_px > lm.upper_bout_width_px
        and lm.upper_bout_width_px >= lm.waist_width_px
        and lm.lower_bout_width_px > lm.waist_width_px
    )
    if not c1:
        violations.append("bout_order_invalid")

    c2 = 0.35 <= lm.waist_y_norm <= 0.55
    if not c2:
        violations.append("waist_position_invalid")

    c3 = 0.70 <= lm.width_to_length_ratio <= 0.95
    if not c3:
        violations.append("aspect_ratio_invalid")

    c4 = True if has_cutaway else symmetry_score > 0.80
    if not c4:
        violations.append("symmetry_invalid")

    model.constraints = GeometryConstraints(
        lower_gt_waist_gt_upper=c1,
        waist_position_valid=c2,
        aspect_ratio_valid=c3,
        symmetry_valid=c4,
        all_valid=(len(violations) == 0),
        violations=violations,
    )

    if not model.constraints.all_valid:
        model.diagnostics["body_constraint_violations"] = list(violations)

    return model


# ── Diff 3: spec fitting and expected outline generation ──────────────────────

def fit_body_model_to_spec(
    model: BodyModel,
    *,
    geometry_authority: "GeometryAuthority",  # type: ignore[name-defined]
) -> BodyModel:
    """
    Find the nearest spec from body_dimension_reference.json and populate
    BodyModel.spec_delta.

    The fit metric is L1 distance across the four width/length dimensions,
    all converted to mm using model.mm_per_px.

    When mm_per_px is None (calibration not yet available), the fit is
    performed in normalised landmark space (ratios) so a spec is still
    selected; the mm deltas will be None in that case.
    """
    from geometry_authority import BodyDimensionSpec
    from body_model import SpecDelta

    lm = model.landmarks
    if lm is None:
        return model

    candidates = geometry_authority.find_candidate_specs(
        family_hint=model.family_hint,
        spec_name=model.spec_hint,
    )

    # If family-filtered list is empty, fall back to all specs
    if not candidates:
        candidates = geometry_authority.find_candidate_specs()

    if not candidates:
        model.diagnostics["spec_fit"] = "no_candidates"
        return model

    mpp = model.mm_per_px

    if mpp is not None and mpp > 0:
        # Fit in mm space
        obs_length = lm.body_length_px * mpp
        obs_upper = lm.upper_bout_width_px * mpp
        obs_waist = lm.waist_width_px * mpp
        obs_lower = lm.lower_bout_width_px * mpp

        def _score(spec: BodyDimensionSpec) -> float:
            return (
                abs(obs_length - spec.body_length_mm) +
                abs(obs_upper - spec.upper_bout_width_mm) +
                abs(obs_waist - spec.waist_width_mm) +
                abs(obs_lower - spec.lower_bout_width_mm)
            )

        best = min(candidates, key=_score)
        fit_score = _score(best)

        model.spec_delta = SpecDelta(
            spec_name=best.name,
            family=best.family,
            body_length_mm_delta=round(obs_length - best.body_length_mm, 2),
            waist_width_mm_delta=round(obs_waist - best.waist_width_mm, 2),
            upper_bout_width_mm_delta=round(obs_upper - best.upper_bout_width_mm, 2),
            lower_bout_width_mm_delta=round(obs_lower - best.lower_bout_width_mm, 2),
            fit_score=round(fit_score, 2),
        )
    else:
        # Calibration unavailable — fit in normalised ratio space
        obs_wl = lm.waist_to_lower_ratio
        obs_ul = lm.upper_to_lower_ratio
        obs_wp = lm.waist_y_norm

        def _score_norm(spec: BodyDimensionSpec) -> float:
            spec_wl = spec.waist_width_mm / max(spec.lower_bout_width_mm, 1e-6)
            spec_ul = spec.upper_bout_width_mm / max(spec.lower_bout_width_mm, 1e-6)
            return abs(obs_wl - spec_wl) + abs(obs_ul - spec_ul) + abs(obs_wp - spec.waist_y_norm)

        best = min(candidates, key=_score_norm)

        model.spec_delta = SpecDelta(
            spec_name=best.name,
            family=best.family,
            fit_score=round(_score_norm(best), 4),
        )

    model.diagnostics["spec_fit_name"] = best.name
    model.diagnostics["spec_fit_score"] = model.spec_delta.fit_score
    return model


def generate_expected_outline(model: BodyModel) -> BodyModel:
    """
    Generate a synthetic body outline from the extracted landmarks.

    The outline is a closed polygon approximating a guitar body shape,
    constructed by interpolating a half-width envelope across 5 anchor
    points (top → upper bout → waist → lower bout → tail) and mirroring
    about the centerline.

    This becomes BodyModel.expected_outline_px, which Diff 3's election
    uses as the reference target for Hausdorff-distance-based candidate
    ranking.

    Design choice: linear interpolation between anchors, not spline.
    A spline is smoother but introduces overshoot artefacts near the
    waist when landmarks are extracted from noisy profiles.  The linear
    envelope is a conservative prior — it will never extend outside the
    observed landmark bounds.
    """
    lm = model.landmarks
    if lm is None:
        return model

    # Five anchor points in (y_px, half_width_px) space
    anchor_y = np.array([
        float(lm.body_top_y_px),
        float(lm.upper_bout_y_px),
        float(lm.waist_y_px),
        float(lm.lower_bout_y_px),
        float(lm.body_bottom_y_px),
    ])
    anchor_hw = np.array([
        lm.upper_bout_width_px * 0.12,   # top taper — roughly neck width
        lm.upper_bout_width_px * 0.50,
        lm.waist_width_px * 0.50,
        lm.lower_bout_width_px * 0.50,
        lm.lower_bout_width_px * 0.08,   # tail taper
    ])

    # Ensure anchors are strictly monotone in y (required for np.interp)
    if not np.all(np.diff(anchor_y) > 0):
        model.diagnostics["expected_outline_skipped"] = "non_monotone_anchors"
        return model

    n_points = 200
    y_vals = np.linspace(anchor_y[0], anchor_y[-1], n_points)
    half_widths = np.interp(y_vals, anchor_y, anchor_hw)

    cx = lm.centerline_x_px
    left_side = np.column_stack([cx - half_widths, y_vals])
    right_side = np.column_stack([cx + half_widths, y_vals[::-1]])

    outline = np.vstack([left_side, right_side]).astype(np.float32)
    model.expected_outline_px = outline

    model.diagnostics["expected_outline_n_points"] = int(outline.shape[0])
    model.diagnostics["expected_outline_spec"] = (
        model.spec_delta.spec_name if model.spec_delta is not None else "landmark_only"
    )
    return model

