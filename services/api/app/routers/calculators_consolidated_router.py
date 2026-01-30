"""
Consolidated Calculators Router - Math, CAM, and Luthier calculations.

Consolidates:
- calculators_router.py (CAM cutting parameters)
- ltb_calculator_router.py (luthier math calculations)

Endpoints:
  CAM Cutting:
    - POST /cam/evaluate - Evaluate cut operation (chipload, heat, deflection)
    - POST /cam/evaluate-cut - Alias for above
    - GET /cam/health - CAM calculator health check

  Math:
    - POST /math/evaluate - Evaluate math expression
    - POST /math/fraction/convert - Decimal to fraction
    - GET /math/fraction/parse/{text} - Parse fraction to decimal
    - POST /math/tvm - Time Value of Money calculation

  Luthier:
    - POST /luthier/radius/from-3-points - Radius from 3 curve points
    - POST /luthier/radius/from-chord - Radius from chord/height
    - POST /luthier/radius/compound - Compound fretboard radius
    - POST /luthier/wedge/angle - Wedge angle calculation
    - POST /luthier/board-feet - Board feet calculation
    - GET /luthier/miter/{num_sides} - Miter angle for polygon
    - GET /luthier/dovetail/{ratio} - Dovetail angle from ratio
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import luthier calculator classes
from ..ltb_calculators import (
    LTBFractionCalculator,
    LTBScientificCalculator,
    LTBFinancialCalculator,
    LTBLuthierCalculator,
)


router = APIRouter(tags=["calculators"])


# ============================================================================
# CAM Calculator Models and Functions
# ============================================================================

@dataclass
class ChiploadResult:
    """Chipload calculation result."""
    chipload_mm: Optional[float]
    in_range: bool
    min_recommended_mm: Optional[float] = None
    max_recommended_mm: Optional[float] = None
    message: str = ""


@dataclass
class HeatResult:
    """Heat risk assessment."""
    heat_risk: float  # 0-1, where 1 is worst
    category: str  # "COOL" / "WARM" / "HOT"
    message: str = ""


@dataclass
class DeflectionResult:
    """Tool deflection assessment."""
    deflection_mm: Optional[float]
    risk: str  # "GREEN" / "YELLOW" / "RED"
    message: str = ""


@dataclass
class RimSpeedResult:
    """Saw blade rim speed result."""
    surface_speed_m_per_min: Optional[float]
    within_limits: bool
    max_recommended_m_per_min: Optional[float] = None
    message: str = ""


@dataclass
class KickbackRiskResult:
    """Saw blade kickback risk assessment."""
    risk_score: float  # 0-1
    category: str  # "LOW" / "MEDIUM" / "HIGH"
    message: str = ""


@dataclass
class BitePerToothResult:
    """Saw blade bite per tooth (feed per tooth)."""
    bite_mm: Optional[float]
    in_range: bool
    min_recommended_mm: Optional[float] = None
    max_recommended_mm: Optional[float] = None
    message: str = ""


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


def calculate_chipload(
    feed_mm_min: float, rpm: float, flute_count: int,
    min_chipload: float = 0.05, max_chipload: float = 0.25
) -> ChiploadResult:
    """Calculate chipload (feed per tooth) for router bits."""
    if rpm <= 0 or flute_count <= 0:
        return ChiploadResult(chipload_mm=None, in_range=False, message="Invalid RPM or flute count")

    chipload = feed_mm_min / (rpm * flute_count)
    in_range = min_chipload <= chipload <= max_chipload

    if chipload < min_chipload:
        message = f"Chipload {chipload:.4f}mm below min ({min_chipload}mm) - rubbing risk"
    elif chipload > max_chipload:
        message = f"Chipload {chipload:.4f}mm exceeds max ({max_chipload}mm) - breakage risk"
    else:
        message = f"Chipload {chipload:.4f}mm within recommended range"

    return ChiploadResult(chipload_mm=chipload, in_range=in_range,
                         min_recommended_mm=min_chipload, max_recommended_mm=max_chipload, message=message)


def calculate_heat_risk(
    chipload_mm: Optional[float], rpm: float, depth_of_cut_mm: float,
    material_heat_sensitivity: float = 0.5
) -> HeatResult:
    """Estimate heat risk based on cutting parameters."""
    if chipload_mm is None or chipload_mm <= 0:
        return HeatResult(heat_risk=0.8, category="HOT", message="Unable to calculate chipload - high heat risk")

    chipload_factor = max(0, 1 - (chipload_mm / 0.15))
    rpm_factor = min(1, rpm / 20000)
    depth_factor = min(1, depth_of_cut_mm / 10)
    heat_risk = (chipload_factor * 0.4 + rpm_factor * 0.3 + depth_factor * 0.2 + material_heat_sensitivity * 0.1)
    heat_risk = min(1.0, max(0.0, heat_risk))

    if heat_risk < 0.3:
        return HeatResult(heat_risk=heat_risk, category="COOL", message="Low heat risk")
    elif heat_risk < 0.6:
        return HeatResult(heat_risk=heat_risk, category="WARM", message="Moderate heat risk - monitor for burns")
    else:
        return HeatResult(heat_risk=heat_risk, category="HOT", message="High heat risk - reduce RPM or increase feed")


def calculate_deflection(
    tool_diameter_mm: float, depth_of_cut_mm: float,
    width_of_cut_mm: Optional[float], stickout_mm: float = 25.0
) -> DeflectionResult:
    """Estimate tool deflection risk."""
    if tool_diameter_mm <= 0:
        return DeflectionResult(deflection_mm=None, risk="RED", message="Invalid tool diameter")

    stickout_ratio = stickout_mm / tool_diameter_mm
    woc = width_of_cut_mm if width_of_cut_mm else tool_diameter_mm * 0.5
    force_proxy = depth_of_cut_mm * woc
    deflection_mm = (stickout_ratio ** 3) * force_proxy * 0.0001

    if deflection_mm < 0.05:
        return DeflectionResult(deflection_mm=deflection_mm, risk="GREEN", message=f"Low deflection ({deflection_mm:.4f}mm)")
    elif deflection_mm < 0.15:
        return DeflectionResult(deflection_mm=deflection_mm, risk="YELLOW", message=f"Moderate deflection ({deflection_mm:.4f}mm)")
    else:
        return DeflectionResult(deflection_mm=deflection_mm, risk="RED", message=f"High deflection ({deflection_mm:.4f}mm)")


def calculate_rim_speed(blade_diameter_mm: float, rpm: float, max_rim_speed: float = 80.0) -> RimSpeedResult:
    """Calculate saw blade rim speed."""
    if blade_diameter_mm <= 0 or rpm <= 0:
        return RimSpeedResult(surface_speed_m_per_min=None, within_limits=False, message="Invalid parameters")

    rim_speed = math.pi * blade_diameter_mm * rpm / 1000
    within_limits = rim_speed <= max_rim_speed

    if within_limits:
        message = f"Rim speed {rim_speed:.1f} m/min within limits"
    else:
        message = f"Rim speed {rim_speed:.1f} m/min EXCEEDS maximum ({max_rim_speed} m/min)"

    return RimSpeedResult(surface_speed_m_per_min=rim_speed, within_limits=within_limits,
                         max_recommended_m_per_min=max_rim_speed, message=message)


def calculate_bite_per_tooth(
    feed_mm_min: float, rpm: float, tooth_count: int,
    min_bite: float = 0.05, max_bite: float = 0.20
) -> BitePerToothResult:
    """Calculate saw blade bite per tooth."""
    if rpm <= 0 or tooth_count <= 0:
        return BitePerToothResult(bite_mm=None, in_range=False, message="Invalid parameters")

    bite = feed_mm_min / (rpm * tooth_count)
    in_range = min_bite <= bite <= max_bite

    if bite < min_bite:
        message = f"Bite {bite:.4f}mm below min - rubbing risk"
    elif bite > max_bite:
        message = f"Bite {bite:.4f}mm exceeds max - tooth damage risk"
    else:
        message = f"Bite {bite:.4f}mm within recommended range"

    return BitePerToothResult(bite_mm=bite, in_range=in_range,
                             min_recommended_mm=min_bite, max_recommended_mm=max_bite, message=message)


def calculate_kickback_risk(depth_of_cut_mm: float, blade_diameter_mm: float,
                           tooth_count: int, feed_mm_min: float) -> KickbackRiskResult:
    """Estimate kickback risk for saw operations."""
    max_depth = blade_diameter_mm * 0.4
    depth_ratio = min(1.0, depth_of_cut_mm / max_depth) if max_depth > 0 else 1.0
    feed_factor = min(1.0, feed_mm_min / 5000)
    tooth_factor = max(0, 1 - (tooth_count / 100))

    risk_score = depth_ratio * 0.5 + feed_factor * 0.3 + tooth_factor * 0.2
    risk_score = min(1.0, max(0.0, risk_score))

    if risk_score < 0.3:
        return KickbackRiskResult(risk_score=risk_score, category="LOW", message="Low kickback risk")
    elif risk_score < 0.6:
        return KickbackRiskResult(risk_score=risk_score, category="MEDIUM", message="Moderate kickback - ensure workholding")
    else:
        return KickbackRiskResult(risk_score=risk_score, category="HIGH", message="HIGH kickback risk - reduce depth/feed")


def evaluate_cut_operation(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Evaluate a cut operation and return all calculator results."""
    warnings: List[str] = []
    hard_failures: List[str] = []

    tool_diameter = payload.tool_diameter_mm or 6.0
    flute_count = payload.flute_count or 2

    chipload_res = heat_res = deflection_res = None
    rim_speed_res = kickback_res = bite_res = None

    if payload.tool_kind == "router_bit":
        chipload_res = calculate_chipload(payload.feed_mm_min, payload.rpm, flute_count)
        heat_res = calculate_heat_risk(chipload_res.chipload_mm, payload.rpm, payload.depth_of_cut_mm)
        deflection_res = calculate_deflection(tool_diameter, payload.depth_of_cut_mm, payload.width_of_cut_mm)

        if not chipload_res.in_range:
            warnings.append(chipload_res.message)
        if heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if deflection_res.risk == "RED":
            hard_failures.append(deflection_res.message)
        elif deflection_res.risk == "YELLOW":
            warnings.append(deflection_res.message)

    elif payload.tool_kind == "saw_blade":
        rim_speed_res = calculate_rim_speed(tool_diameter, payload.rpm)
        bite_res = calculate_bite_per_tooth(payload.feed_mm_min, payload.rpm, flute_count)
        heat_res = calculate_heat_risk(bite_res.bite_mm if bite_res else None, payload.rpm, payload.depth_of_cut_mm)
        kickback_res = calculate_kickback_risk(payload.depth_of_cut_mm, tool_diameter, flute_count, payload.feed_mm_min)

        if not rim_speed_res.within_limits:
            hard_failures.append(rim_speed_res.message)
        if not bite_res.in_range:
            warnings.append(bite_res.message)
        if heat_res.category == "HOT":
            warnings.append(heat_res.message)
        if kickback_res.category == "HIGH":
            hard_failures.append(kickback_res.message)
        elif kickback_res.category == "MEDIUM":
            warnings.append(kickback_res.message)

    overall_risk = "RED" if hard_failures else ("YELLOW" if warnings else "GREEN")

    return CAMCalculatorBundleResponse(
        tool_id=payload.tool_id, material_id=payload.material_id, tool_kind=payload.tool_kind,
        chipload=asdict(chipload_res) if chipload_res else None,
        heat=asdict(heat_res) if heat_res else None,
        deflection=asdict(deflection_res) if deflection_res else None,
        rim_speed=asdict(rim_speed_res) if rim_speed_res else None,
        kickback=asdict(kickback_res) if kickback_res else None,
        bite_per_tooth=asdict(bite_res) if bite_res else None,
        warnings=warnings, hard_failures=hard_failures, overall_risk=overall_risk,
    )


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


