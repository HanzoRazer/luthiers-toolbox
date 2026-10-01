"""
RMOS 2.0 API Contracts
Factory pattern for lazy-loaded service initialization and type definitions.
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

from app.safety import safety_critical


# ======================
# Risk & Feasibility Types
# ======================

class RiskBucket(str, Enum):
    """Risk classification for manufacturing feasibility"""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class RmosFeasibilityResult(BaseModel):
    """Result of feasibility analysis"""
    score: float = Field(..., ge=0, le=100, description="Overall feasibility score 0-100")
    risk_bucket: RiskBucket = Field(..., description="GREEN/YELLOW/RED classification")
    warnings: List[str] = Field(default_factory=list, description="Manufacturing warnings")
    efficiency: Optional[float] = Field(None, description="Material efficiency percentage")
    estimated_cut_time_seconds: Optional[float] = Field(None, description="Estimated machining time")
    calculator_results: Dict[str, Any] = Field(default_factory=dict, description="Individual calculator outputs")


# ======================
# BOM & Toolpath Types
# ======================

class RmosBomResult(BaseModel):
    """Bill of Materials result"""
    material_required_mm2: float = Field(..., description="Material area required")
    tool_ids: List[str] = Field(default_factory=list, description="Required tool identifiers")
    estimated_waste_percent: float = Field(0.0, description="Waste percentage")
    notes: List[str] = Field(default_factory=list, description="BOM notes")


class RmosToolpathPlan(BaseModel):
    """Toolpath planning result"""
    toolpaths: List[Dict[str, Any]] = Field(default_factory=list, description="Generated toolpath segments")
    total_length_mm: float = Field(0.0, description="Total toolpath length")
    estimated_time_seconds: float = Field(0.0, description="Estimated runtime")
    warnings: List[str] = Field(default_factory=list, description="Toolpath warnings")


# ======================
# Context & Design Types
# ======================

class RmosContext(BaseModel):
    """Manufacturing environment snapshot.

    The machine/process facts below are consumed by the Saw feasibility path
    (``feasibility_scorer`` -> ``SawEngine.check_feasibility`` conversions).
    ``_score_via_scorer`` already forwarded them, but they were previously
    undeclared here; under pydantic v2's default ``extra='ignore'`` they were
    silently dropped, so the Saw evaluator scored on hardcoded conversion
    defaults regardless of the truthful request. They are optional (``None``)
    so router/rosette scoring is unaffected; the Saw feasibility path guards on
    their presence and returns UNKNOWN rather than scoring on defaults when a
    safety-critical fact is missing.
    """
    material_id: Optional[str] = Field(None, description="Material database ID")
    tool_id: Optional[str] = Field(None, description="Tool database ID")
    machine_profile_id: Optional[str] = Field(None, description="Machine profile ID")
    use_shapely_geometry: bool = Field(True, description="Use Shapely vs ML geometry engine")
    # Machine/process facts (consumed by the Saw scorer path; optional for other modes).
    # Additive and optional so router/rosette scoring is unaffected; the Saw feasibility
    # path guards on presence and returns UNKNOWN rather than scoring on a default when a
    # safety-critical fact is absent. Bounds mirror ``saw_lab.models.SawContext``.
    rpm: Optional[float] = Field(None, description="Spindle/blade RPM (C-axis)")
    feed_rate_mm_min: Optional[float] = Field(None, description="Feed rate (mm/min)")
    spindle_power_watts: Optional[float] = Field(None, description="Available spindle/machine power (W); legacy alias, convert once to kW")
    tool_diameter_mm: Optional[float] = Field(None, description="Tool/blade diameter (mm); legacy alias of blade_diameter_mm")
    tooth_count: Optional[int] = Field(None, description="Blade tooth count")
    blade_diameter_mm: Optional[float] = Field(None, ge=100.0, le=600.0, description="Saw blade diameter (mm)")
    blade_kerf_mm: Optional[float] = Field(None, ge=1.0, le=10.0, description="Saw blade kerf (mm)")
    blade_thickness_mm: Optional[float] = Field(None, ge=0.5, le=8.0, description="Saw blade plate thickness (mm)")
    arbor_size_mm: Optional[float] = Field(None, ge=10.0, le=50.0, description="Saw arbor diameter (mm)")
    stock_thickness_mm: Optional[float] = Field(None, ge=1.0, le=150.0, description="Stock thickness (mm)")
    machine_power_kw: Optional[float] = Field(None, ge=0.5, le=20.0, description="Available machine power (kW)")
    blade_youngs_modulus_gpa: Optional[float] = Field(None, ge=100.0, le=250.0, description="Blade material Young's modulus (GPa)")
    use_dust_collection: Optional[bool] = Field(None, description="Dust collection engaged")


# Lazy import stub for RosetteParamSpec to prevent circular dependencies
try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    # Fallback stub if art_studio not yet available
    class RosetteParamSpec(BaseModel):  # type: ignore
        outer_diameter_mm: float = 100.0
        inner_diameter_mm: float = 20.0
        ring_count: int = 3
        pattern_type: str = "herringbone"


# ======================
# Service Factory Pattern
# ======================

class RmosServices:
    """
    Factory for lazy-loaded RMOS service instances.
    Prevents circular dependencies by deferring imports until first use.
    """
    _feasibility_scorer = None
    _calculator_service = None
    _geometry_engine = None
    _toolpath_service = None

    @classmethod
    def get_feasibility_scorer(cls):
        """Lazy-load feasibility scorer"""
        if cls._feasibility_scorer is None:
            from .feasibility_scorer import score_design_feasibility
            cls._feasibility_scorer = score_design_feasibility
        return cls._feasibility_scorer

    @classmethod
    def get_calculator_service(cls):
        """Lazy-load calculator service"""
        if cls._calculator_service is None:
            from ..calculators.service import CalculatorService
            cls._calculator_service = CalculatorService()
        return cls._calculator_service

    @classmethod
    def get_geometry_engine(cls, ctx: RmosContext):
        """Lazy-load geometry engine with strategy selection"""
        if cls._geometry_engine is None:
            from ..toolpath.geometry_engine import get_geometry_engine
            cls._geometry_engine = get_geometry_engine
        return cls._geometry_engine(ctx)

    @classmethod
    def get_toolpath_service(cls):
        """Lazy-load toolpath service"""
        if cls._toolpath_service is None:
            from ..toolpath.service import ToolpathService
            cls._toolpath_service = ToolpathService()
        return cls._toolpath_service


# ======================
# Core API Functions
# ======================

@safety_critical
def compute_feasibility_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosFeasibilityResult:
    """
    Main feasibility computation entry point.
    All three directional workflows funnel through this function.
    """
    scorer = RmosServices.get_feasibility_scorer()
    return scorer(design, ctx)


def compute_bom_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosBomResult:
    """
    Compute Bill of Materials for a design.
    """
    calc_service = RmosServices.get_calculator_service()
    return calc_service.compute_bom(design, ctx)


def generate_toolpaths_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext
) -> RmosToolpathPlan:
    """
    Generate toolpath plan for a design.
    """
    toolpath_service = RmosServices.get_toolpath_service()
    return toolpath_service.generate_toolpaths(design, ctx)
