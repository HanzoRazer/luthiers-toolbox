from __future__ import annotations

import numpy as np

from body_isolation_result import BodyIsolationResult, BodyIsolationSignalBreakdown
from body_model import BodyModel
from landmark_extractor import (
    build_body_model_from_isolation,
    extract_landmarks_from_profile,
    fit_body_model_to_spec,
    generate_expected_outline,
    validate_body_constraints,
)


class _BodyRegionStub:
    def __init__(self, x=50, y=100, width=320, height=500, confidence=0.86):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.height_mm = None
        self.width_mm = None

    @property
    def bbox(self):
        return (self.x, self.y, self.width, self.height)

    @property
    def height_px(self):
        return self.height


def _make_body_result() -> BodyIsolationResult:
    result = BodyIsolationResult(
        body_bbox_px=(50, 100, 320, 500),
        body_region=_BodyRegionStub(),
        confidence=0.86,
        completeness_score=0.82,
        review_required=False,
        score_breakdown=BodyIsolationSignalBreakdown(),
    )

    # Build a profile that satisfies all four geometric constraints:
    #   1. lower_bout > waist > upper_bout
    #   2. waist y-norm in [0.35, 0.55]
    #   3. width_to_length_ratio = lower_w / body_length in [0.70, 0.95]
    #      body_length = 500 (bbox height), so lower_w must be >= 350
    #   4. symmetry handled externally in validate_body_constraints
    #
    profile = np.zeros(800, dtype=float)

    # Body band spans absolute indices 100–600 (body_bbox y=100, h=500).
    # Landmark extraction slices:
    #   upper slice: body_band[0 : int(0.35*500)] = body_band[0:175] → absolute 100–274
    #   mid slice:   body_band[150 : 350]                             → absolute 250–449
    #   lower slice: body_band[250 : 500]                             → absolute 350–599
    #
    # Desired landmarks (all in absolute index space):
    #   upper bout:  absolute 150  → body_band[50]  → norm 50/500=0.10  (in upper slice)
    #   waist:       absolute 320  → body_band[220] → norm 220/500=0.44  (in mid slice, valid [0.35,0.55])
    #   lower bout:  absolute 490  → body_band[390] → norm 390/500=0.78  (in lower slice)
    #
    # Constraint requirements:
    #   1. lower_w > waist_w > upper_w     → set 360 > 170 > 150 explicitly
    #   2. waist_y_norm in [0.35, 0.55]   → 0.44 — satisfied above
    #   3. width_to_length_ratio in [0.70, 0.95] → lower_w/body_length = 360/500 = 0.72 — satisfied
    #   4. symmetry — checked externally

    # Upper bout peak: must be global max of upper slice (body_band[0:175])
    profile[150] = 150.0   # unique peak in upper slice

    # Waist minimum: must be global min of mid slice (body_band[150:350], absolute 250–449)
    # Fill mid-region at 190, then punch a clear hole at 320
    for i in range(250, 450):
        profile[i] = 190.0
    profile[320] = 170.0   # explicit dip — will be argmin of mid slice

    # Lower bout peak: must be global max of lower slice (body_band[250:500], absolute 350–599)
    profile[490] = 360.0   # unique peak in lower slice

    # Fill upper region (excluding peaks already set)
    for i in range(100, 250):
        if profile[i] == 0.0:
            profile[i] = 140.0   # below upper bout peak (150) so peak dominates

    # Fill lower region (excluding peaks already set)
    for i in range(450, 600):
        if profile[i] == 0.0:
            profile[i] = 280.0   # below lower bout peak (360) so peak dominates

    result.row_width_profile = profile.copy()
    result.row_width_profile_smoothed = profile.copy()
    result.column_profile = np.zeros(600, dtype=float)
    return result


def test_build_body_model_from_isolation_reads_existing_profiles():
    body_result = _make_body_result()

    model = build_body_model_from_isolation(
        body_result,
        family_hint="archtop",
        mm_per_px=0.5,
    )

    assert isinstance(model, BodyModel)
    assert model.body_bbox_px == (50, 100, 320, 500)
    assert model.row_width_profile_px is not None
    assert model.row_width_profile_smoothed_px is not None
    assert model.column_profile_px is not None
    assert model.family_hint == "archtop"
    assert model.mm_per_px == 0.5


