# services/api/app/rmos/logging_ai.py
"""
AI Logging + Analytics Wrapper for RMOS constraint search loops.
Records every AI candidate + feasibility result for analysis.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .api_contracts import RiskBucket, RmosContext, RmosFeasibilityResult

# Lazy import for RosetteParamSpec
try:
    from .models import RosetteParamSpec, SearchBudgetSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from pydantic import BaseModel as RosetteParamSpec  # type: ignore
    from pydantic import BaseModel as SearchBudgetSpec  # type: ignore


# ---------------------------------------------------------------------
# Integration with existing RMOS logging system
# ---------------------------------------------------------------------

try:
    from .logging_core import log_rmos_event  # type: ignore[import]
except ImportError:  # WP-1: narrowed from except Exception
    def log_rmos_event(event_type: str, payload: Dict[str, Any]) -> None:
        """Safe no-op fallback if the core RMOS logging system is not available."""
        return


# ---------------------------------------------------------------------
# Log models
# ---------------------------------------------------------------------


class AiConstraintSearchAttemptLog(BaseModel):
    """Structured log entry for a single candidate in a constraint-first / AI run."""

    run_id: str = Field(..., description="UUID that groups all attempts in a run.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp for this attempt.",
    )

    attempt_index: int = Field(..., ge=1)
    workflow_mode: str = Field(..., description="constraint_first / ai_assisted, etc.")

    # Context
    tool_id: Optional[str] = Field(default=None)
    material_id: Optional[str] = Field(default=None)
    machine_id: Optional[str] = Field(default=None)

    geometry_engine: Optional[str] = Field(default=None)

    # Result metrics
    score: float = Field(..., description="Feasibility overall_score.")
    risk_bucket: RiskBucket
    is_acceptable: bool = Field(...)

    # Optional lightweight design summary
    design_version: Optional[str] = None
    ring_count: Optional[int] = None
    notes: Optional[str] = None


class AiConstraintSearchRunSummaryLog(BaseModel):
    """Aggregated summary for an entire constraint-first / AI run."""

    run_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    workflow_mode: str
    max_attempts: int
    time_limit_seconds: float

    attempts: int
    success: bool
    reason: str

    # Best / selected candidate info
    selected_score: Optional[float] = None
    selected_risk_bucket: Optional[RiskBucket] = None

    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None

    geometry_engine: Optional[str] = None


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _infer_geometry_engine(ctx: RmosContext) -> Optional[str]:
    """Map RmosContext flags into a simple geometry_engine string."""
    try:
        if getattr(ctx, "use_shapely_geometry", False):
            return "shapely"
        if getattr(ctx, "use_ml_geometry", False):
            return "ml"
    except (AttributeError, TypeError):  # WP-1: narrowed from except Exception
        pass
    return None


def _extract_design_summary(design: Any) -> Dict[str, Any]:
    """Extract a lightweight, non-geometry summary from a RosetteParamSpec."""
    summary: Dict[str, Any] = {}
    summary["design_version"] = getattr(design, "version", None)
    rings = getattr(design, "rings", None)
    if rings is not None:
        try:
            summary["ring_count"] = len(rings)
        except TypeError:
            summary["ring_count"] = None
    summary["notes"] = getattr(design, "notes", None)
    return summary


def _extract_context_ids(ctx: RmosContext) -> Dict[str, Optional[str]]:
    tool_id = getattr(ctx, "tool_id", None)
    material_id = getattr(ctx, "material_id", None)
    machine_id = getattr(ctx, "machine_profile_id", None)
    return {
        "tool_id": tool_id,
        "material_id": material_id,
        "machine_id": machine_id,
    }


# ---------------------------------------------------------------------
# Public logging functions
# ---------------------------------------------------------------------


def new_run_id() -> str:
    """Generate a new UUID for grouping all log events in a single search."""
    return str(uuid.uuid4())


def log_ai_constraint_attempt(
    *,
    run_id: str,
    attempt_index: int,
    workflow_mode: str,
    ctx: RmosContext,
    design: Any,
    feasibility: RmosFeasibilityResult,
    is_acceptable: bool,
) -> None:
    """Log a single candidate evaluation during a constraint-first / AI run."""
    context_ids = _extract_context_ids(ctx)
    geom_engine = _infer_geometry_engine(ctx)
    design_summary = _extract_design_summary(design)

    # Get score - handle both .score and .overall_score
    score = getattr(feasibility, "overall_score", None)
    if score is None:
        score = getattr(feasibility, "score", 0.0)

    entry = AiConstraintSearchAttemptLog(
        run_id=run_id,
        attempt_index=attempt_index,
        workflow_mode=workflow_mode,
        tool_id=context_ids["tool_id"],
        material_id=context_ids["material_id"],
        machine_id=context_ids["machine_id"],
        geometry_engine=geom_engine,
        score=score,
        risk_bucket=feasibility.risk_bucket,
        is_acceptable=is_acceptable,
        design_version=design_summary.get("design_version"),
        ring_count=design_summary.get("ring_count"),
        notes=design_summary.get("notes"),
    )

    log_rmos_event("ai_constraint_attempt", entry.model_dump())


def log_ai_constraint_run_summary(
    *,
    run_id: str,
    workflow_mode: str,
    budget: Any,
    ctx: RmosContext,
    attempts: int,
    success: bool,
    reason: str,
    selected_feasibility: Optional[RmosFeasibilityResult],
) -> None:
    """Log the overall outcome of a constraint-first / AI run."""
    context_ids = _extract_context_ids(ctx)
    geom_engine = _infer_geometry_engine(ctx)

    selected_score: Optional[float] = None
    selected_risk: Optional[RiskBucket] = None
    if selected_feasibility is not None:
        selected_score = getattr(selected_feasibility, "overall_score", None)
        if selected_score is None:
            selected_score = getattr(selected_feasibility, "score", None)
        selected_risk = selected_feasibility.risk_bucket

    max_attempts = getattr(budget, "max_attempts", 50)
    time_limit = getattr(budget, "time_limit_seconds", 30.0)

    entry = AiConstraintSearchRunSummaryLog(
        run_id=run_id,
        workflow_mode=workflow_mode,
        max_attempts=max_attempts,
        time_limit_seconds=time_limit,
        attempts=attempts,
        success=success,
        reason=reason,
        selected_score=selected_score,
        selected_risk_bucket=selected_risk,
        tool_id=context_ids["tool_id"],
        material_id=context_ids["material_id"],
        machine_id=context_ids["machine_id"],
        geometry_engine=geom_engine,
    )

    log_rmos_event("ai_constraint_run_summary", entry.model_dump())
