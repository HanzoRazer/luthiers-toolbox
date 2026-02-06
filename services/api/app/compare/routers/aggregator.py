"""
Compare Router Aggregator

Single router combining all compare category routers.

Mounted at /api/compare in main.py, provides:
    /baselines/*     - Baseline CRUD and geometry diff
    /risk/*          - Risk aggregation and bucket analysis
    /lab/*           - Compare Lab UI endpoints
    /automation/*    - SVG compare automation
"""

from fastapi import APIRouter

from .baselines import router as baselines_router
from .risk import router as risk_router
from .lab import router as lab_router
# WP-2 2026-02-06: DISABLED - zero frontend usage
# from .automation import router as automation_router
automation_router = None

compare_router = APIRouter()

# Mount category routers
compare_router.include_router(baselines_router, tags=["Compare Baselines"])
compare_router.include_router(risk_router, tags=["Compare Risk"])
compare_router.include_router(lab_router, prefix="/lab", tags=["Compare Lab"])
if automation_router:
    compare_router.include_router(automation_router, tags=["Compare Automation"])

__all__ = ["compare_router"]
