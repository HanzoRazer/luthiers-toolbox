# services/api/app/business/schemas.py
"""
Business Estimator Schemas - Pydantic models for cost estimation.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field

class InstrumentType(str, Enum):
    ACOUSTIC_DREADNOUGHT = "acoustic_dreadnought"
    ACOUSTIC_OM = "acoustic_om"
    ACOUSTIC_PARLOR = "acoustic_parlor"
    CLASSICAL = "classical"
    ELECTRIC_SOLID = "electric_solid"
    ELECTRIC_HOLLOW = "electric_hollow"
    ELECTRIC_SEMI_HOLLOW = "electric_semi_hollow"
    BASS_4 = "bass_4"
    BASS_5 = "bass_5"
    UKULELE = "ukulele"

class BuilderExperience(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
    MASTER = "master"

class BodyComplexity(str, Enum):
    STANDARD = "standard"
    CUTAWAY_SOFT = "cutaway_soft"
    CUTAWAY_FLORENTINE = "cutaway_florentine"
    CUTAWAY_VENETIAN = "cutaway_venetian"
    DOUBLE_CUTAWAY = "double_cutaway"
    ARM_BEVEL = "arm_bevel"
    TUMMY_CUT = "tummy_cut"
    CARVED_TOP = "carved_top"

class BindingComplexity(str, Enum):
    NONE = "none"
    SINGLE = "single"
    MULTIPLE = "multiple"
    HERRINGBONE = "herringbone"

class NeckComplexity(str, Enum):
    STANDARD = "standard"
    VOLUTE = "volute"
    SCARF_JOINT = "scarf_joint"
    MULTI_SCALE = "multi_scale"

class FretboardInlay(str, Enum):
    NONE = "none"
    DOTS = "dots"
    BLOCKS = "blocks"
    TRAPEZOIDS = "trapezoids"
    CUSTOM = "custom"

class FinishType(str, Enum):
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
    NONE = "none"
    SIMPLE_RINGS = "simple_rings"
    MOSAIC = "mosaic"
    CUSTOM_ART = "custom_art"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ARCHIVED = "archived"

class EstimateRequest(BaseModel):
    instrument_type: InstrumentType
    builder_experience: BuilderExperience
    body_complexity: list[BodyComplexity] = Field(default_factory=lambda: [BodyComplexity.STANDARD])
    binding_body_complexity: BindingComplexity = BindingComplexity.NONE
    neck_complexity: NeckComplexity = NeckComplexity.STANDARD
    fretboard_inlay: FretboardInlay = FretboardInlay.DOTS
    finish_type: FinishType = FinishType.OIL
    rosette_complexity: RosetteComplexity = RosetteComplexity.NONE
    batch_size: int = Field(default=1, ge=1, le=100)
    hourly_rate: float = Field(default=50.0, ge=0)
    include_materials: bool = True

class GoalCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    instrument_type: InstrumentType
    target_cost: float = Field(ge=0)
    target_hours: float = Field(ge=0)
    deadline: datetime | None = None
    notes: str | None = None

class GoalUpdateRequest(BaseModel):
    name: str | None = None
    target_cost: float | None = Field(default=None, ge=0)
    target_hours: float | None = Field(default=None, ge=0)
    status: GoalStatus | None = None
    deadline: datetime | None = None
    notes: str | None = None

class WBSTask(BaseModel):
    task_id: str
    task_name: str
    base_hours: float
    complexity_multiplier: float
    adjusted_hours: float
    labor_cost: float
    notes: str | None = None

class MaterialEstimate(BaseModel):
    category: str
    base_cost: float
    waste_factor: float
    adjusted_cost: float

class LearningCurvePoint(BaseModel):
    unit_number: int
    hours_per_unit: float
    cumulative_hours: float
    cumulative_cost: float

class LearningCurveProjection(BaseModel):
    first_unit_hours: float
    learning_rate: float
    quantity: int
    points: list[LearningCurvePoint]
    average_hours_per_unit: float
    total_hours: float
    efficiency_gain_pct: float

class RiskFactor(BaseModel):
    factor: str
    impact: str
    description: str

class EstimateResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    instrument_type: str
    quantity: int
    first_unit_hours: float
    average_hours_per_unit: float
    total_hours: float
    labor_cost_per_unit: float
    material_cost_per_unit: float
    total_cost_per_unit: float
    total_project_cost: float
    wbs_tasks: list[WBSTask]
    material_breakdown: list[MaterialEstimate]
    learning_curve: LearningCurveProjection | None = None
    complexity_factors_applied: dict[str, float]
    total_complexity_multiplier: float
    experience_level: str
    experience_multiplier: float
    confidence_level: str
    risk_factors: list[RiskFactor]
    estimate_range_low: float
    estimate_range_high: float
    notes: list[str]

class EstimateResponse(BaseModel):
    ok: bool = True
    estimate: EstimateResult

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    name: str
    instrument_type: str
    target_cost: float
    target_hours: float
    current_best_cost: float | None = None
    current_best_hours: float | None = None
    progress_pct: float = 0.0
    status: GoalStatus = GoalStatus.ACTIVE
    deadline: datetime | None = None
    notes: str | None = None
    estimate_ids: list[str] = Field(default_factory=list)

class GoalResponse(BaseModel):
    ok: bool = True
    goal: Goal

class GoalListResponse(BaseModel):
    ok: bool = True
    goals: list[Goal]
    total: int

class EstimateListResponse(BaseModel):
    ok: bool = True
    estimates: list[EstimateResult]
    total: int

class SyncStatusResponse(BaseModel):
    ok: bool = True
    synced: bool
    last_sync: datetime | None = None
    pending_count: int = 0
