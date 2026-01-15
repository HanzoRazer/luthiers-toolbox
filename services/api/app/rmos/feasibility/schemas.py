from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class FeasibilityInput(BaseModel):
    """
    Deterministic, minimal input for feasibility. Must be stable and hashable.
    Do not include timestamps or non-deterministic fields.
    """

    # identity / context
    pipeline_id: str = Field(default="mvp_dxf_to_grbl_v1")
    post_id: str = Field(default="GRBL")
    units: str = Field(default="mm")

    # CAM params
    tool_d: float
    stepover: float
    stepdown: float
    z_rough: float
    feed_xy: float
    feed_z: float
    rapid: float
    safe_z: float
    strategy: str
    layer_name: str
    climb: bool
    smoothing: float
    margin: float

    # cheap geometry summary (pre-CAM)
    # These should come from DXF preflight/summary where possible.
    has_closed_paths: Optional[bool] = None
    loop_count_hint: Optional[int] = None  # preflight polyline count, or 0/None if unknown
    entity_count: Optional[int] = None
    bbox: Optional[Dict[str, float]] = None  # {x_min,y_min,x_max,y_max}
    smallest_feature_mm: Optional[float] = None  # optional (can be None for MVP)


class FeasibilityResult(BaseModel):
    risk_level: RiskLevel
    blocking: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # "constraints" should be machine-readable later; strings are fine for MVP.
    constraints: List[str] = Field(default_factory=list)

    engine_version: str = Field(default="feasibility_engine_v1")
    computed_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Keep a stable "details" bag for audits, but ensure it's deterministic content only.
    details: Dict[str, Any] = Field(default_factory=dict)
