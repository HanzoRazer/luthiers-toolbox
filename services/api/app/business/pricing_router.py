"""Pricing Router — Endpoints for pricing strategy and competitor analysis.

Provides:
- POST /calculate - Calculate pricing strategy
- GET /competitors - Get competitor landscape
- POST /competitors - Add competitor

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from .schemas import (
    PricingStrategy,
    CompetitorPrice,
)
from .pricing_service import PricingService

router = APIRouter(tags=["Pricing", "Business"])

# Service (singleton instance)
pricing_service = PricingService()


@router.post("/calculate", response_model=PricingStrategy, summary="Calculate pricing strategy")
async def calculate_pricing(
    cogs: float = Query(..., ge=0, description="Cost of Goods Sold"),
    instrument_name: str = Query(..., min_length=1),
    instrument_type: str = "acoustic_dreadnought",
    target_tier: str = "custom",
    markup_pct: Optional[float] = None,
) -> PricingStrategy:
    """
    Calculate pricing strategy for an instrument.

    Returns cost-plus, market-based, and value-based pricing
    with a recommended price.
    """
    return pricing_service.calculate_pricing(
        cogs=cogs,
        instrument_name=instrument_name,
        instrument_type=instrument_type,
        target_tier=target_tier,
        custom_markup_pct=markup_pct,
    )


@router.get("/competitors", summary="Get competitor landscape")
async def get_competitor_summary(
    instrument_type: Optional[str] = None,
):
    """Get summary of competitor pricing landscape."""
    return pricing_service.get_competitor_summary(instrument_type)


@router.post("/competitors", response_model=CompetitorPrice, summary="Add competitor")
async def add_competitor(competitor: CompetitorPrice) -> CompetitorPrice:
    """Add a competitor to the pricing database."""
    pricing_service.add_competitor(competitor)
    return competitor


__all__ = ["router", "pricing_service"]
