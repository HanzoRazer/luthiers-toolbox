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
    """Manufacturing environment snapshot"""
    material_id: Optional[str] = Field(None, description="Material database ID")
    tool_id: Optional[str] = Field(None, description="Tool database ID")
    machine_profile_id: Optional[str] = Field(None, description="Machine profile ID")
    use_shapely_geometry: bool = Field(True, description="Use Shapely vs ML geometry engine")


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
