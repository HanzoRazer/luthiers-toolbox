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


class MaterialHardness(str, Enum):
    """Material hardness classification for DOC/feed validation."""
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very-hard"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


class FeasibilityInput(BaseModel):
    """
    Deterministic, minimal input for feasibility. Must be stable and hashable.
    Do not include timestamps or non-deterministic fields.

    Schema v2: Extended with material/geometry/tool fields for adversarial detection.
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

    # === Schema v2 fields (adversarial detection) ===

    # Material properties
    material_id: Optional[str] = None  # e.g., "maple", "pine", "ebony"
    material_hardness: Optional[MaterialHardness] = None  # soft/medium/hard/very-hard/extreme
    material_thickness_mm: Optional[float] = None  # stock thickness
    material_resinous: Optional[bool] = None  # true for rosewood, pine sap pockets, etc.

    # Geometry dimensions (explicit, not just bbox)
    geometry_width_mm: Optional[float] = None  # pocket/slot width
    geometry_length_mm: Optional[float] = None  # pocket/slot length
    geometry_depth_mm: Optional[float] = None  # target cutting depth
    wall_thickness_mm: Optional[float] = None  # thinnest wall in geometry

    # Tool properties
    tool_flute_length_mm: Optional[float] = None  # cutting length
    tool_stickout_mm: Optional[float] = None  # total extension from collet

    # Process properties
    coolant_enabled: Optional[bool] = None  # air blast, mist, flood

    # === Schema v2.1 fields (edge pressure detection) ===

    # Geometry properties
    floor_thickness_mm: Optional[float] = None  # remaining material below pocket
    geometry_complex: Optional[bool] = None  # L-shapes, multiple islands, etc.

    # Process overrides
    feed_override_percent: Optional[float] = None  # 100 = normal, 150 = 50% faster


class FeasibilityResult(BaseModel):
    """
    Phase 3 — Explainability-ready feasibility result.
    
    Every YELLOW/RED outcome can be explained by looking up rules_triggered
    in the authoritative rule_registry.py.
    """
    risk_level: RiskLevel
    blocking: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Phase 3: Rule IDs that triggered this outcome (for registry lookup)
    rules_triggered: List[str] = Field(
        default_factory=list,
        description="Rule IDs (e.g., 'F001', 'F010') that triggered this outcome. "
                    "Look up in rule_registry.py for human-readable explanations.",
    )

    # "constraints" should be machine-readable later; strings are fine for MVP.
    constraints: List[str] = Field(default_factory=list)

    engine_version: str = Field(default="feasibility_engine_v1")
    computed_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Keep a stable "details" bag for audits, but ensure it's deterministic content only.
    details: Dict[str, Any] = Field(default_factory=dict)
