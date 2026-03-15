from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


BBoxPx = Tuple[int, int, int, int]  # x, y, w, h


@dataclass
class BodyIsolationSignalBreakdown:
    """
    Diagnostic scores used by the coach.

    All values normalized to 0..1 where higher is better unless noted.
    """
    hull_coverage: float = 0.0
    vertical_extent_ratio: float = 0.0
    width_stability: float = 0.0
    border_contact_penalty: float = 0.0
    center_alignment: float = 0.0
    lower_bout_presence: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "hull_coverage": self.hull_coverage,
            "vertical_extent_ratio": self.vertical_extent_ratio,
            "width_stability": self.width_stability,
            "border_contact_penalty": self.border_contact_penalty,
            "center_alignment": self.center_alignment,
            "lower_bout_presence": self.lower_bout_presence,
        }


@dataclass
class BodyIsolationIssue:
    code: str
    message: str
    severity: str = "warning"  # info|warning|error


@dataclass
class BodyIsolationResult:
    """
    Typed output for Stage 4.5 body isolation.

    This wraps the existing BodyRegion output with richer diagnostics
    so the coach can inspect body ownership before Stage 8 commits a contour.
    """
    # Primary geometry
    body_bbox_px: BBoxPx
    body_region: Any  # keep broad initially to wrap existing BodyRegion
    isolation_mask: Optional[np.ndarray] = None

    # Raw profiles / diagnostics
    row_width_profile: Optional[np.ndarray] = None
    row_width_profile_smoothed: Optional[np.ndarray] = None
    column_profile: Optional[np.ndarray] = None
    detected_body_center_px: Optional[Tuple[int, int]] = None
    source: str = "unknown"  # fg_mask|original_image|image_raw|fallback

    # Summary signals
    confidence: float = 0.0
    completeness_score: float = 0.0
    expected_height_ratio: Optional[float] = None
    expected_width_ratio: Optional[float] = None
    lower_bout_missing_likely: bool = False
    border_contact_likely: bool = False
    neck_inclusion_likely: bool = False

    score_breakdown: BodyIsolationSignalBreakdown = field(
        default_factory=BodyIsolationSignalBreakdown
    )
    issues: List[BodyIsolationIssue] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    # Coach / control flags
    review_required: bool = False
    recommended_next_action: Optional[str] = None  # rerun_body_isolation/manual_review_required

    @property
    def x(self) -> int:
        return self.body_bbox_px[0]

    @property
    def y(self) -> int:
        return self.body_bbox_px[1]

    @property
    def width_px(self) -> int:
        return self.body_bbox_px[2]

    @property
    def height_px(self) -> int:
        return self.body_bbox_px[3]

    def add_issue(self, code: str, message: str, severity: str = "warning") -> None:
        self.issues.append(BodyIsolationIssue(code=code, message=message, severity=severity))
