"""Pydantic models for body generator router."""
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field

class ToolConfigModel(BaseModel):
    """Tool configuration model."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    stepover_pct: float

class MachineConfigModel(BaseModel):
    """Machine configuration model."""
    name: str
    max_x_in: float
    max_y_in: float
    max_z_in: float
    safe_z_in: float = 0.75
    retract_z_in: float = 0.25
    rapid_rate: float = 200.0

class AnalyzeResponse(BaseModel):
    """DXF analysis results."""
    filepath: str
    body_outline: Optional[Dict[str, Any]]
    layers: Dict[str, Dict[str, int]]
    origin_offset: Tuple[float, float]
    recommended_operations: List[str]

class GenerateRequest(BaseModel):
    """Request to generate body G-code."""
    post_id: str = Field("Mach4", description="Post-processor ID")
    machine: str = Field("txrx_router", description="Machine configuration")
    stock_thickness_in: float = Field(1.75, description="Stock thickness in inches")
    tab_count: int = Field(6, description="Number of holding tabs")
    tab_width_in: float = Field(0.5, description="Tab width in inches")
    tab_height_in: float = Field(0.125, description="Tab height in inches")
    job_name: Optional[str] = None

class GenerateResponse(BaseModel):
    """Body G-code generation results."""
    gcode: str
    post_id: str
    job_name: str
    stats: Dict[str, Any]
    body_size: Dict[str, float]

class GenerateGovernedResponse(BaseModel):
    """Body G-code generation results with RMOS tracking."""
    gcode: str
    post_id: str
    job_name: str
    stats: Dict[str, Any]
    body_size: Dict[str, float]
    run_id: str
    request_hash: str
    gcode_hash: str

class MultiExportRequest(BaseModel):
    """Request for multi-post ZIP export."""
    post_ids: List[str] = Field(["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"], description="Post-processor IDs")
    machine: str = "txrx_router"
    stock_thickness_in: float = 1.75
    tab_count: int = 6
    job_name: Optional[str] = None
