"""
Analytics API Router (Consolidated Wrapper)
============================================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.routers.analytics_patterns_router import router as patterns_router
    from app.routers.analytics_materials_router import router as materials_router
    from app.routers.analytics_jobs_router import router as jobs_router
    from app.routers.analytics_advanced_router import router as advanced_router

Sub-modules:
- analytics_patterns_router.py (6 routes: complexity, rings, geometry, families, popularity, details)
- analytics_materials_router.py (6 routes: distribution, consumption, efficiency, dimensions, suppliers, inventory)
- analytics_jobs_router.py (7 routes: success-trends, duration, status, throughput, failures, types, recent)
- analytics_advanced_router.py (4 routes: correlation, anomalies/durations, anomalies/success, predict)

Total: 23 routes for analytics

LANE: UTILITY
"""

from fastapi import APIRouter

# Import sub-routers
from .analytics_patterns_router import router as patterns_router
from .analytics_materials_router import router as materials_router
from .analytics_jobs_router import router as jobs_router
from .analytics_advanced_router import router as advanced_router

# Aggregate router
router = APIRouter()

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(patterns_router)
router.include_router(materials_router)
router.include_router(jobs_router)
router.include_router(advanced_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "patterns_router",
    "materials_router",
    "jobs_router",
    "advanced_router",
]
