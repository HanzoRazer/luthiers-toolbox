from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class PipelineHandoffRequest(BaseModel):
    pattern_id: str = Field(..., description="Rosette pattern id")
    batch_op: Dict[str, Any] = Field(..., description="SawSlice batch operation payload")
    manufacturing_plan: Optional[Dict[str, Any]] = Field(
        None, description="Optional plan snapshot"
    )
    lane: str = Field("rosette", description="Pipeline lane/category")
    machine_profile: str = Field("default_saw_rig", description="Target machine profile")
    priority: Literal["low", "normal", "high"] = "normal"
    notes: Optional[str] = None


class PipelineHandoffResponse(BaseModel):
    success: bool
    handoff_mode: Literal["pipeline_service", "local_queue"]
    job_id: str
    message: str
    payload_path: Optional[str] = None
