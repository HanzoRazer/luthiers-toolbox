1️⃣ RMOS 2.0 API Factory (api_contracts.py)
This is a full replacement for the earlier api_contracts.py we drafted. It:
•	Keeps the same public models (RmosContext, RmosFeasibilityResult, etc.).
•	Adds an RmosServices dataclass as the central wiring point.
•	Adds get_rmos_services() which acts as the factory for the active RMOS implementation.
•	Makes the public functions (compute_feasibility_for_design, etc.) just thin delegators to the services instance.
"""
rmos/api_contracts.py

RMOS 2.0 public API contract + service factory.

This module defines:

- The high-level request/response models that upstream systems
  (Art Studio, AI, CLI, etc.) use to talk to RMOS.
- The RmosServices factory that wires those public APIs to concrete
  implementations (feasibility scorer, BOM calculator, toolpath planner,
  geometry engine selector).

Implementation details live in other modules (calculators, feasibility
scorer, geometry engine, CAM). This file is the stable *contract layer*.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

from pydantic import BaseModel

# NOTE:
# - RosetteParamSpec should already exist in your Art Studio schemas.
#   Adjust import path as needed to match your repo layout.
try:
    from art_studio.schemas.rosette_params import RosetteParamSpec
except ImportError:
    # Temporary fallback stub; replace with real import.
    class RosetteParamSpec(BaseModel):  # type: ignore
        """TODO: replace with real RosetteParamSpec import."""
        outer_diameter_mm: float
        inner_diameter_mm: float


# ---------------------------------------------------------------------------
#  Shared enums / basic types
# ---------------------------------------------------------------------------

class RiskBucket(str, Enum):
    """
    Coarse risk category used across RMOS.

    This should align with calculators.models.RiskBucket if you already
    have one defined there.
    """
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


# ---------------------------------------------------------------------------
#  RMOS context + core result models
# ---------------------------------------------------------------------------

class RmosContext(BaseModel):
    """
    High-level manufacturing context for a design.

    RMOS uses this to look up materials, tools, machine limits, and
    to decide which geometry backend to use (M/L vs Shapely).
    """
    material_id: str
    tool_id: str
    machine_profile_id: Optional[str] = None
    project_id: Optional[str] = None

    # If True, GeometryEngine should prefer Shapely backend where available.
    use_shapely_geometry: bool = False


class RmosFeasibilityResult(BaseModel):
    """
    Aggregated feasibility result for a single design.

    This is what Art Studio / AI / UI should consume.
    """
    overall_score: float                 # 0–100
    risk_bucket: RiskBucket              # GREEN / YELLOW / RED
    material_efficiency: float           # 0–1
    estimated_cut_time_min: float        # rough cut time
    warnings: List[str] = []             # human-readable notes

    # Optional: raw details from calculators/feasibility layer for debugging.
    raw_details: Optional[dict] = None


class RmosBomRingDetail(BaseModel):
    """
    Per-ring BOM/tiling stats (simplified contract).
    """
    ring_id: str
    required_strip_length_mm: float
    estimated_scrap_length_mm: float
    tile_count: Optional[int] = None


class RmosBomResult(BaseModel):
    """
    Bill-of-materials / tiling summary for one design.
    """
    total_strip_length_mm: float
    total_scrap_length_mm: float
    material_efficiency: float = 0.0
    rings: List[RmosBomRingDetail] = []


class RmosToolpathOperation(BaseModel):
    """
    Single toolpath operation summary.

    Implementation-specific details (exact move list, G-code) live in
    lower-level modules. RMOS just exposes high-level structure here.
    """
    op_id: str
    description: str
    strategy: str                 # e.g. "PROFILE", "POCKET", "INLAY_CAVITY"
    estimated_runtime_min: float


class RmosToolpathPlan(BaseModel):
    """
    High-level toolpath plan for a design.

    This is the contract for "what operations will we run?" and
    "how long will it take?" - not the raw G-code.
    """
    operations: List[RmosToolpathOperation] = []
    total_estimated_runtime_min: float = 0.0
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
#  RMOS services factory
# ---------------------------------------------------------------------------

@dataclass
class RmosServices:
    """
    Container for concrete RMOS service implementations.

    This lets you centralize wiring in one place (get_rmos_services)
    and keep the public API (functions below) decoupled from the
    implementation details.

    These callables are expected to be pure functions or thin wrappers
    around your actual services/modules.
    """
    feasibility_scorer: Callable[[RosetteParamSpec, RmosContext], RmosFeasibilityResult]
    bom_calculator: Callable[[RosetteParamSpec, RmosContext], RmosBomResult]
    toolpath_planner: Callable[[RosetteParamSpec, RmosContext], RmosToolpathPlan]
    geometry_engine_selector: Callable[[Optional[RmosContext]], object]


# Global singleton for default services (can be swapped in tests)
_default_services: Optional[RmosServices] = None


def get_rmos_services() -> RmosServices:
    """
    Factory function that returns the active RmosServices instance.

    By default, this wires in the "real" implementations from:
    - rmos.feasibility_scorer
    - calculators.service (BOM)
    - toolpath.service (planner)
    - toolpath.geometry_engine (selector)

    You can override _default_services in tests or alternative deployments.
    """
    global _default_services
    if _default_services is not None:
        return _default_services

    # Lazy imports to avoid circular dependencies at import time.
    # TODO: adjust import paths to your actual module layout.
    from .feasibility_scorer import score_design_feasibility
    from calculators import service as calc_service
    from toolpath import service as toolpath_service
    from toolpath.geometry_engine import get_geometry_engine as _get_geometry_engine

    _default_services = RmosServices(
        feasibility_scorer=score_design_feasibility,
        bom_calculator=calc_service.compute_bom_for_design,
        toolpath_planner=toolpath_service.plan_toolpaths_for_design,
        geometry_engine_selector=_get_geometry_engine,
    )
    return _default_services


def override_rmos_services(services: RmosServices) -> None:
    """
    Override the global RMOS services instance.

    Useful in:
    - unit tests,
    - sandbox deployments,
    - experimental branches where you want to plug in
      alternate implementations.
    """
    global _default_services
    _default_services = services


# ---------------------------------------------------------------------------
#  RMOS 2.0 public API functions (delegating to services)
# ---------------------------------------------------------------------------

def compute_feasibility_for_design(
    design: RosetteParamSpec,
    context: RmosContext,
) -> RmosFeasibilityResult:
    """
    Compute feasibility for a single design.

    This is the canonical entrypoint for:
    - Art Studio
    - AI suggestion lanes
    - CLI tools
    - Constraint-first workflows
    """
    services = get_rmos_services()
    return services.feasibility_scorer(design, context)


def compute_bom_for_design(
    design: RosetteParamSpec,
    context: RmosContext,
) -> RmosBomResult:
    """
    Compute BOM / tiling / strip usage for a design.
    """
    services = get_rmos_services()
    return services.bom_calculator(design, context)


def generate_toolpaths_for_design(
    design: RosetteParamSpec,
    context: RmosContext,
) -> RmosToolpathPlan:
    """
    Generate a high-level toolpath plan for a design.

    This delegates to the CAM toolpath engine (e.g., CAM_N16 lineage)
    via the toolpath_planner callable.
    """
    services = get_rmos_services()
    return services.toolpath_planner(design, context)


def get_geometry_engine(context: Optional[RmosContext] = None) -> object:
    """
    Return the active GeometryEngine instance for the given context.

    This will typically:
    - choose between MLGeometryEngine (legacy) and ShapelyGeometryEngine
      based on config/env and/or context.use_shapely_geometry.
    - return a shared or cached engine instance.
    """
    services = get_rmos_services()
    return services.geometry_engine_selector(context)
You already have rmos/__init__.py re-exporting these; with this factory in place, the rest of the system can keep using:
import rmos

r = rmos.compute_feasibility_for_design(design, ctx)
…and you’ve got a single, controlled place (get_rmos_services) where the implementations are chosen.
________________________________________
