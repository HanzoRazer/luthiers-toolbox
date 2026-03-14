"""Engineering Estimator Router — Endpoints for parametric cost estimation.

Provides:
- POST /parametric - Create parametric estimate
- POST /quote - Generate customer quote
- GET /factors - List complexity factors
- GET /wbs/{instrument_type} - Get WBS template
- GET /learning-curve - Preview learning curve

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .estimator import (
    EngineeringEstimatorService,
    EstimateRequest,
    EstimateResult,
)
from .estimator.schemas import (
    InstrumentType as EstimatorInstrumentType,
    QuoteRequest,
    QuoteResult,
)
from .estimator.work_breakdown import get_wbs_template, get_wbs_by_phase

router = APIRouter(tags=["Estimator", "Business"])

# Service (singleton instance)
estimator_service = EngineeringEstimatorService()


@router.post("/parametric", response_model=EstimateResult, summary="Create parametric estimate")
async def create_parametric_estimate(request: EstimateRequest) -> EstimateResult:
    """
    Create a parametric cost estimate for an instrument build.

    Uses engineering estimation techniques:
    - Work Breakdown Structure (WBS) templates
    - Complexity factors for design choices
    - Learning curve adjustments for batch production
    - Material yield/waste factors

    The estimate includes labor hours, material costs, and
    recommended pricing based on experience level and design complexity.
    """
    return estimator_service.estimate(request)


@router.post("/quote", response_model=QuoteResult, summary="Generate customer quote")
async def generate_customer_quote(request: QuoteRequest) -> QuoteResult:
    """
    Generate a customer-facing quote from an estimate.

    Wraps the parametric estimate with:
    - Professional formatting
    - Margin calculations
    - Payment terms
    - Validity period
    """
    return estimator_service.generate_quote(request)


@router.get("/factors", summary="List complexity factors")
async def list_complexity_factors():
    """
    List all complexity factors and their multipliers.

    Useful for understanding how design choices affect build time:
    - Body complexity (cutaway, carved top, etc.)
    - Binding complexity (none, simple, multi-ply, etc.)
    - Neck complexity (bolt-on, set-neck, etc.)
    - Fretboard inlay (dots, blocks, custom, etc.)
    - Finish type (oil, nitro, french polish, etc.)
    - Rosette complexity (simple, multi-ring, inlaid, etc.)
    """
    return estimator_service.get_factors_summary()


@router.get("/wbs/{instrument_type}", summary="Get WBS template")
async def get_wbs_for_instrument(instrument_type: EstimatorInstrumentType):
    """
    Get the Work Breakdown Structure template for an instrument type.

    Returns all tasks with baseline hours, organized by phase:
    - Design & Planning
    - Body Construction
    - Neck Construction
    - Assembly
    - Finishing
    - Setup & Quality Control
    """
    template = get_wbs_template(instrument_type)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"No WBS template for instrument type: {instrument_type.value}",
        )

    by_phase = get_wbs_by_phase(instrument_type)
    total_hours = sum(t.base_hours for t in template)

    return {
        "instrument_type": instrument_type.value,
        "total_baseline_hours": round(total_hours, 1),
        "task_count": len(template),
        "phases": {
            phase: [
                {
                    "task_id": t.task_id,
                    "name": t.task_name,
                    "base_hours": t.base_hours,
                    "complexity_group": t.complexity_group,
                }
                for t in tasks
            ]
            for phase, tasks in by_phase.items()
        },
    }


@router.get("/learning-curve", summary="Preview learning curve")
async def preview_learning_curve(
    first_unit_hours: float = Query(..., ge=1, description="Hours for first unit"),
    quantity: int = Query(..., ge=1, le=100, description="Batch size"),
    learning_rate: float = Query(0.85, ge=0.7, le=0.95, description="Learning rate"),
    hourly_rate: float = Query(45.0, ge=0, description="Labor rate for cost calc"),
):
    """
    Preview learning curve effect for batch production.

    Shows how build time decreases with repetition:
    - Unit-by-unit time projection
    - Cumulative hours and cost
    - Efficiency gain vs no learning

    Learning rate of 0.85 means each doubling of quantity
    reduces per-unit time by 15%.
    """
    from .estimator.learning_curve import generate_learning_curve_projection

    return generate_learning_curve_projection(
        first_unit_hours=first_unit_hours,
        quantity=quantity,
        learning_rate=learning_rate,
        hourly_rate=hourly_rate,
    )


__all__ = ["router", "estimator_service"]
