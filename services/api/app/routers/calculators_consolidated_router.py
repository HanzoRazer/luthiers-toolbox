"""
Consolidated Calculators Router - Math, CAM, and Luthier calculations.

Endpoints:
  CAM: /cam/evaluate, /cam/evaluate-cut, /cam/health
  Math: /math/evaluate, /math/fraction/convert, /math/fraction/parse, /math/tvm
  Luthier: radius, wedge, board-feet, miter, dovetail calculations
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..ltb_calculators import (
    LTBFractionCalculator, LTBScientificCalculator,
    LTBFinancialCalculator, LTBLuthierCalculator,
)
from ..calculators.cam_cutting_evaluator import evaluate_cut_operation
from ..schemas.calculators_schemas import (
    CutOperationPayload, CAMCalculatorBundleResponse,
    MathEvaluateRequest, MathEvaluateResponse,
    FractionRequest, FractionResponse, TVMRequest, TVMResponse,
    RadiusFrom3PointsRequest, RadiusFromChordRequest,
    CompoundRadiusRequest, WedgeAngleRequest, BoardFeetRequest,
)

router = APIRouter(tags=["calculators"])

# CAM Cutting Endpoints
@router.post("/cam/evaluate", response_model=CAMCalculatorBundleResponse)
def cam_evaluate_cut(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Evaluate cut operation - returns chipload, heat, deflection, risk levels."""
    result = evaluate_cut_operation(
        tool_id=payload.tool_id, material_id=payload.material_id,
        tool_kind=payload.tool_kind, feed_mm_min=payload.feed_mm_min,
        rpm=payload.rpm, depth_of_cut_mm=payload.depth_of_cut_mm,
        width_of_cut_mm=payload.width_of_cut_mm,
        tool_diameter_mm=payload.tool_diameter_mm or 6.0,
        flute_count=payload.flute_count or 2,
    )
    return CAMCalculatorBundleResponse(**result)

@router.post("/cam/evaluate-cut", response_model=CAMCalculatorBundleResponse)
def cam_evaluate_cut_alias(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    """Alias for /cam/evaluate."""
    return cam_evaluate_cut(payload)

@router.get("/cam/health")
def cam_calculator_health():
    """Health check for CAM calculator service."""
    return {"status": "ok", "calculators": ["chipload", "heat_risk", "deflection", "rim_speed", "bite_per_tooth", "kickback_risk"], "tool_kinds": ["router_bit", "saw_blade"]}

# Math Endpoints
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
    return FractionResponse(decimal=request.decimal, fraction=str(result),
                            numerator=result.numerator, denominator=result.denominator, whole=result.whole)

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
        solvers = {'n': calc.solve_n, 'i_y': calc.solve_rate, 'pv': calc.solve_pv, 'pmt': calc.solve_pmt, 'fv': calc.solve_fv}
        if request.solve_for not in solvers:
            raise HTTPException(400, f"Invalid solve_for: {request.solve_for}")
        result = solvers[request.solve_for]()
    except ValueError as e:
        raise HTTPException(400, str(e))
    return TVMResponse(result=result, variable=request.solve_for,
                       inputs={"n": calc.n, "i_y": calc.i_y, "pv": calc.pv, "pmt": calc.pmt, "fv": calc.fv})

# Luthier Endpoints
@router.post("/luthier/radius/from-3-points")
async def luthier_radius_from_3_points(request: RadiusFrom3PointsRequest):
    """Calculate radius from 3 points on a curve."""
    calc = LTBLuthierCalculator()
    return {"radius": calc.radius_from_3_points(request.p1, request.p2, request.p3), "unit": "same as input"}

@router.post("/luthier/radius/from-chord")
async def luthier_radius_from_chord(request: RadiusFromChordRequest):
    """Calculate radius from chord length and arc height."""
    calc = LTBLuthierCalculator()
    return {"radius": calc.radius_from_chord(request.chord_length, request.height), "unit": "same as input"}

@router.post("/luthier/radius/compound")
async def luthier_compound_radius(request: CompoundRadiusRequest):
    """Calculate compound radius at any fretboard position."""
    calc = LTBLuthierCalculator()
    return {"radius": calc.compound_radius(request.nut_radius, request.saddle_radius, request.scale_length, request.position),
            "position": request.position, "nut_radius": request.nut_radius, "saddle_radius": request.saddle_radius}

@router.post("/luthier/wedge/angle")
async def luthier_wedge_angle(request: WedgeAngleRequest):
    """Calculate wedge angle from dimensions."""
    calc = LTBLuthierCalculator()
    return {"angle_degrees": calc.wedge_angle(request.length, request.thick_end, request.thin_end),
            "taper_per_foot": calc.taper_per_foot(request.thick_end, request.thin_end, request.length)}

@router.post("/luthier/board-feet")
async def luthier_board_feet(request: BoardFeetRequest):
    """Calculate board feet."""
    calc = LTBLuthierCalculator()
    return {"board_feet": calc.board_feet(request.thickness, request.width, request.length, quarters=request.quarters)}

@router.get("/luthier/miter/{num_sides}")
async def luthier_miter_angle(num_sides: int):
    """Calculate miter angle for n-sided polygon."""
    return {"sides": num_sides, "miter_angle": LTBLuthierCalculator().miter_angle(num_sides)}

@router.get("/luthier/dovetail/{ratio}")
async def luthier_dovetail_angle(ratio: str):
    """Calculate dovetail angle from ratio (e.g., '1:8')."""
    return {"ratio": ratio, "angle_degrees": LTBLuthierCalculator().dovetail_angle(ratio)}

# Legacy Compatibility Endpoints
@router.post("/evaluate", response_model=CAMCalculatorBundleResponse)
def legacy_evaluate_cut(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    return cam_evaluate_cut(payload)

@router.post("/evaluate-cut", response_model=CAMCalculatorBundleResponse)
def legacy_evaluate_cut_alias(payload: CutOperationPayload) -> CAMCalculatorBundleResponse:
    return cam_evaluate_cut(payload)