def test_extract_landmarks_from_profile_finds_primary_body_points():
    body_result = _make_body_result()
    model = build_body_model_from_isolation(body_result)

    model = extract_landmarks_from_profile(model)

    assert model.landmarks is not None
    assert model.landmarks.upper_bout_width_px > model.landmarks.waist_width_px
    assert model.landmarks.lower_bout_width_px > model.landmarks.waist_width_px
    assert 0.35 <= model.landmarks.waist_y_norm <= 0.55


def test_validate_body_constraints_marks_valid_profile():
    body_result = _make_body_result()
    model = extract_landmarks_from_profile(build_body_model_from_isolation(body_result))

    model = validate_body_constraints(model, symmetry_score=0.91, has_cutaway=False)

    assert model.constraints is not None
    assert model.constraints.all_valid is True
    assert model.constraints.violations == []


def test_validate_body_constraints_surfaces_invalid_geometry():
    body_result = _make_body_result()
    model = extract_landmarks_from_profile(build_body_model_from_isolation(body_result))
    assert model.landmarks is not None

    # Force violations on all four invariants
    model.landmarks.upper_bout_width_px = 290.0
    model.landmarks.waist_width_px = 210.0
    model.landmarks.lower_bout_width_px = 205.0   # lower < waist → c1 fails
    model.landmarks.width_to_length_ratio = 0.50  # below 0.70 → c3 fails
    model.landmarks.waist_y_norm = 0.20            # below 0.35 → c2 fails

    model = validate_body_constraints(model, symmetry_score=0.40, has_cutaway=False)

    assert model.constraints is not None
    assert model.constraints.all_valid is False
    assert "bout_order_invalid" in model.constraints.violations
    assert "waist_position_invalid" in model.constraints.violations
    assert "aspect_ratio_invalid" in model.constraints.violations
    assert "symmetry_invalid" in model.constraints.violations


def test_extract_landmarks_gracefully_handles_missing_profile():
    body_result = _make_body_result()
    model = build_body_model_from_isolation(body_result)
    model.row_width_profile_smoothed_px = None

    model = extract_landmarks_from_profile(model)

    assert model.landmarks is None
    assert model.manual_review_required is True
    assert model.diagnostics["landmark_extraction_failed"] == "missing_row_width_profile_smoothed"


def test_extract_landmarks_gracefully_handles_degenerate_bbox():
    body_result = _make_body_result()
    model = build_body_model_from_isolation(body_result)
    model.body_bbox_px = (50, 100, 0, 500)  # zero width

    model = extract_landmarks_from_profile(model)

    assert model.landmarks is None
    assert model.manual_review_required is True
    assert model.diagnostics["landmark_extraction_failed"] == "degenerate_body_bbox"


def test_fit_body_model_to_spec_populates_spec_delta():
    body_result = _make_body_result()
    model = extract_landmarks_from_profile(
        build_body_model_from_isolation(body_result, family_hint="archtop", mm_per_px=1.0)
    )

    from geometry_authority import GeometryAuthority
    model = fit_body_model_to_spec(model, geometry_authority=GeometryAuthority())

    assert model.spec_delta is not None
    assert model.spec_delta.family == "archtop"


def test_generate_expected_outline_produces_closed_prior():
    body_result = _make_body_result()
    model = extract_landmarks_from_profile(build_body_model_from_isolation(body_result))

    model = generate_expected_outline(model)

    assert model.expected_outline_px is not None
    assert model.expected_outline_px.shape[1] == 2
    assert len(model.expected_outline_px) == 400


def test_fit_body_model_skips_when_mm_per_px_none():
    body_result = _make_body_result()
    model = extract_landmarks_from_profile(build_body_model_from_isolation(body_result))
    assert model.mm_per_px is None

    from geometry_authority import GeometryAuthority
    model = fit_body_model_to_spec(model, geometry_authority=GeometryAuthority())

    # Should still fit using normalised ratio space — spec_delta may be set
    # but mm deltas will be None
    if model.spec_delta is not None:
        assert model.spec_delta.body_length_mm_delta is None
