"""Cash Flow Router — Endpoints for cash flow projections.

Provides:
- POST /project - Create cash flow projection
- POST /startup - Create startup projection
- POST /required-capital - Calculate required capital

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from .schemas import CashFlowProjection
from .cashflow_service import CashFlowService

router = APIRouter(tags=["Cash Flow", "Business"])

# Service (singleton instance)
cashflow_service = CashFlowService()


@router.post("/project", response_model=CashFlowProjection, summary="Create cash flow projection")
async def create_cash_flow_projection(
    projection_name: str = Query(..., min_length=1),
    months: int = Query(12, ge=1, le=60),
    starting_cash: float = Query(0, ge=0),
    monthly_revenue: float = Query(0, ge=0),
    monthly_materials: float = Query(0, ge=0),
    monthly_labor: float = Query(0, ge=0),
    monthly_overhead: float = Query(0, ge=0),
    revenue_growth_pct: float = Query(0, ge=-50, le=100),
) -> CashFlowProjection:
    """
    Create a cash flow projection.

    Projects monthly cash flows and identifies potential shortfalls.
    """
    return cashflow_service.create_projection(
        projection_name=projection_name,
        months=months,
        starting_cash=starting_cash,
        monthly_revenue=monthly_revenue,
        monthly_materials=monthly_materials,
        monthly_labor=monthly_labor,
        monthly_overhead=monthly_overhead,
        revenue_growth_pct=revenue_growth_pct,
    )


@router.post("/startup", response_model=CashFlowProjection, summary="Create startup projection")
async def create_startup_projection(
    projection_name: str = Query(..., min_length=1),
    starting_cash: float = Query(..., ge=0),
    monthly_overhead: float = Query(..., ge=0),
    target_monthly_revenue: float = Query(..., ge=0),
    months_to_ramp: int = Query(6, ge=1, le=24),
    total_months: int = Query(12, ge=1, le=60),
    cogs_pct: float = Query(40, ge=0, le=100),
    owner_salary: float = Query(0, ge=0),
) -> CashFlowProjection:
    """
    Create a startup cash flow projection with revenue ramp-up.

    Models the journey from $0 revenue to target, showing when
    you'll break even and if you have enough capital.
    """
    return cashflow_service.create_ramp_up_projection(
        projection_name=projection_name,
        starting_cash=starting_cash,
        monthly_overhead=monthly_overhead,
        target_monthly_revenue=target_monthly_revenue,
        months_to_ramp=months_to_ramp,
        total_months=total_months,
        cogs_pct=cogs_pct,
        owner_salary=owner_salary,
    )


@router.post("/required-capital", summary="Calculate required capital")
async def calculate_required_capital(
    monthly_overhead: float = Query(..., ge=0),
    months_to_revenue: int = Query(3, ge=0, le=24),
    target_monthly_revenue: float = Query(..., ge=0),
    cogs_pct: float = Query(40, ge=0, le=100),
    buffer_months: int = Query(3, ge=0, le=12),
):
    """
    Calculate how much starting capital you need.

    Accounts for:
    - Pre-revenue burn
    - Ramp-up shortfall
    - Emergency buffer
    - Working capital for materials
    """
    return cashflow_service.calculate_required_capital(
        monthly_overhead=monthly_overhead,
        months_to_revenue=months_to_revenue,
        target_monthly_revenue=target_monthly_revenue,
        cogs_pct=cogs_pct,
        buffer_months=buffer_months,
    )


__all__ = ["router", "cashflow_service"]