# ============================================================================
# CAM Cutting Endpoints
# ============================================================================

@router.post("/cam/evaluate", response_model=CAMCalculatorBundleResponse)
def cam_evaluate_cut(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """
    Evaluate a cut operation and return all calculator results.

    Supports both router bits and saw blades. Returns:
    - Chipload or bite-per-tooth
    - Heat risk assessment
    - Deflection risk (router bits)
    - Rim speed (saw blades)
    - Kickback risk (saw blades)
    - Overall risk level (GREEN/YELLOW/RED)
    """
    return evaluate_cut_operation(payload)


@router.post("/cam/evaluate-cut", response_model=CAMCalculatorBundleResponse)
def cam_evaluate_cut_alias(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Alias for /cam/evaluate - Calculator Spine API compatibility."""
    return evaluate_cut_operation(payload)


@router.get("/cam/health")
def cam_calculator_health():
    """Health check for CAM calculator service."""
    return {
        "status": "ok",
        "calculators": ["chipload", "heat_risk", "deflection", "rim_speed", "bite_per_tooth", "kickback_risk"],
        "tool_kinds": ["router_bit", "saw_blade"],
    }


# ============================================================================
# Math Endpoints
# ============================================================================

@router.post("/math/evaluate", response_model=MathEvaluateResponse)
async def math_evaluate_expression(request: MathEvaluateRequest):
    """Evaluate a mathematical expression."""
    calc = LTBScientificCalculator()
    result = calc.evaluate(request.expression)
    return MathEvaluateResponse(result=result, display=calc.display, error=calc.error)


@router.post("/math/fraction/convert", response_model=FractionResponse)
async def fraction_convert(request: FractionRequest):
    """Convert decimal to woodworker fraction."""
    calc = LTBFractionCalculator(precision=request.precision)
    result = calc.to_fraction(request.decimal)
    return FractionResponse(
        decimal=request.decimal, fraction=str(result),
        numerator=result.numerator, denominator=result.denominator, whole=result.whole
    )


@router.get("/math/fraction/parse/{text:path}")
async def fraction_parse(text: str):
    """Parse fraction string to decimal."""
    calc = LTBFractionCalculator()
    value = calc.parse_fraction(text)
    if calc.error:
        raise HTTPException(status_code=400, detail=calc.error)
    return {"input": text, "decimal": value, "fraction": calc.display_fraction}


@router.post("/math/tvm", response_model=TVMResponse)
async def math_tvm(request: TVMRequest):
    """Time Value of Money calculation."""
    calc = LTBFinancialCalculator()
    calc.tvm.begin_mode = request.begin_mode

    if request.n is not None: calc.n = request.n
    if request.i_y is not None: calc.i_y = request.i_y
    if request.pv is not None: calc.pv = request.pv
    if request.pmt is not None: calc.pmt = request.pmt
    if request.fv is not None: calc.fv = request.fv

    try:
        if request.solve_for == 'n': result = calc.solve_n()
        elif request.solve_for == 'i_y': result = calc.solve_rate()
        elif request.solve_for == 'pv': result = calc.solve_pv()
        elif request.solve_for == 'pmt': result = calc.solve_pmt()
        elif request.solve_for == 'fv': result = calc.solve_fv()
        else: raise HTTPException(400, f"Invalid solve_for: {request.solve_for}")
    except ValueError as e:
        raise HTTPException(400, str(e))

    return TVMResponse(result=result, variable=request.solve_for,
                       inputs={"n": calc.n, "i_y": calc.i_y, "pv": calc.pv, "pmt": calc.pmt, "fv": calc.fv})


# ============================================================================
# Luthier Endpoints
# ============================================================================

@router.post("/luthier/radius/from-3-points")
async def luthier_radius_from_3_points(request: RadiusFrom3PointsRequest):
    """Calculate radius from 3 points on a curve."""
    calc = LTBLuthierCalculator()
    radius = calc.radius_from_3_points(request.p1, request.p2, request.p3)
    return {"radius": radius, "unit": "same as input"}


@router.post("/luthier/radius/from-chord")
async def luthier_radius_from_chord(request: RadiusFromChordRequest):
    """Calculate radius from chord length and arc height."""
    calc = LTBLuthierCalculator()
    radius = calc.radius_from_chord(request.chord_length, request.height)
    return {"radius": radius, "unit": "same as input"}


@router.post("/luthier/radius/compound")
async def luthier_compound_radius(request: CompoundRadiusRequest):
    """Calculate compound radius at any fretboard position."""
    calc = LTBLuthierCalculator()
    radius = calc.compound_radius(request.nut_radius, request.saddle_radius,
                                  request.scale_length, request.position)
    return {"radius": radius, "position": request.position,
            "nut_radius": request.nut_radius, "saddle_radius": request.saddle_radius}


@router.post("/luthier/wedge/angle")
async def luthier_wedge_angle(request: WedgeAngleRequest):
    """Calculate wedge angle from dimensions."""
    calc = LTBLuthierCalculator()
    angle = calc.wedge_angle(request.length, request.thick_end, request.thin_end)
    tpf = calc.taper_per_foot(request.thick_end, request.thin_end, request.length)
    return {"angle_degrees": angle, "taper_per_foot": tpf}


@router.post("/luthier/board-feet")
async def luthier_board_feet(request: BoardFeetRequest):
    """Calculate board feet."""
    calc = LTBLuthierCalculator()
    bf = calc.board_feet(request.thickness, request.width, request.length, quarters=request.quarters)
    return {"board_feet": bf}


@router.get("/luthier/miter/{num_sides}")
async def luthier_miter_angle(num_sides: int):
    """Calculate miter angle for n-sided polygon."""
    calc = LTBLuthierCalculator()
    angle = calc.miter_angle(num_sides)
    return {"sides": num_sides, "miter_angle": angle}


@router.get("/luthier/dovetail/{ratio}")
async def luthier_dovetail_angle(ratio: str):
    """Calculate dovetail angle from ratio (e.g., '1:8')."""
    calc = LTBLuthierCalculator()
    angle = calc.dovetail_angle(ratio)
    return {"ratio": ratio, "angle_degrees": angle}


# ============================================================================
# Legacy Compatibility Endpoints
# ============================================================================

@router.post("/evaluate", response_model=CAMCalculatorBundleResponse)
def legacy_evaluate_cut(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Legacy endpoint - redirects to /cam/evaluate."""
    return evaluate_cut_operation(payload)


@router.post("/evaluate-cut", response_model=CAMCalculatorBundleResponse)
def legacy_evaluate_cut_alias(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Legacy endpoint - redirects to /cam/evaluate-cut."""
    return evaluate_cut_operation(payload)


@router.get("/health")
def legacy_health():
    """Legacy health endpoint - redirects to /cam/health."""
    return cam_calculator_health()
