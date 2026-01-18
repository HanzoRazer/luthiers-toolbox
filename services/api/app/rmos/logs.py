# services/api/app/rmos/logs.py
"""
RMOS Event Logging System.

Provides in-memory logging of RMOS feasibility events for debugging and analytics.

Features:
- In-memory ring buffer (max 500 entries)
- Full design snapshots for "jump to design" functionality
- Filterable by source, mode, risk_bucket
- CSV export for spreadsheet analysis
"""

from __future__ import annotations

import csv
import io
from collections import deque
from datetime import datetime, timezone
from typing import Deque, List, Optional, Dict, Any

from pydantic import BaseModel, Field

from .api_contracts import RiskBucket, RmosContext, RmosFeasibilityResult


class RosetteDesignSnapshot(BaseModel):
    """Snapshot of a rosette design for logging."""
    outer_diameter_mm: float
    inner_diameter_mm: float
    ring_count: int
    ring_params: List[Dict[str, Any]] = Field(default_factory=list)
    depth_mm: float = 3.0


class RmosLogEntry(BaseModel):
    """
    Single RMOS feasibility event log.
    
    Captures key design stats, risk, and context snapshots.
    Includes full design for "jump to design" functionality.
    """
    
    id: int = Field(..., description="Monotonic ID within this process.")
    timestamp: datetime = Field(..., description="UTC timestamp of the event.")
    
    source: str = Field(
        ...,
        description="Logical source: 'directional_mode', 'art_studio_batch', 'constraint_search'."
    )
    mode: Optional[str] = Field(
        default=None,
        description="Workflow mode: 'design_first', 'constraint_first', 'ai_assisted'."
    )
    
    # Full design snapshot (for jump-to-design)
    design: RosetteDesignSnapshot = Field(
        ...,
        description="The exact design evaluated in this event."
    )
    
    # Design summary (denormalized for quick access)
    design_outer_diameter_mm: float
    design_inner_diameter_mm: float
    ring_count: int
    
    # Feasibility summary
    overall_score: float = Field(..., description="Feasibility score 0-100.")
    risk_bucket: RiskBucket = Field(..., description="Overall risk: GREEN/YELLOW/RED.")
    estimated_cut_time_min: float = Field(..., description="Estimated cut time (min).")
    material_efficiency: float = Field(..., description="Material efficiency 0-1.")
    
    # Context snapshot
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    machine_profile_id: Optional[str] = None
    risk_tolerance: Optional[RiskBucket] = None
    max_cut_time_min: Optional[float] = None
    waste_tolerance: Optional[float] = None
    
    # Warnings
    warnings: List[str] = Field(default_factory=list)


# In-memory log buffer
_MAX_LOG_ENTRIES: int = 500
_LOG_BUFFER: Deque[RmosLogEntry] = deque(maxlen=_MAX_LOG_ENTRIES)
_LOG_COUNTER: int = 0


def _next_id() -> int:
    """Get next monotonic log ID."""
    global _LOG_COUNTER
    _LOG_COUNTER += 1
    return _LOG_COUNTER


def log_feasibility_event(
    *,
    source: str,
    mode: Optional[str],
    design: Any,  # RosetteParamSpec or similar
    context: Optional[RmosContext],
    result: RmosFeasibilityResult,
) -> RmosLogEntry:
    """
    Record a single RMOS feasibility event into the in-memory buffer.
    
    Args:
        source: Logical source of the call
        mode: Workflow mode if known
        design: The rosette design evaluated
        context: RMOS context used
        result: Feasibility result
    
    Returns:
        The created log entry
    """
    now = datetime.now(timezone.utc)
    
    # Extract design info
    outer_d = getattr(design, 'outer_diameter_mm', 100.0)
    inner_d = getattr(design, 'inner_diameter_mm', 90.0)
    ring_params = getattr(design, 'ring_params', [])
    ring_count = len(ring_params) if ring_params else 0
    depth = getattr(design, 'depth_mm', 3.0)
    
    # Build ring params list
    ring_params_list = []
    for rp in ring_params:
        if hasattr(rp, 'dict'):
            ring_params_list.append(rp.dict())
        elif hasattr(rp, 'model_dump'):
            ring_params_list.append(rp.model_dump())
        elif isinstance(rp, dict):
            ring_params_list.append(rp)
        else:
            ring_params_list.append({
                "ring_index": getattr(rp, 'ring_index', 0),
                "width_mm": getattr(rp, 'width_mm', 2.0),
                "tile_length_mm": getattr(rp, 'tile_length_mm', None)
            })
    
    # Build design snapshot
    design_snapshot = RosetteDesignSnapshot(
        outer_diameter_mm=outer_d,
        inner_diameter_mm=inner_d,
        ring_count=ring_count,
        ring_params=ring_params_list,
        depth_mm=depth,
    )
    
    # Extract context info
    material_id = getattr(context, 'material_id', None) if context else None
    tool_id = getattr(context, 'tool_id', None) if context else None
    machine_profile_id = getattr(context, 'machine_profile_id', None) if context else None
    risk_tolerance = getattr(context, 'risk_tolerance', None) if context else None
    max_cut_time = getattr(context, 'max_cut_time_min', None) if context else None
    waste_tol = getattr(context, 'waste_tolerance', None) if context else None
    
    # Create entry
    entry = RmosLogEntry(
        id=_next_id(),
        timestamp=now,
        source=source,
        mode=mode,
        design=design_snapshot,
        design_outer_diameter_mm=outer_d,
        design_inner_diameter_mm=inner_d,
        ring_count=ring_count,
        overall_score=result.score,
        risk_bucket=result.risk_bucket,
        estimated_cut_time_min=result.estimated_cut_time_seconds / 60.0,
        material_efficiency=result.efficiency,
        material_id=material_id,
        tool_id=tool_id,
        machine_profile_id=machine_profile_id,
        risk_tolerance=risk_tolerance,
        max_cut_time_min=max_cut_time,
        waste_tolerance=waste_tol,
        warnings=result.warnings,
    )
    
    _LOG_BUFFER.append(entry)
    return entry


