"""
Business Suite Schemas — Types for financial planning.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class MaterialCategory(str, Enum):
    """Categories of materials in guitar building."""
    TONEWOOD = "tonewood"
    HARDWARE = "hardware"
    STRINGS = "strings"
    FINISH = "finish"
    ADHESIVE = "adhesive"
    ABRASIVE = "abrasive"
    FRET_WIRE = "fret_wire"
    BINDING = "binding"
    INLAY = "inlay"
    ELECTRONICS = "electronics"
    CASE = "case"
    OTHER = "other"


class LaborCategory(str, Enum):
    """Categories of labor in guitar building."""
    DESIGN = "design"
    WOOD_PREP = "wood_prep"
    JOINERY = "joinery"
    CARVING = "carving"
    FRETTING = "fretting"
    FINISHING = "finishing"
    ASSEMBLY = "assembly"
    SETUP = "setup"
    QA = "qa"
    ADMIN = "admin"


# NOTE: PricingModel enum removed 2026-02-26 (dead code - PricingStrategy used instead)


class InstrumentType(str, Enum):
    """Types of instruments for BOM templates."""
    ACOUSTIC_DREADNOUGHT = "acoustic_dreadnought"
    ACOUSTIC_OM = "acoustic_om"
    ACOUSTIC_PARLOR = "acoustic_parlor"
    CLASSICAL = "classical"
    ELECTRIC_SOLID = "electric_solid"
    ELECTRIC_HOLLOW = "electric_hollow"
    BASS_4 = "bass_4"
    BASS_5 = "bass_5"
    UKULELE = "ukulele"
    MANDOLIN = "mandolin"
    CUSTOM = "custom"


# ============================================================================
# MATERIALS & BOM
# ============================================================================

class Material(BaseModel):
    """A material used in guitar building."""
    id: str = Field(..., description="Unique identifier")
    name: str
    category: MaterialCategory
    unit: str = Field(..., description="Unit of measure (bd_ft, piece, oz, etc.)")
    unit_cost: float = Field(..., ge=0, description="Cost per unit in USD")
    supplier: Optional[str] = None
    notes: Optional[str] = None

    # For wood
    species: Optional[str] = None
    grade: Optional[str] = None  # AAA, AA, A, etc.


class BOMItem(BaseModel):
    """A line item in a Bill of Materials."""
    material_id: str
    material_name: str
    category: MaterialCategory
    quantity: float = Field(..., gt=0)
    unit: str
    unit_cost: float
    extended_cost: float = Field(..., description="quantity × unit_cost")
    notes: Optional[str] = None


class BillOfMaterials(BaseModel):
    """Complete Bill of Materials for an instrument."""
    instrument_type: InstrumentType
    instrument_name: str
    created_at: str

    items: List[BOMItem] = []

    # Calculated totals
    total_materials_cost: float = 0.0
    total_items: int = 0

    # By category
    cost_by_category: Dict[str, float] = {}


# ============================================================================
# LABOR
# ============================================================================

class LaborRate(BaseModel):
    """Hourly rate for a category of labor."""
    category: LaborCategory
    hourly_rate: float = Field(..., ge=0, description="USD per hour")
    description: Optional[str] = None


class LaborEntry(BaseModel):
    """Time spent on a task."""
    category: LaborCategory
    hours: float = Field(..., ge=0)
    hourly_rate: float
    total_cost: float = Field(..., description="hours × hourly_rate")
    task_description: Optional[str] = None


class LaborEstimate(BaseModel):
    """Estimated labor for building an instrument."""
    instrument_type: InstrumentType
    entries: List[LaborEntry] = []
    total_hours: float = 0.0
    total_labor_cost: float = 0.0

    # By category
    hours_by_category: Dict[str, float] = {}


# ============================================================================
# COGS (Cost of Goods Sold)
# ============================================================================

class OverheadItem(BaseModel):
    """A fixed or variable overhead cost."""
    name: str
    monthly_cost: float
    is_fixed: bool = True  # Fixed vs variable
    notes: Optional[str] = None


class COGSBreakdown(BaseModel):
    """Complete Cost of Goods Sold analysis."""
    instrument_name: str
    calculated_at: str

    # Direct costs
    materials_cost: float = 0.0
    labor_cost: float = 0.0
    direct_costs_total: float = 0.0

    # Overhead allocation
    overhead_per_unit: float = 0.0
    overhead_allocation_method: str = "per_unit"  # or "percentage"

    # Total COGS
    total_cogs: float = 0.0

    # Breakdown
    materials_breakdown: Optional[BillOfMaterials] = None
    labor_breakdown: Optional[LaborEstimate] = None

    # Margins at various prices
    margin_analysis: List[Dict[str, float]] = []


# ============================================================================
# PRICING
# ============================================================================

class CompetitorPrice(BaseModel):
    """Competitor pricing data point."""
    competitor_name: str
    instrument_type: str
    price: float
    quality_tier: str = "mid"  # "entry", "mid", "premium", "custom"
    source: Optional[str] = None
    date_observed: Optional[str] = None


class PricingStrategy(BaseModel):
    """Pricing recommendation with analysis."""
    instrument_name: str
    cogs: float

    # Different pricing approaches
    cost_plus_price: float = Field(..., description="COGS + markup")
    cost_plus_markup_pct: float = 50.0

    market_based_price: Optional[float] = None
    market_position: Optional[str] = None  # "below", "at", "above"

    value_based_price: Optional[float] = None
    value_justification: Optional[str] = None

    # Recommended price
    recommended_price: float
    recommended_margin: float
    recommended_margin_pct: float

    # Analysis
    break_even_units: Optional[float] = None
    notes: List[str] = []


# ============================================================================
# BREAK-EVEN ANALYSIS
# ============================================================================

class BreakEvenAnalysis(BaseModel):
    """Break-even analysis for a product or business."""
    analysis_name: str
    calculated_at: str

    # Inputs
    fixed_costs_monthly: float
    variable_cost_per_unit: float  # COGS
    selling_price_per_unit: float

    # Results
    contribution_margin: float = Field(
        ..., description="Price - Variable Cost"
    )
    contribution_margin_pct: float
    break_even_units: float = Field(
        ..., description="Units needed to cover fixed costs"
    )
    break_even_revenue: float

    # Scenarios
    scenarios: List[Dict[str, Any]] = []  # What-if analysis


# ============================================================================
# CASH FLOW
# ============================================================================

class CashFlowMonth(BaseModel):
    """Cash flow for a single month."""
    month: int  # 1-12 or 1-36 for multi-year
    month_label: str  # "Jan 2026"

    # Inflows
    revenue: float = 0.0
    other_income: float = 0.0
    total_inflows: float = 0.0

    # Outflows
    materials: float = 0.0
    labor: float = 0.0
    overhead: float = 0.0
    other_expenses: float = 0.0
    total_outflows: float = 0.0

    # Net
    net_cash_flow: float = 0.0
    cumulative_cash_flow: float = 0.0

    # Status
    is_positive: bool = True


class CashFlowProjection(BaseModel):
    """Multi-month cash flow projection."""
    projection_name: str
    created_at: str
    months: int = 12

    # Starting position
    starting_cash: float = 0.0

    # Monthly data
    monthly_data: List[CashFlowMonth] = []

    # Summary
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    net_cash_flow: float = 0.0
    ending_cash: float = 0.0

    # Key metrics
    months_to_positive: Optional[int] = None
    runway_months: Optional[int] = None  # How long cash lasts if no revenue
    minimum_cash_month: Optional[int] = None
    minimum_cash_amount: Optional[float] = None

    # Warnings
    warnings: List[str] = []


# ============================================================================
# BUSINESS PLAN SUMMARY
# ============================================================================

class BusinessPlanSummary(BaseModel):
    """High-level business plan summary."""
    business_name: str
    created_at: str

    # Products
    products: List[Dict[str, Any]] = []  # Name, COGS, Price, Annual Volume

    # Financials
    annual_revenue_target: float
    annual_cogs: float
    gross_margin: float
    gross_margin_pct: float

    # Fixed costs
    monthly_overhead: float
    annual_overhead: float

    # Break-even
    monthly_break_even_revenue: float
    annual_break_even_revenue: float
    break_even_units_per_year: Dict[str, float] = {}

    # Cash requirements
    startup_costs: float = 0.0
    working_capital_needed: float = 0.0
    total_funding_needed: float = 0.0

    # Timeline
    months_to_break_even: Optional[int] = None
    months_to_profitability: Optional[int] = None
