"""Business Suite API Router (Consolidated)

Thin wrapper that re-exports from focused sub-modules:
- bom_router.py (5 routes)
- cogs_router.py (4 routes)
- pricing_router.py (3 routes)
- breakeven_router.py (3 routes)
- cashflow_router.py (3 routes)
- estimator_router.py (5 routes)
- goals_router.py (6 routes)

Total: 29 routes under /api/business

LANE: UTILITY (business planning operations)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Helps luthiers with business fundamentals:
- Bill of Materials
- Cost of Goods Sold
- Pricing strategy
- Break-even analysis
- Cash flow projections
- Engineering cost estimation (parametric)
- Pricing goals management
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .bom_router import router as bom_router
from .cogs_router import router as cogs_router
from .pricing_router import router as pricing_router
from .breakeven_router import router as breakeven_router
from .cashflow_router import router as cashflow_router
from .estimator_router import router as estimator_router
from .goals_router import router as goals_router

# Re-export schemas for backward compatibility
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
    GoalCreateRequest,
    GoalUpdateRequest,
    Goal,
    GoalStatus,
)

# Re-export services for direct access
from .bom_router import bom_service
from .cogs_router import cogs_service
from .pricing_router import pricing_service
from .breakeven_router import breakeven_service
from .cashflow_router import cashflow_service
from .estimator_router import estimator_service
from .goals_router import goals_store

# Aggregate router
router = APIRouter(
    prefix="/api/business",
    tags=["business"],
)

# Mount sub-routers with prefixes
# Materials endpoints at root level for backward compatibility (/api/business/materials/...)
router.include_router(bom_router, tags=["BOM"])  # materials at root
router.include_router(bom_router, prefix="/bom", tags=["BOM"])  # BOM templates under /bom
router.include_router(cogs_router, prefix="/cogs", tags=["COGS"])
router.include_router(pricing_router, prefix="/pricing", tags=["Pricing"])
router.include_router(breakeven_router, prefix="/breakeven", tags=["Break-Even"])
router.include_router(cashflow_router, prefix="/cashflow", tags=["Cash Flow"])
router.include_router(estimator_router, prefix="/estimate", tags=["Estimator"])
router.include_router(goals_router, prefix="/goals", tags=["Goals"])


# ============================================================================
# Convenience functions for cross-module access
# ============================================================================

def get_material(material_id: str):
    """Get material by ID (used by other modules like CAM energy calculations)."""
    return bom_service.get_material(material_id)


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", summary="Business module health check")
async def business_health():
    """Health check for business module."""
    return {
        "status": "healthy",
        "module": "business",
        "services": ["bom", "cogs", "pricing", "breakeven", "cashflow", "estimator", "goals"],
        "purpose": "Financial planning for luthiers",
    }


__all__ = [
    # Routers
    "router",
    "bom_router",
    "cogs_router",
    "pricing_router",
    "breakeven_router",
    "cashflow_router",
    "estimator_router",
    "goals_router",
    # Services
    "bom_service",
    "cogs_service",
    "pricing_service",
    "breakeven_service",
    "cashflow_service",
    "estimator_service",
    "goals_store",
    # Schemas
    "Material",
    "MaterialCategory",
    "BillOfMaterials",
    "COGSBreakdown",
    "PricingStrategy",
    "BreakEvenAnalysis",
    "CashFlowProjection",
    "InstrumentType",
    "LaborCategory",
    "CompetitorPrice",
    "GoalCreateRequest",
    "GoalUpdateRequest",
    "Goal",
    "GoalStatus",
    # Convenience functions
    "get_material",
]
