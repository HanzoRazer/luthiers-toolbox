"""Break-Even Router — Endpoints for break-even analysis.

Provides:
- POST /calculate - Calculate break-even point
- POST /target-profit - Calculate target profit volume
- POST /sensitivity - Run sensitivity analysis

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from .schemas import BreakEvenAnalysis
from .breakeven_service import BreakEvenService

router = APIRouter(tags=["Break-Even", "Business"])

# Service (singleton instance)
breakeven_service = BreakEvenService()


@router.post("/calculate", response_model=BreakEvenAnalysis, summary="Calculate break-even point")
async def calculate_break_even(
    fixed_costs_monthly: float = Query(..., ge=0),
    variable_cost_per_unit: float = Query(..., ge=0),
    selling_price_per_unit: float = Query(..., ge=0),
    analysis_name: str = "Break-Even Analysis",
) -> BreakEvenAnalysis:
    """
    Calculate break-even point.

    Break-even units = Fixed Costs / (Price - Variable Cost)
    """
    return breakeven_service.calculate_break_even(
        fixed_costs_monthly=fixed_costs_monthly,
        variable_cost_per_unit=variable_cost_per_unit,
        selling_price_per_unit=selling_price_per_unit,
        analysis_name=analysis_name,
    )


@router.post("/target-profit", summary="Calculate target profit volume")
async def calculate_target_profit_volume(
    fixed_costs: float = Query(..., ge=0),
    variable_cost: float = Query(..., ge=0),
    price: float = Query(..., ge=0),
    target_monthly_profit: float = Query(..., ge=0),
):
    """Calculate units needed to achieve a target monthly profit."""
    return breakeven_service.find_target_profit_volume(
        fixed_costs=fixed_costs,
        variable_cost=variable_cost,
        price=price,
        target_monthly_profit=target_monthly_profit,
    )


@router.post("/sensitivity", summary="Run sensitivity analysis")
async def run_sensitivity_analysis(
    fixed_costs: float = Query(..., ge=0),
    variable_cost: float = Query(..., ge=0),
    price: float = Query(..., ge=0),
):
    """
    Run sensitivity analysis on break-even.

    Shows how break-even changes as price, costs, and overhead vary.
    """
    return breakeven_service.sensitivity_analysis(
        base_fixed_costs=fixed_costs,
        base_variable_cost=variable_cost,
        base_price=price,
    )


__all__ = ["router", "breakeven_service"]
