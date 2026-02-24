"""
Business Suite API Router — Endpoints for financial planning.

Helps luthiers with business fundamentals:
- Bill of Materials
- Cost of Goods Sold
- Pricing strategy
- Break-even analysis
- Cash flow projections
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    Material,
    MaterialCategory,
    BillOfMaterials,
    COGSBreakdown,
    PricingStrategy,
    BreakEvenAnalysis,
    CashFlowProjection,
    InstrumentType,
    LaborCategory,
    CompetitorPrice,
)
from .bom_service import BOMService
from .cogs_service import COGSService
from .pricing_service import PricingService
from .breakeven_service import BreakEvenService
from .cashflow_service import CashFlowService


router = APIRouter(
    prefix="/api/business",
    tags=["business"],
)

# Services (singleton instances)
bom_service = BOMService()
cogs_service = COGSService()
pricing_service = PricingService()
breakeven_service = BreakEvenService()
cashflow_service = CashFlowService()


# ============================================================================
# BOM Endpoints
# ============================================================================

@router.get("/materials", response_model=List[Material])
async def list_materials(
    category: Optional[MaterialCategory] = None,
) -> List[Material]:
    """List all materials in the library, optionally filtered by category."""
    return bom_service.list_materials(category)


@router.get("/materials/{material_id}", response_model=Material)
async def get_material(material_id: str) -> Material:
    """Get a specific material by ID."""
    material = bom_service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("/materials", response_model=Material)
async def add_material(material: Material) -> Material:
    """Add a new material to the library."""
    bom_service.add_material(material)
    return material


@router.post("/bom/from-template", response_model=BillOfMaterials)
async def create_bom_from_template(
    instrument_type: InstrumentType,
    instrument_name: str = Query(..., min_length=1),
) -> BillOfMaterials:
    """
    Create a Bill of Materials from a template.

    Templates available for:
    - acoustic_dreadnought
    - classical
    - electric_solid (coming soon)
    """
    return bom_service.create_bom_from_template(
        instrument_type=instrument_type,
        instrument_name=instrument_name,
    )


@router.get("/bom/templates")
async def list_bom_templates():
    """List available BOM templates."""
    return {
        "templates": [
            {
                "type": t.value,
                "name": t.value.replace("_", " ").title(),
                "available": t in bom_service.BOM_TEMPLATES,
            }
            for t in InstrumentType
        ]
    }


# ============================================================================
# COGS Endpoints
# ============================================================================

@router.post("/cogs/calculate", response_model=COGSBreakdown)
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


@router.get("/cogs/labor-rates")
async def get_labor_rates():
    """Get current labor rates by category."""
    return {
        "rates": [
            {"category": cat.value, "hourly_rate": rate}
            for cat, rate in cogs_service.labor_rates.items()
        ]
    }


@router.put("/cogs/labor-rates/{category}")
async def update_labor_rate(
    category: LaborCategory,
    hourly_rate: float = Query(..., ge=0),
):
    """Update the hourly rate for a labor category."""
    cogs_service.update_labor_rate(category, hourly_rate)
    return {"status": "updated", "category": category.value, "hourly_rate": hourly_rate}


@router.get("/cogs/overhead")
async def get_overhead_summary():
    """Get current overhead configuration."""
    return cogs_service.get_overhead_summary()


# ============================================================================
# Pricing Endpoints
# ============================================================================

@router.post("/pricing/calculate", response_model=PricingStrategy)
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


@router.get("/pricing/competitors")
async def get_competitor_summary(
    instrument_type: Optional[str] = None,
):
    """Get summary of competitor pricing landscape."""
    return pricing_service.get_competitor_summary(instrument_type)


@router.post("/pricing/competitors", response_model=CompetitorPrice)
async def add_competitor(competitor: CompetitorPrice) -> CompetitorPrice:
    """Add a competitor to the pricing database."""
    pricing_service.add_competitor(competitor)
    return competitor


# ============================================================================
# Break-Even Endpoints
# ============================================================================

@router.post("/breakeven/calculate", response_model=BreakEvenAnalysis)
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


@router.post("/breakeven/target-profit")
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


@router.post("/breakeven/sensitivity")
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


# ============================================================================
# Cash Flow Endpoints
# ============================================================================

@router.post("/cashflow/project", response_model=CashFlowProjection)
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


@router.post("/cashflow/startup", response_model=CashFlowProjection)
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


@router.post("/cashflow/required-capital")
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


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def business_health():
    """Health check for business module."""
    return {
        "status": "healthy",
        "module": "business",
        "services": ["bom", "cogs", "pricing", "breakeven", "cashflow"],
        "purpose": "Financial planning for luthiers",
    }
