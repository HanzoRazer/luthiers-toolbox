"""
Calculator API Routes - Luthier's ToolBox

Exposes the calculator suite via REST API.
Place this in: services/api/app/routers/calculator_router.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

# Adjust import path based on your repo structure
from ..ltb_calculators import (
    LTBBasicCalculator,
    LTBFractionCalculator,
    LTBScientificCalculator,
    LTBFinancialCalculator,
    LTBLuthierCalculator,
)

router = APIRouter(prefix="/api/calculators", tags=["calculators"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class EvaluateRequest(BaseModel):
    expression: str = Field(..., description="Math expression to evaluate")
    
class EvaluateResponse(BaseModel):
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


class RadiusFrom3PointsRequest(BaseModel):
    p1: Tuple[float, float] = Field(..., description="Point 1 (x, y)")
    p2: Tuple[float, float] = Field(..., description="Point 2 (x, y)")
    p3: Tuple[float, float] = Field(..., description="Point 3 (x, y)")

class RadiusResponse(BaseModel):
    radius: float
    unit: str = "same as input"


class RadiusFromChordRequest(BaseModel):
    chord_length: float = Field(..., description="Length of chord/straightedge")
    height: float = Field(..., description="Arc height at center (sagitta)")

class CompoundRadiusRequest(BaseModel):
    nut_radius: float
    saddle_radius: float
    scale_length: float
    position: float = Field(..., description="Distance from nut")

class FretPositionRequest(BaseModel):
    scale_length: float
    fret_number: int

class FretTableRequest(BaseModel):
    scale_length: float
    num_frets: int = Field(24, ge=1, le=36)

class FretPosition(BaseModel):
    fret_number: int
    distance_from_nut: float
    distance_from_previous: float
    remaining_to_bridge: float

class WedgeAngleRequest(BaseModel):
    length: float
    thick_end: float
    thin_end: float

class BoardFeetRequest(BaseModel):
    thickness: float
    width: float
    length: float
    quarters: bool = Field(False, description="Thickness in quarters (4/4, 8/4)")


# =============================================================================
# BASIC CALCULATOR ROUTES
# =============================================================================

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_expression(request: EvaluateRequest):
    """Evaluate a mathematical expression."""
    calc = LTBScientificCalculator()
    result = calc.evaluate(request.expression)
    
    return EvaluateResponse(
        result=result,
        display=calc.display,
        error=calc.error
    )


# =============================================================================
# FRACTION ROUTES
# =============================================================================

@router.post("/fraction/convert", response_model=FractionResponse)
async def convert_to_fraction(request: FractionRequest):
    """Convert decimal to woodworker fraction."""
    calc = LTBFractionCalculator(precision=request.precision)
    result = calc.to_fraction(request.decimal)
    
    return FractionResponse(
        decimal=request.decimal,
        fraction=str(result),
        numerator=result.numerator,
        denominator=result.denominator,
        whole=result.whole
    )


@router.get("/fraction/parse/{text:path}")
async def parse_fraction(text: str):
    """Parse fraction string to decimal."""
    calc = LTBFractionCalculator()
    value = calc.parse_fraction(text)
    
    if calc.error:
        raise HTTPException(status_code=400, detail=calc.error)
    
    return {
        "input": text,
        "decimal": value,
        "fraction": calc.display_fraction
    }


# =============================================================================
# FINANCIAL ROUTES (TVM)
# =============================================================================

@router.post("/tvm", response_model=TVMResponse)
async def calculate_tvm(request: TVMRequest):
    """Time Value of Money calculation."""
    calc = LTBFinancialCalculator()
    calc.tvm.begin_mode = request.begin_mode
    
    if request.n is not None:
        calc.n = request.n
    if request.i_y is not None:
        calc.i_y = request.i_y
    if request.pv is not None:
        calc.pv = request.pv
    if request.pmt is not None:
        calc.pmt = request.pmt
    if request.fv is not None:
        calc.fv = request.fv
    
    try:
        if request.solve_for == 'n':
            result = calc.solve_n()
        elif request.solve_for == 'i_y':
            result = calc.solve_rate()
        elif request.solve_for == 'pv':
            result = calc.solve_pv()
        elif request.solve_for == 'pmt':
            result = calc.solve_pmt()
        elif request.solve_for == 'fv':
            result = calc.solve_fv()
        else:
            raise HTTPException(400, f"Invalid solve_for: {request.solve_for}")
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    return TVMResponse(
        result=result,
        variable=request.solve_for,
        inputs={
            "n": calc.n,
            "i_y": calc.i_y,
            "pv": calc.pv,
            "pmt": calc.pmt,
            "fv": calc.fv,
        }
    )


# =============================================================================
# LUTHIER ROUTES
# =============================================================================

@router.post("/radius/from-3-points", response_model=RadiusResponse)
async def radius_from_3_points(request: RadiusFrom3PointsRequest):
    """Calculate radius from 3 points on a curve."""
    calc = LTBLuthierCalculator()
    radius = calc.radius_from_3_points(request.p1, request.p2, request.p3)
    return RadiusResponse(radius=radius)


@router.post("/radius/from-chord", response_model=RadiusResponse)
async def radius_from_chord(request: RadiusFromChordRequest):
    """Calculate radius from chord length and arc height."""
    calc = LTBLuthierCalculator()
    radius = calc.radius_from_chord(request.chord_length, request.height)
    return RadiusResponse(radius=radius)


@router.post("/radius/compound")
async def compound_radius(request: CompoundRadiusRequest):
    """Calculate compound radius at any fretboard position."""
    calc = LTBLuthierCalculator()
    radius = calc.compound_radius(
        request.nut_radius,
        request.saddle_radius,
        request.scale_length,
        request.position
    )
    return {
        "radius": radius,
        "position": request.position,
        "nut_radius": request.nut_radius,
        "saddle_radius": request.saddle_radius
    }


@router.post("/fret/position")
async def fret_position(request: FretPositionRequest):
    """Calculate single fret position."""
    calc = LTBLuthierCalculator()
    position = calc.fret_position(request.scale_length, request.fret_number)
    spacing = calc.fret_spacing(request.scale_length, request.fret_number)
    return {
        "fret": request.fret_number,
        "distance_from_nut": position,
        "spacing_from_previous": spacing,
        "scale_length": request.scale_length
    }


@router.post("/fret/table", response_model=List[FretPosition])
async def fret_table(request: FretTableRequest):
    """Generate complete fret position table."""
    calc = LTBLuthierCalculator()
    table = calc.fret_table(request.scale_length, request.num_frets)
    return [
        FretPosition(
            fret_number=f.fret_number,
            distance_from_nut=f.distance_from_nut,
            distance_from_previous=f.distance_from_previous,
            remaining_to_bridge=f.remaining_to_bridge
        )
        for f in table
    ]


@router.post("/wedge/angle")
async def wedge_angle(request: WedgeAngleRequest):
    """Calculate wedge angle from dimensions."""
    calc = LTBLuthierCalculator()
    angle = calc.wedge_angle(request.length, request.thick_end, request.thin_end)
    tpf = calc.taper_per_foot(request.thick_end, request.thin_end, request.length)
    return {
        "angle_degrees": angle,
        "taper_per_foot": tpf
    }


@router.post("/board-feet")
async def board_feet(request: BoardFeetRequest):
    """Calculate board feet."""
    calc = LTBLuthierCalculator()
    bf = calc.board_feet(
        request.thickness,
        request.width,
        request.length,
        quarters=request.quarters
    )
    return {"board_feet": bf}


@router.get("/miter/{num_sides}")
async def miter_angle(num_sides: int):
    """Calculate miter angle for n-sided polygon."""
    calc = LTBLuthierCalculator()
    angle = calc.miter_angle(num_sides)
    return {"sides": num_sides, "miter_angle": angle}


@router.get("/dovetail/{ratio}")
async def dovetail_angle(ratio: str):
    """Calculate dovetail angle from ratio (e.g., '1:8')."""
    calc = LTBLuthierCalculator()
    angle = calc.dovetail_angle(ratio)
    return {"ratio": ratio, "angle_degrees": angle}
