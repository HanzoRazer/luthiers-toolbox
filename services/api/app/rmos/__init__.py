"""
RMOS 2.0 - Rosette Manufacturing Orchestration System
Public API facade for manufacturing feasibility, BOM, and toolpath generation.
"""

from .api_contracts import (
    RmosContext,
    RmosFeasibilityResult,
    RmosBomResult,
    RmosToolpathPlan,
    RiskBucket,
    compute_feasibility_for_design,
    compute_bom_for_design,
    generate_toolpaths_for_design,
    RmosServices
)

from .api_routes import router as rmos_router

__all__ = [
    "RmosContext",
    "RmosFeasibilityResult",
    "RmosBomResult",
    "RmosToolpathPlan",
    "RiskBucket",
    "compute_feasibility_for_design",
    "compute_bom_for_design",
    "generate_toolpaths_for_design",
    "RmosServices",
    "rmos_router"
]

__version__ = "2.0.0"
