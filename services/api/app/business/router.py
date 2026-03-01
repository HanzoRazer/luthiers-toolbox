"""
Business Suite API Router — Endpoints for financial planning.

Helps luthiers with business fundamentals:
- Bill of Materials
- Cost of Goods Sold
- Pricing strategy
- Break-even analysis
- Cash flow projections
- Engineering cost estimation (parametric)
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
from .goals_service import goals_store
from .schemas import GoalCreateRequest, GoalUpdateRequest, Goal, GoalStatus

# Engineering Estimator
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
estimator_service = EngineeringEstimatorService()


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
# Engineering Cost Estimator Endpoints
# ============================================================================

@router.post("/estimate/parametric", response_model=EstimateResult)
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


@router.post("/estimate/quote", response_model=QuoteResult)
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


@router.get("/estimate/factors")
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


@router.get("/estimate/wbs/{instrument_type}")
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


@router.get("/estimate/learning-curve")
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



# ============================================================================
# Pricing Goals Endpoints
# ============================================================================

@router.get("/goals")
async def list_goals():
    """List all pricing goals."""
    goals = goals_store.list_goals()
    return {"ok": True, "goals": goals, "total": len(goals)}


@router.post("/goals")
async def create_goal(request: GoalCreateRequest):
    """Create a new pricing goal."""
    goal = goals_store.create_goal(request)
    return {"ok": True, "goal": goal}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Get a specific goal."""
    goal = goals_store.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


@router.patch("/goals/{goal_id}")
async def update_goal(goal_id: str, request: GoalUpdateRequest):
    """Update a goal."""
    goal = goals_store.update_goal(goal_id, request)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """Delete a goal."""
    if not goals_store.delete_goal(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True}


@router.post("/goals/{goal_id}/link-estimate/{estimate_id}")
async def link_estimate_to_goal(goal_id: str, estimate_id: str):
    """Link an estimate to a goal."""
    goal = goals_store.link_estimate(goal_id, estimate_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def business_health():
    """Health check for business module."""
    return {
        "status": "healthy",
        "module": "business",
        "services": ["bom", "cogs", "pricing", "breakeven", "cashflow", "estimator", "goals"],
        "purpose": "Financial planning for luthiers",
    }
