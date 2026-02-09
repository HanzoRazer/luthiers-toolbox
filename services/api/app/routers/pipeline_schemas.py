"""Pydantic models for CAM pipeline router."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# --- TYPE DEFINITIONS ---
PipelineOpKind = Literal[
    "dxf_preflight", "adaptive_plan", "adaptive_plan_run", "export_post", "simulate_gcode"
]

# --- VALIDATION CONSTANTS ---
DEFAULT_TOOL_DIAMETER_MM: float = 6.0

# --- PYDANTIC MODELS ---
class PipelineOp(BaseModel):
    """Single pipeline operation with optional params override."""
    id: Optional[str] = Field(None, description="Optional operation ID for tracking")
    kind: PipelineOpKind
    params: Dict[str, Any] = Field(default_factory=dict, description="Op-specific params.")

class PipelineRequest(BaseModel):
    """Pipeline request with ops list and shared context."""
    ops: List[PipelineOp] = Field(..., description="Operations to apply to uploaded DXF.")
    tool_d: float = DEFAULT_TOOL_DIAMETER_MM
    units: Literal["mm", "inch"] = "mm"
    geometry_layer: Optional[str] = Field(None, description="DXF geometry layer.")
    auto_scale: bool = True
    cam_layer_prefix: str = "CAM_"
    machine_id: Optional[str] = Field(None, description="Machine profile ID.")
    post_id: Optional[str] = Field(None, description="Post preset ID.")

class PipelineOpResult(BaseModel):
    """Result of single pipeline operation (ok, error, payload)."""
    id: Optional[str] = None
    kind: PipelineOpKind
    ok: bool
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class PipelineResponse(BaseModel):
    """Complete pipeline result with per-op status and summary stats."""
    ops: List[PipelineOpResult]
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary stats.")
    job_int: Optional[Dict[str, Any]] = Field(default=None, description="Job intelligence payload.")
