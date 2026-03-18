"""
Bridge Saddle Compensation Router.

Endpoints for calculating and adjusting bridge saddle compensation.

Two modes:
  - POST /api/instrument/bridge/compensation - Design mode (estimate from specs)
  - POST /api/instrument/bridge/setup - Setup mode (adjust from measurements)
"""
from fastapi import APIRouter

from app.calculators.saddle_compensation import (
    DesignCalculatorInput,
    DesignCalculatorResult,
    SetupCalculatorInput,
    SetupCalculatorResult,
    build_design_report,
    build_setup_result,
)

router = APIRouter(
    prefix="/api/instrument/bridge",
    tags=["instrument-bridge"],
)


@router.post(
    "/compensation",
    response_model=DesignCalculatorResult,
    summary="Calculate saddle compensation (Design Mode)",
    description="""
    Estimate per-string bridge saddle compensation from physical parameters.

    **Input:**
    - Scale length (mm)
    - Action at 12th fret (treble and bass)
    - String specifications (gauge, tension, wound status, position)

    **Output:**
    - Per-string compensation estimates
    - Straight saddle fit (slope, angle, R-squared)
    - Crown residuals (deviation from straight line)
    - Recommendation for saddle design

    **Semi-empirical model:**
    ```
    c_i = 0.45 + 0.55×gauge_mm + 0.18×action^1.7
        + 0.25×(scale/647.7) + 7.5/tension_lb
        + 0.55 (if wound)
    ```
    """,
)
def calculate_compensation(inp: DesignCalculatorInput) -> DesignCalculatorResult:
    """
    Calculate saddle compensation from design parameters.

    Estimates compensation for each string based on physical properties,
    fits a straight saddle line, and computes crown deviations.
    """
    return build_design_report(inp)


@router.post(
    "/setup",
    response_model=SetupCalculatorResult,
    summary="Calculate saddle adjustments (Setup Mode)",
    description="""
    Compute saddle adjustments from measured intonation errors.

    **Input:**
    - Scale length (mm)
    - Per-string measurements:
      - Current compensation position
      - Measured cents error (positive = sharp)

    **Output:**
    - Per-string adjustment (delta_L in mm)
    - New compensation positions
    - Average and maximum adjustments
    - Recommendation

    **Formula:**
    ```
    delta_L = scale_length × (2^(cents/1200) - 1)
    ```

    - Positive cents (sharp) → positive delta_L (move saddle back)
    - Negative cents (flat) → negative delta_L (move saddle forward)
    """,
)
def calculate_setup_adjustments(inp: SetupCalculatorInput) -> SetupCalculatorResult:
    """
    Calculate saddle adjustments from measured cents errors.

    Converts cents error to physical saddle adjustment using
    the standard pitch-to-length relationship.
    """
    return build_setup_result(inp)
