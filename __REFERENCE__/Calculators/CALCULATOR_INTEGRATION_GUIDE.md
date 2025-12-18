# Calculator Integration Guide - Luthier's ToolBox

## Current Problem

The original calculators got tangled with CAM geometry code during "vibe coding."
These new calculators are **pure input→output** with clean inheritance.

## New Calculator Stack

```
calculators/
├── __init__.py
├── basic_calculator.py         # +−×÷ √ % ±
├── fraction_calculator.py      # Woodworker fractions (1/8, 1/16, 1/32)
├── scientific_calculator.py    # e^x, ln, log, trig (e^1 = 2.7182818285 ✓)
├── financial_calculator.py     # TVM, amortization, depreciation
└── luthier_calculator.py       # Radius from 3 pts, wedge, frets, woodworking
```

**Inheritance chain:**
```
BasicCalculator
    └── FractionCalculator
            └── ScientificCalculator
                    ├── FinancialCalculator
                    └── LuthierCalculator
```

## Step 1: Create Directory Structure

```bash
cd /path/to/luthiers-toolbox/services/api/app

# Create calculators module
mkdir -p calculators

# Copy the new calculator files
cp /path/to/downloads/basic_calculator.py calculators/
cp /path/to/downloads/fraction_calculator.py calculators/
cp /path/to/downloads/scientific_calculator.py calculators/
cp /path/to/downloads/financial_calculator.py calculators/
cp /path/to/downloads/luthier_calculator.py calculators/
```

## Step 2: Create __init__.py

```python
# services/api/app/calculators/__init__.py
"""
Luthier's ToolBox Calculator Suite

Clean, tested calculators with proper separation of concerns.
These are pure calculators (input → output), NOT CAM geometry.

For CAM geometry (toolpaths, G-code), see:
    - generators/body_generator.py
    - generators/gcode_generator.py
"""

from .basic_calculator import BasicCalculator
from .fraction_calculator import FractionCalculator
from .scientific_calculator import ScientificCalculator
from .financial_calculator import FinancialCalculator
from .luthier_calculator import LuthierCalculator

__all__ = [
    'BasicCalculator',
    'FractionCalculator', 
    'ScientificCalculator',
    'FinancialCalculator',
    'LuthierCalculator',
]
```

## Step 3: Create FastAPI Router

```python
# services/api/app/routers/calculator_router.py
"""
Calculator API Routes

Exposes the calculator suite via REST API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from ..calculators import (
    BasicCalculator,
    FractionCalculator,
    ScientificCalculator,
    FinancialCalculator,
    LuthierCalculator,
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
    """Calculate radius from 3 points on a curve."""
    p1: Tuple[float, float] = Field(..., description="Point 1 (x, y)")
    p2: Tuple[float, float] = Field(..., description="Point 2 (x, y)")
    p3: Tuple[float, float] = Field(..., description="Point 3 (x, y)")

class RadiusResponse(BaseModel):
    radius: float
    unit: str = "same as input"


class RadiusFromChordRequest(BaseModel):
    """Calculate radius from chord and sagitta (arc height)."""
    chord_length: float = Field(..., description="Length of chord/straightedge")
    height: float = Field(..., description="Arc height at center (sagitta)")

class CompoundRadiusRequest(BaseModel):
    """Calculate compound radius at position."""
    nut_radius: float
    saddle_radius: float
    scale_length: float
    position: float = Field(..., description="Distance from nut")

class FretPositionRequest(BaseModel):
    """Calculate fret position."""
    scale_length: float
    fret_number: int

class FretTableRequest(BaseModel):
    """Generate fret position table."""
    scale_length: float
    num_frets: int = Field(24, ge=1, le=36)

class FretPosition(BaseModel):
    fret_number: int
    distance_from_nut: float
    distance_from_previous: float
    remaining_to_bridge: float

class WedgeAngleRequest(BaseModel):
    """Calculate wedge angle."""
    length: float
    thick_end: float
    thin_end: float

class BoardFeetRequest(BaseModel):
    """Calculate board feet."""
    thickness: float
    width: float
    length: float
    quarters: bool = Field(False, description="Thickness in quarters (4/4, 8/4)")


# =============================================================================
# BASIC CALCULATOR ROUTES
# =============================================================================

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_expression(request: EvaluateRequest):
    """
    Evaluate a mathematical expression.
    
    Examples:
        "5 + 3 * 2" → 11
        "(5 + 3) * 2" → 16
        "sqrt(144)" → 12
        "e^1" → 2.718...
    """
    calc = ScientificCalculator()
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
    """
    Convert decimal to woodworker fraction.
    
    Example: 0.875 → 7/8
    """
    calc = FractionCalculator(precision=request.precision)
    result = calc.to_fraction(request.decimal)
    
    return FractionResponse(
        decimal=request.decimal,
        fraction=str(result),
        numerator=result.numerator,
        denominator=result.denominator,
        whole=result.whole
    )


@router.get("/fraction/parse/{text}")
async def parse_fraction(text: str):
    """
    Parse fraction string to decimal.
    
    Examples:
        "3/4" → 0.75
        "2-3/8" → 2.375
        "4'6-1/2\"" → 54.5
    """
    calc = FractionCalculator()
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
    """
    Time Value of Money calculation.
    
    Set 4 of 5 variables (n, i_y, pv, pmt, fv) and solve for the 5th.
    
    Example - Mortgage payment:
        n=360, i_y=0.5417, pv=200000, fv=0, solve_for="pmt"
        → -1264.14/month
    """
    calc = FinancialCalculator()
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
    """
    Calculate radius from 3 points on a curve.
    
    Classic luthier measurement for archtops, radius gauges, etc.
    """
    calc = LuthierCalculator()
    radius = calc.radius_from_3_points(request.p1, request.p2, request.p3)
    
    return RadiusResponse(radius=radius)


@router.post("/radius/from-chord", response_model=RadiusResponse)
async def radius_from_chord(request: RadiusFromChordRequest):
    """
    Calculate radius from chord length and arc height.
    
    Example: Lay straightedge across fretboard, measure gap at center.
    """
    calc = LuthierCalculator()
    radius = calc.radius_from_chord(request.chord_length, request.height)
    
    return RadiusResponse(radius=radius)


@router.post("/radius/compound")
async def compound_radius(request: CompoundRadiusRequest):
    """
    Calculate compound radius at any fretboard position.
    """
    calc = LuthierCalculator()
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
    """
    Calculate single fret position.
    """
    calc = LuthierCalculator()
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
    """
    Generate complete fret position table.
    """
    calc = LuthierCalculator()
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
    """
    Calculate wedge angle from dimensions.
    """
    calc = LuthierCalculator()
    angle = calc.wedge_angle(request.length, request.thick_end, request.thin_end)
    tpf = calc.taper_per_foot(request.thick_end, request.thin_end, request.length)
    
    return {
        "angle_degrees": angle,
        "taper_per_foot": tpf
    }


@router.post("/board-feet")
async def board_feet(request: BoardFeetRequest):
    """
    Calculate board feet.
    """
    calc = LuthierCalculator()
    bf = calc.board_feet(
        request.thickness,
        request.width,
        request.length,
        quarters=request.quarters
    )
    
    return {"board_feet": bf}


@router.get("/miter/{num_sides}")
async def miter_angle(num_sides: int):
    """
    Calculate miter angle for n-sided polygon.
    """
    calc = LuthierCalculator()
    angle = calc.miter_angle(num_sides)
    
    return {
        "sides": num_sides,
        "miter_angle": angle
    }


@router.get("/dovetail/{ratio}")
async def dovetail_angle(ratio: str):
    """
    Calculate dovetail angle from ratio (e.g., "1:8").
    """
    calc = LuthierCalculator()
    angle = calc.dovetail_angle(ratio)
    
    return {
        "ratio": ratio,
        "angle_degrees": angle
    }
```

