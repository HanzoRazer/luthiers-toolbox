"""Learned Overrides Models — Pydantic schemas for 4-tuple lane-based parameter learning."""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class OverrideSource(str, Enum):
    """Source of override value."""
    MANUAL = "manual"                   # Operator manual adjustment
    AUTO_LEARN = "auto_learn"          # Learned from telemetry
    OPERATOR_OVERRIDE = "operator_override"  # Operator one-time override
    PROMOTED = "promoted"              # Promoted to preset
    IMPORTED = "imported"              # Imported from external source


class LaneKey(BaseModel):
    """4-tuple lane identifier."""
    tool_id: str                       # Blade ID from registry
    material: str                      # Material family (hardwood, softwood, etc.)
    mode: str                          # Operation mode (rip, crosscut, contour)
    machine_profile: str               # Machine identifier


class ParameterOverride(BaseModel):
    """Single parameter override with metadata."""
    param_name: str                    # feed_ipm, rpm, doc_mm, etc.
    value: float                       # Override value
    scale: float = 1.0                 # Multiplier relative to baseline
    source: OverrideSource            # Where this came from
    confidence: float = 1.0            # 0.0-1.0 confidence score
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    operator: Optional[str] = None     # Operator who made change
    notes: Optional[str] = None


class LaneOverrides(BaseModel):
    """All overrides for a specific lane."""
    lane_key: LaneKey
    overrides: Dict[str, ParameterOverride] = {}  # param_name -> override
    lane_scale: float = 1.0            # Overall lane adjustment factor
    run_count: int = 0                 # Number of successful runs
    success_rate: float = 1.0          # Success rate (0.0-1.0)
    last_run: Optional[str] = None     # ISO timestamp of last run
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AuditEntry(BaseModel):
    """Audit trail entry for override changes."""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    lane_key: LaneKey
    param_name: str
    source: OverrideSource
    prev_value: Optional[float]
    new_value: float
    prev_scale: Optional[float]
    new_scale: float
    operator: Optional[str] = None
    reason: Optional[str] = None