def get_recent_logs(
    limit: int = 50,
    *,
    source: Optional[str] = None,
    mode: Optional[str] = None,
    risk_bucket: Optional[RiskBucket] = None,
) -> List[RmosLogEntry]:
    """
    Return up to `limit` most recent log entries (newest first), with optional filters.
    
    Args:
        limit: Maximum entries to return
        source: Filter by source string
        mode: Filter by workflow mode
        risk_bucket: Filter by risk level
    
    Returns:
        List of matching log entries, newest first
    """
    if limit <= 0:
        return []
    
    filtered: List[RmosLogEntry] = []
    for entry in reversed(_LOG_BUFFER):
        if source is not None and entry.source != source:
            continue
        if mode is not None and entry.mode != mode:
            continue
        if risk_bucket is not None and entry.risk_bucket != risk_bucket:
            continue
        
        filtered.append(entry)
        if len(filtered) >= limit:
            break
    
    return filtered


def logs_to_csv(entries: List[RmosLogEntry]) -> str:
    """
    Convert a list of RmosLogEntry objects into CSV text.
    
    Note: Full design is not exported, only summary columns.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "id",
        "timestamp",
        "source",
        "mode",
        "design_outer_diameter_mm",
        "design_inner_diameter_mm",
        "ring_count",
        "overall_score",
        "risk_bucket",
        "estimated_cut_time_min",
        "material_efficiency",
        "material_id",
        "tool_id",
        "machine_profile_id",
        "warnings",
    ])
    
    for e in entries:
        risk_str = e.risk_bucket.value if hasattr(e.risk_bucket, 'value') else str(e.risk_bucket)
        warnings_str = "; ".join(e.warnings) if e.warnings else ""
        
        writer.writerow([
            e.id,
            e.timestamp.isoformat(),
            e.source,
            e.mode or "",
            e.design_outer_diameter_mm,
            e.design_inner_diameter_mm,
            e.ring_count,
            e.overall_score,
            risk_str,
            round(e.estimated_cut_time_min, 2),
            round(e.material_efficiency, 3),
            e.material_id or "",
            e.tool_id or "",
            e.machine_profile_id or "",
            warnings_str,
        ])
    
    return output.getvalue()


def clear_logs() -> int:
    """
    Clear all log entries. Returns count of cleared entries.
    """
    count = len(_LOG_BUFFER)
    _LOG_BUFFER.clear()
    return count


# =============================================================================
# Promotion Intent Logging (Bundle 32.7.1)
# =============================================================================

class PromotionIntentLogEntry(BaseModel):
    """Log entry for design-first workflow promotion intent events."""
    
    id: int = Field(..., description="Monotonic ID within this process.")
    timestamp: datetime = Field(..., description="UTC timestamp of the event.")
    session_id: str = Field(..., description="Design-first workflow session ID.")
    approved: bool = Field(..., description="True if intent was generated, False if blocked.")
    blocked_reason: Optional[str] = Field(
        default=None,
        description="Reason if blocked (e.g., 'workflow_not_approved')."
    )
    mode: str = Field(default="design_first", description="Workflow mode.")
    design_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Design parameters at time of intent request."
    )


_INTENT_LOG_BUFFER: Deque[PromotionIntentLogEntry] = deque(maxlen=_MAX_LOG_ENTRIES)


def log_promotion_intent_event(
    *,
    session_id: str,
    approved: bool,
    blocked_reason: Optional[str] = None,
    mode: str = "design_first",
    design_snapshot: Optional[Dict[str, Any]] = None,
) -> PromotionIntentLogEntry:
    """
    Record a promotion intent event into the in-memory buffer.
    
    Called when a design-first workflow requests CAM handoff intent.
    
    Args:
        session_id: The workflow session ID
        approved: True if intent generated, False if blocked
        blocked_reason: Reason string if blocked
        mode: Workflow mode
        design_snapshot: Design parameters at request time
    
    Returns:
        The created log entry
    """
    import logging
    
    now = datetime.now(timezone.utc)
    
    entry = PromotionIntentLogEntry(
        id=_next_id(),
        timestamp=now,
        session_id=session_id,
        approved=approved,
        blocked_reason=blocked_reason,
        mode=mode,
        design_snapshot=design_snapshot,
    )
    
    _INTENT_LOG_BUFFER.append(entry)
    
    # Also emit to standard logging for observability
    log = logging.getLogger("rmos.promotion_intent")
    log.info(
        "promotion_intent session_id=%s approved=%s blocked_reason=%s",
        session_id,
        approved,
        blocked_reason,
    )
    
    return entry


def get_recent_intent_logs(limit: int = 50) -> List[PromotionIntentLogEntry]:
    """Return up to `limit` most recent promotion intent log entries (newest first)."""
    if limit <= 0:
        return []
    return list(reversed(_INTENT_LOG_BUFFER))[:limit]
