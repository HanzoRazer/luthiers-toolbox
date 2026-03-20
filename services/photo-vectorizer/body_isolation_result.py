from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, runtime_checkable

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

    def to_payload(self) -> Dict[str, float]:
        return {
            "hull_coverage": float(self.hull_coverage),
            "vertical_extent_ratio": float(self.vertical_extent_ratio),
            "width_stability": float(self.width_stability),
            "border_contact_penalty": float(self.border_contact_penalty),
            "center_alignment": float(self.center_alignment),
            "lower_bout_presence": float(self.lower_bout_presence),
        }

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]]) -> "BodyIsolationSignalBreakdown":
        payload = payload or {}
        return cls(
            hull_coverage=float(payload.get("hull_coverage", 0.0)),
            vertical_extent_ratio=float(payload.get("vertical_extent_ratio", 0.0)),
            width_stability=float(payload.get("width_stability", 0.0)),
            border_contact_penalty=float(payload.get("border_contact_penalty", 0.0)),
            center_alignment=float(payload.get("center_alignment", 0.0)),
            lower_bout_presence=float(payload.get("lower_bout_presence", 0.0)),
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "hull_coverage": self.hull_coverage,
            "vertical_extent_ratio": self.vertical_extent_ratio,
            "width_stability": self.width_stability,
            "border_contact_penalty": self.border_contact_penalty,
            "center_alignment": self.center_alignment,
            "lower_bout_presence": self.lower_bout_presence,
        }


@runtime_checkable
class BodyRegionProtocol(Protocol):
    x: int
    y: int
    width: int
    height: int
    confidence: float
    height_mm: Optional[float]
    width_mm: Optional[float]

    @property
    def bbox(self) -> BBoxPx:
        ...

    @property
    def height_px(self) -> int:
        ...


@dataclass
class ReplayBodyRegion:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    height_mm: Optional[float] = None
    width_mm: Optional[float] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    @property
    def height_px(self) -> int:
        return self.height

    def to_payload(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }
        if self.height_mm is not None:
            d["height_mm"] = self.height_mm
        if self.width_mm is not None:
            d["width_mm"] = self.width_mm
        return d

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]]) -> Optional["ReplayBodyRegion"]:
        if payload is None:
            return None
        return cls(
            x=int(payload.get("x", 0)),
            y=int(payload.get("y", 0)),
            width=int(payload.get("width", 0)),
            height=int(payload.get("height", 0)),
            confidence=float(payload.get("confidence", 0.0)),
            height_mm=payload.get("height_mm"),
            width_mm=payload.get("width_mm"),
        )


BodyRegionLike = Union[ReplayBodyRegion, BodyRegionProtocol]


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
    body_region: BodyRegionLike
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

    def to_payload(self) -> Dict[str, Any]:
        body_region_payload = None
        if self.body_region is not None:
            if isinstance(self.body_region, ReplayBodyRegion):
                body_region_payload = self.body_region.to_payload()
            else:
                body_region_payload = {
                    "x": int(getattr(self.body_region, "x", getattr(self.body_region, "x_px", 0))),
                    "y": int(getattr(self.body_region, "y", getattr(self.body_region, "y_px", 0))),
                    "width": int(getattr(self.body_region, "width", getattr(self.body_region, "width_px", 0))),
                    "height": int(getattr(self.body_region, "height", getattr(self.body_region, "height_px", 0))),
                    "confidence": float(getattr(self.body_region, "confidence", self.confidence)),
                    "height_mm": getattr(self.body_region, "height_mm", None),
                    "width_mm": getattr(self.body_region, "width_mm", None),
                }

        return {
            "body_bbox_px": [int(v) for v in self.body_bbox_px],
            "body_region": body_region_payload,
            "confidence": float(self.confidence),
            "completeness_score": float(self.completeness_score),
            "review_required": bool(self.review_required),
            "lower_bout_missing_likely": bool(self.lower_bout_missing_likely),
            "border_contact_likely": bool(self.border_contact_likely),
            "neck_inclusion_likely": bool(self.neck_inclusion_likely),
            "score_breakdown": self.score_breakdown.to_payload(),
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity,
                }
                for issue in self.issues
            ],
            "diagnostics": dict(self.diagnostics or {}),
            "recommended_next_action": self.recommended_next_action,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "BodyIsolationResult":
        bbox = tuple(payload.get("body_bbox_px", (0, 0, 0, 0)))
        region_payload = payload.get("body_region")

        body_region: Optional[BodyRegionLike] = ReplayBodyRegion.from_payload(
            {**region_payload, "confidence": float(region_payload.get("confidence", payload.get("confidence", 0.0)))} if region_payload is not None else None
        )

        result = cls(
            body_bbox_px=(
                int(bbox[0]) if len(bbox) > 0 else 0,
                int(bbox[1]) if len(bbox) > 1 else 0,
                int(bbox[2]) if len(bbox) > 2 else 0,
                int(bbox[3]) if len(bbox) > 3 else 0,
            ),
            body_region=body_region,
            confidence=float(payload.get("confidence", 0.0)),
            completeness_score=float(payload.get("completeness_score", 0.0)),
            review_required=bool(payload.get("review_required", False)),
            lower_bout_missing_likely=bool(payload.get("lower_bout_missing_likely", False)),
            border_contact_likely=bool(payload.get("border_contact_likely", False)),
            neck_inclusion_likely=bool(payload.get("neck_inclusion_likely", False)),
            score_breakdown=BodyIsolationSignalBreakdown.from_payload(payload.get("score_breakdown")),
            diagnostics=dict(payload.get("diagnostics", {}) or {}),
            recommended_next_action=payload.get("recommended_next_action"),
        )
        for issue in payload.get("issues", []) or []:
            result.issues.append(
                BodyIsolationIssue(
                    code=issue.get("code", "unknown"),
                    message=issue.get("message", ""),
                    severity=issue.get("severity", "warning"),
                )
            )
        return result

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
