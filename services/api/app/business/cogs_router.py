"""COGS (Cost of Goods Sold) Router — Endpoints for cost calculation.

Provides:
- POST /calculate - Calculate COGS from BOM
- GET /labor-rates - Get labor rates
- PUT /labor-rates/{category} - Update labor rate
- GET /overhead - Get overhead summary

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from .schemas import (
    BillOfMaterials,
    COGSBreakdown,
    LaborCategory,
)
from .cogs_service import COGSService

router = APIRouter(tags=["COGS", "Business"])

# Service (singleton instance)
cogs_service = COGSService()


@router.post("/calculate", response_model=COGSBreakdown, summary="Calculate COGS")
async def calculate_cogs(
    bom: BillOfMaterials,
    include_overhead: bool = True,
) -> COGSBreakdown:
    """
    Calculate Cost of Goods Sold from a BOM.

    COGS = Materials + Labor + Allocated Overhead
    """
    return cogs_service.calculate_cogs(
        bom=bom,
        include_overhead=include_overhead,
    )


@router.get("/labor-rates", summary="Get labor rates")
async def get_labor_rates():
    """Get current labor rates by category."""
    return {
        "rates": [
            {"category": cat.value, "hourly_rate": rate}
            for cat, rate in cogs_service.labor_rates.items()
        ]
    }


@router.put("/labor-rates/{category}", summary="Update labor rate")
async def update_labor_rate(
    category: LaborCategory,
    hourly_rate: float = Query(..., ge=0),
):
    """Update the hourly rate for a labor category."""
    cogs_service.update_labor_rate(category, hourly_rate)
    return {"status": "updated", "category": category.value, "hourly_rate": hourly_rate}


@router.get("/overhead", summary="Get overhead summary")
async def get_overhead_summary():
    """Get current overhead configuration."""
    return cogs_service.get_overhead_summary()


__all__ = ["router", "cogs_service"]
