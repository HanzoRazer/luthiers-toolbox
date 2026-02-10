"""
Pydantic schemas for calculators router.

Extracted from calculators_consolidated_router.py (Phase 13 decomposition).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


# ============================================================================
# CAM Calculator Models
# ============================================================================

ToolKind = Literal["router_bit", "saw_blade"]


class CutOperationPayload(BaseModel):
    """Request payload for cut operation evaluation."""
    tool_id: str = Field(..., description="Tool identifier from tool library")
    material_id: str = Field(..., description="Material identifier")
    tool_kind: ToolKind = Field(..., description="Type of cutting tool")
    feed_mm_min: float = Field(..., gt=0, description="Feed rate in mm/min")
    rpm: float = Field(..., gt=0, description="Spindle/blade RPM")
    depth_of_cut_mm: float = Field(..., gt=0, description="Axial depth of cut")
    width_of_cut_mm: Optional[float] = Field(None, gt=0, description="Radial width of cut")
    tool_diameter_mm: Optional[float] = Field(None, gt=0, description="Tool diameter")
    flute_count: Optional[int] = Field(None, gt=0, description="Number of flutes/teeth")
    machine_id: Optional[str] = None
    profile_id: Optional[str] = None


class CAMCalculatorBundleResponse(BaseModel):
    """Response with all CAM calculator results."""
    tool_id: str
    material_id: str
    tool_kind: str
    chipload: Optional[Dict[str, Any]] = None
    heat: Optional[Dict[str, Any]] = None
    deflection: Optional[Dict[str, Any]] = None
    rim_speed: Optional[Dict[str, Any]] = None
    kickback: Optional[Dict[str, Any]] = None
    bite_per_tooth: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    hard_failures: List[str] = []
    overall_risk: str = "GREEN"


# ============================================================================
# Math Calculator Models
# ============================================================================

class MathEvaluateRequest(BaseModel):
    expression: str = Field(..., description="Math expression to evaluate")


class MathEvaluateResponse(BaseModel):
    result: float
    display: str
    error: Optional[str] = None


class FractionRequest(BaseModel):
    decimal: float = Field(..., description="Decimal to convert")
    precision: int = Field(16, description="Max denominator (8, 16, 32, 64)")


class FractionResponse(BaseModel):
    decimal: float
    fraction: str
    numerator: int
    denominator: int
    whole: int


class TVMRequest(BaseModel):
    """Time Value of Money calculation request."""
    n: Optional[float] = Field(None, description="Number of periods")
    i_y: Optional[float] = Field(None, description="Interest rate per period (%)")
    pv: Optional[float] = Field(None, description="Present Value")
    pmt: Optional[float] = Field(None, description="Payment per period")
    fv: Optional[float] = Field(None, description="Future Value")
    solve_for: str = Field(..., description="Variable to solve: n, i_y, pv, pmt, or fv")
    begin_mode: bool = Field(False, description="Payment at beginning of period")


class TVMResponse(BaseModel):
    result: float
    variable: str
    inputs: dict


# ============================================================================
# Luthier Calculator Models
# ============================================================================

class RadiusFrom3PointsRequest(BaseModel):
    p1: Tuple[float, float] = Field(..., description="Point 1 (x, y)")
    p2: Tuple[float, float] = Field(..., description="Point 2 (x, y)")
    p3: Tuple[float, float] = Field(..., description="Point 3 (x, y)")


class RadiusFromChordRequest(BaseModel):
    chord_length: float = Field(..., description="Length of chord/straightedge")
    height: float = Field(..., description="Arc height at center (sagitta)")


class CompoundRadiusRequest(BaseModel):
    nut_radius: float
    saddle_radius: float
    scale_length: float
    position: float = Field(..., description="Distance from nut")


class WedgeAngleRequest(BaseModel):
    length: float
    thick_end: float
    thin_end: float


class BoardFeetRequest(BaseModel):
    thickness: float
    width: float
    length: float
    quarters: bool = Field(False, description="Thickness in quarters (4/4, 8/4)")
