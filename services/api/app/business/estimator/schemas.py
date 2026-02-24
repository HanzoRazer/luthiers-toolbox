"""
Engineering Estimator Schemas — Data types for parametric estimation.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class InstrumentType(str, Enum):
    """Instrument types with WBS templates."""
    ACOUSTIC_DREADNOUGHT = "acoustic_dreadnought"
    ACOUSTIC_OM = "acoustic_om"
    ACOUSTIC_PARLOR = "acoustic_parlor"
    CLASSICAL = "classical"
    ELECTRIC_SOLID = "electric_solid"
    ELECTRIC_HOLLOW = "electric_hollow"
    ELECTRIC_SEMI = "electric_semi"
    BASS_4 = "bass_4"
    BASS_5 = "bass_5"


class BuilderExperience(str, Enum):
    """Builder experience level affects base times."""
    BEGINNER = "beginner"          # 1.5x multiplier
    INTERMEDIATE = "intermediate"  # 1.2x multiplier
    EXPERIENCED = "experienced"    # 1.0x multiplier
    MASTER = "master"              # 0.85x multiplier


class BodyComplexity(str, Enum):
    """Body complexity options."""
    STANDARD = "standard"
    CUTAWAY_SOFT = "cutaway_soft"
    CUTAWAY_FLORENTINE = "cutaway_florentine"
    CUTAWAY_VENETIAN = "cutaway_venetian"
    ARM_BEVEL = "arm_bevel"
    TUMMY_CUT = "tummy_cut"
    CARVED_TOP = "carved_top"


class BindingComplexity(str, Enum):
    """Binding complexity options."""
    NONE = "none"
    SINGLE = "single"
    MULTIPLE = "multiple"
    HERRINGBONE = "herringbone"


class NeckComplexity(str, Enum):
    """Neck complexity options."""
    STANDARD = "standard"
    VOLUTE = "volute"
    SCARF_JOINT = "scarf_joint"
    MULTI_SCALE = "multi_scale"


class FretboardInlay(str, Enum):
    """Fretboard inlay complexity."""
    NONE = "none"
    DOTS = "dots"
    BLOCKS = "blocks"
    TRAPEZOIDS = "trapezoids"
    CUSTOM = "custom"


class FinishType(str, Enum):
    """Finish type options."""
    OIL = "oil"
    WAX = "wax"
    SHELLAC_WIPE = "shellac_wipe"
    SHELLAC_FRENCH_POLISH = "shellac_french_polish"
    NITRO_SOLID = "nitro_solid"
    NITRO_BURST = "nitro_burst"
    NITRO_VINTAGE = "nitro_vintage"
    POLY_SOLID = "poly_solid"
    POLY_BURST = "poly_burst"


class RosetteComplexity(str, Enum):
    """Rosette complexity options."""
    NONE = "none"
    SIMPLE_RINGS = "simple_rings"
    MOSAIC = "mosaic"
    CUSTOM_ART = "custom_art"


# =============================================================================
# INPUT MODELS
# =============================================================================

class ComplexitySelections(BaseModel):
    """Design complexity selections for estimation."""

    # Body
    body: List[BodyComplexity] = Field(
        default=[BodyComplexity.STANDARD],
        description="Body complexity features (can combine)",
    )

    # Binding
    binding_body: BindingComplexity = Field(
        default=BindingComplexity.NONE,
        description="Body binding complexity",
    )
    binding_neck: bool = Field(
        default=False,
        description="Bound fretboard",
    )
    binding_headstock: bool = Field(
        default=False,
        description="Bound headstock",
    )

    # Neck
    neck: List[NeckComplexity] = Field(
        default=[NeckComplexity.STANDARD],
        description="Neck complexity features",
    )

    # Inlays
    fretboard_inlay: FretboardInlay = Field(
        default=FretboardInlay.DOTS,
        description="Fretboard inlay style",
    )
    headstock_inlay: bool = Field(
        default=False,
        description="Custom headstock inlay",
    )

    # Finish
    finish: FinishType = Field(
        default=FinishType.NITRO_SOLID,
        description="Finish type",
    )

    # Rosette (acoustic only)
    rosette: RosetteComplexity = Field(
        default=RosetteComplexity.SIMPLE_RINGS,
        description="Rosette complexity",
    )

    # Electronics (electric only)
    pickup_count: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Number of pickups",
    )
    active_electronics: bool = Field(
        default=False,
        description="Active electronics (battery box, preamp)",
    )


class EstimateRequest(BaseModel):
    """Request for parametric cost estimate."""

    instrument_type: InstrumentType = Field(
        ...,
        description="Type of instrument to estimate",
    )

    complexity: ComplexitySelections = Field(
        default_factory=ComplexitySelections,
        description="Design complexity selections",
    )

    quantity: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of units to build",
    )

    builder_experience: BuilderExperience = Field(
        default=BuilderExperience.EXPERIENCED,
        description="Builder experience level",
    )

    # Optional overrides
    hourly_rate_override: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override default blended hourly rate",
    )

    learning_rate: float = Field(
        default=0.85,
        ge=0.7,
        le=1.0,
        description="Learning curve rate (0.85 = 15% improvement per doubling)",
    )

    include_material_waste: bool = Field(
        default=True,
        description="Include material waste factors in cost",
    )


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class WBSTask(BaseModel):
    """Single task in work breakdown structure."""

    task_id: str
    task_name: str
    base_hours: float
    complexity_multiplier: float
    adjusted_hours: float
    labor_cost: float
    notes: Optional[str] = None


class LearningCurvePoint(BaseModel):
    """Single point on learning curve."""

    unit_number: int
    hours_per_unit: float
    cumulative_hours: float
    cumulative_cost: float


class LearningCurveProjection(BaseModel):
    """Learning curve projection for batch production."""

    first_unit_hours: float
    learning_rate: float
    quantity: int
    points: List[LearningCurvePoint]
    average_hours_per_unit: float
    total_hours: float
    efficiency_gain_pct: float  # vs building all at first-unit pace


class MaterialEstimate(BaseModel):
    """Material cost estimate with waste factors."""

    category: str
    base_cost: float
    waste_factor: float
    adjusted_cost: float


class RiskFactor(BaseModel):
    """Risk factor affecting estimate confidence."""

    factor: str
    impact: str  # "low", "medium", "high"
    description: str


class EstimateResult(BaseModel):
    """Complete parametric estimate result."""

    # Summary
    instrument_type: str
    quantity: int

    # Hours
    first_unit_hours: float
    average_hours_per_unit: float
    total_hours: float

    # Costs
    labor_cost_per_unit: float
    material_cost_per_unit: float
    total_cost_per_unit: float
    total_project_cost: float

    # Breakdown
    wbs_tasks: List[WBSTask]
    material_breakdown: List[MaterialEstimate]
    learning_curve: Optional[LearningCurveProjection]

    # Complexity summary
    complexity_factors_applied: Dict[str, float]
    total_complexity_multiplier: float

    # Experience adjustment
    experience_level: str
    experience_multiplier: float

    # Confidence
    confidence_level: str  # "high", "medium", "low"
    risk_factors: List[RiskFactor]
    estimate_range_low: float
    estimate_range_high: float

    # Metadata
    notes: List[str]


class QuoteRequest(BaseModel):
    """Request to generate a customer quote from estimate."""

    estimate: EstimateResult
    target_margin_pct: float = Field(
        default=40.0,
        ge=0,
        le=90,
        description="Target profit margin percentage",
    )

    include_design_fee: bool = Field(
        default=False,
        description="Add separate design/consultation fee",
    )
    design_fee: float = Field(
        default=0.0,
        ge=0,
        description="Design fee if included",
    )

    deposit_pct: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="Deposit percentage",
    )


class QuoteResult(BaseModel):
    """Customer quote generated from estimate."""

    # Pricing
    base_cost: float
    markup: float
    subtotal: float
    design_fee: float
    total_price: float

    # Margin analysis
    gross_margin: float
    gross_margin_pct: float

    # Payment terms
    deposit_amount: float
    balance_due: float

    # Confidence
    price_range_low: float
    price_range_high: float

    # For customer
    lead_time_weeks: int
    valid_days: int = 30
