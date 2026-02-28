# server/app/schemas/job_log.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field

RiskGrade = Literal["GREEN", "YELLOW", "RED"]


class SliceRiskSummary(BaseModel):
    """
    Per-slice / per-ring risk summary for saw jobs.
    """
    index: int
    kind: Literal["line", "ring"] = "line"
    offset_mm: float
    risk_grade: RiskGrade
    rim_speed_m_min: float
    doc_grade: RiskGrade
    gantry_grade: RiskGrade


class BaseJobLog(BaseModel):
    """
    Common fields shared by all job log entries.
    """
    id: str = Field(..., description="Unique job id, e.g. rosette_batch_2025-11-20-001")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    job_type: str
    pipeline_id: Optional[str] = None
    node_id: Optional[str] = None

    # Freeform extras for future expansion / debugging.
    extra: Dict[str, Any] = Field(default_factory=dict)


class SawBatchJobLog(BaseJobLog):
    """
    JobLog entry for actual saw cutting jobs (line or circle batches).
    """
    job_type: Literal["saw_slice_batch", "saw_slice"]

    machine_profile: Optional[str] = None
    machine_gantry_span_mm: Optional[float] = None

    tool_id: str
    material: str
    workholding: str

    num_slices: int
    slice_thickness_mm: float
    passes: int

    overall_risk_grade: RiskGrade
    slice_risks: List[SliceRiskSummary] = Field(default_factory=list)

    # Derived or manually added
    yield_estimate: Optional[int] = None
    best_slice_indices: List[int] = Field(default_factory=list)
    operator_notes: Optional[str] = None


class RosettePlanJobLog(BaseJobLog):
    """
    JobLog entry for planning-only jobs (no cutting, just ManufacturingPlan).
    """
    job_type: Literal["rosette_plan"]

    plan_pattern_id: str
    plan_guitars: int
    plan_total_tiles: int

    # High-level "sanity" flag for plan; can be GREEN unless planner adds more nuance.
    summary_risk_grade: RiskGrade = "GREEN"


# Unified type used by APIs and in-memory store.
JobLogEntry = Union[SawBatchJobLog, RosettePlanJobLog]