## Step 4: Register Router in main.py

```python
# services/api/app/main.py

from fastapi import FastAPI
from .routers import calculator_router  # Add this import

app = FastAPI(
    title="Luthier's ToolBox API",
    description="Guitar building tools and calculators",
    version="1.0.0"
)

# Register calculator routes
app.include_router(calculator_router.router)

# ... other routers
```

## Step 5: Test the Integration

```bash
# Start the server
cd services/api
uvicorn app.main:app --reload --port 8000

# Test basic evaluation
curl -X POST http://localhost:8000/api/calculators/evaluate \
  -H "Content-Type: application/json" \
  -d '{"expression": "e^1"}'
# → {"result": 2.718281828459045, "display": "2.7182818285", "error": null}

# Test fraction conversion
curl -X POST http://localhost:8000/api/calculators/fraction/convert \
  -H "Content-Type: application/json" \
  -d '{"decimal": 0.875, "precision": 16}'
# → {"decimal": 0.875, "fraction": "7/8", "numerator": 7, "denominator": 8, "whole": 0}

# Test radius from 3 points
curl -X POST http://localhost:8000/api/calculators/radius/from-3-points \
  -H "Content-Type: application/json" \
  -d '{"p1": [0, 0], "p2": [6, 0.5], "p3": [12, 0]}'
# → {"radius": 36.25, "unit": "same as input"}

# Test TVM mortgage payment
curl -X POST http://localhost:8000/api/calculators/tvm \
  -H "Content-Type: application/json" \
  -d '{"n": 360, "i_y": 0.5417, "pv": 200000, "fv": 0, "solve_for": "pmt"}'
# → {"result": -1264.14, "variable": "pmt", ...}

# Test fret table
curl -X POST http://localhost:8000/api/calculators/fret/table \
  -H "Content-Type: application/json" \
  -d '{"scale_length": 25.5, "num_frets": 12}'
```

## Directory Structure After Integration

```
luthiers-toolbox/
├── services/
│   └── api/
│       └── app/
│           ├── main.py                      # FastAPI app
│           ├── calculators/                 # NEW - Calculator suite
│           │   ├── __init__.py
│           │   ├── basic_calculator.py
│           │   ├── fraction_calculator.py
│           │   ├── scientific_calculator.py
│           │   ├── financial_calculator.py
│           │   └── luthier_calculator.py
│           ├── routers/
│           │   ├── calculator_router.py     # NEW - Calculator API
│           │   ├── cam_fret_slots_export_router.py
│           │   ├── context_router.py
│           │   └── health_router.py
│           ├── generators/                  # CAM/G-code (separate from calculators!)
│           │   ├── body_generator.py
│           │   └── gcode_generator.py
│           └── stores/
│               └── ...
```

## Key Separation

**Calculators** (pure math, input → output):
- `luthier_calculator.radius_from_3_points()` → returns a number
- `luthier_calculator.fret_position()` → returns a number
- `financial_calculator.solve_pmt()` → returns a number

**Generators** (CAM, creates toolpaths):
- `body_generator.generate_perimeter()` → creates G-code
- Uses calculators internally for math, but produces toolpath output

This separation prevents the "spaghetti" problem where calculator logic
gets tangled with CAM geometry code.
