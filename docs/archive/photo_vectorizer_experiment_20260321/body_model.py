from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np


BBoxPx = Tuple[int, int, int, int]


@dataclass
class BodyLandmarks:
    centerline_x_px: float
    body_top_y_px: int
    body_bottom_y_px: int
    body_length_px: float

    waist_y_px: int
    waist_width_px: float

    upper_bout_y_px: int
    upper_bout_width_px: float

    lower_bout_y_px: int
    lower_bout_width_px: float

    neck_join_y_px: Optional[int] = None

    waist_y_norm: float = 0.0
    upper_bout_y_norm: float = 0.0
    lower_bout_y_norm: float = 0.0
    waist_to_lower_ratio: float = 0.0
    upper_to_lower_ratio: float = 0.0
    width_to_length_ratio: float = 0.0


@dataclass
class RegionConfidence:
    upper_bout: float
    waist: float
    lower_bout: float
    centerline: float
    symmetry: float
    outline_refinement: float


@dataclass
class SpecDelta:
    spec_name: Optional[str]
    family: Optional[str]
    body_length_mm_delta: Optional[float] = None
    waist_width_mm_delta: Optional[float] = None
    upper_bout_width_mm_delta: Optional[float] = None
    lower_bout_width_mm_delta: Optional[float] = None
    centerline_offset_mm: Optional[float] = None
    fit_score: Optional[float] = None


@dataclass
class GeometryConstraints:
    lower_gt_waist_gt_upper: bool
    waist_position_valid: bool
    aspect_ratio_valid: bool
    symmetry_valid: bool
    all_valid: bool
    violations: list[str] = field(default_factory=list)


@dataclass
class BodyModel:
    """
    Typed geometry handoff between body isolation and contour evaluation.

    This is intentionally minimal for Diff 2:
      - preserve Stage 4.5 width/column profiles that already exist
      - attach extracted semantic landmarks
      - attach hard constraint evaluation
      - remain backward-compatible with body_region-based contour stage

    Diff 3 will add expected_outline_px generation from landmarks/spec prior
    and rewrite contour election to use it.
    """
    source_image_id: Optional[str]
    family_hint: Optional[str]
    spec_hint: Optional[str]

    body_bbox_px: BBoxPx
    body_region: Optional[Any]  # any BodyRegion-like object (BodyRegionProtocol when available)

    row_width_profile_px: Optional[np.ndarray]
    row_width_profile_smoothed_px: Optional[np.ndarray]
    column_profile_px: Optional[np.ndarray]
    mm_per_px: Optional[float]

    landmarks: Optional[BodyLandmarks] = None
    confidence_map: Optional[RegionConfidence] = None
    spec_delta: Optional[SpecDelta] = None
    constraints: Optional[GeometryConstraints] = None

    # Diff 3 targets — None until expected contour generation is added
    expected_outline_px: Optional[np.ndarray] = None
    refined_outline_px: Optional[np.ndarray] = None
    exported_outline_mm: Optional[np.ndarray] = None

    # Ownership populated by ContourStage, not BodyIsolationResult
    ownership_score: Optional[float] = None
    ownership_ok: Optional[bool] = None
    manual_review_required: bool = False
    recommended_next_action: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
