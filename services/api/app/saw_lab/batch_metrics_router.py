"""
Saw Lab Batch Metrics Router (Consolidated Wrapper)
====================================================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.saw_lab.batch_metrics_execution_router import router as execution_router
    from app.saw_lab.batch_metrics_decision_router import router as decision_router
    from app.saw_lab.batch_metrics_diff_router import router as diff_router

Sub-modules:
- batch_metrics_execution_router.py (7 routes: execution rollups)
- batch_metrics_decision_router.py (5 routes: decision rollups, trends, CSV)
- batch_metrics_diff_router.py (1 route: rollup diff)

Total: 13 routes under /api/saw/batch

LANE: UTILITY
"""

from fastapi import APIRouter

# Import sub-routers
from .batch_metrics_execution_router import router as execution_router
from .batch_metrics_decision_router import router as decision_router
from .batch_metrics_diff_router import router as diff_router

# Re-export helper functions for backward compatibility
from .batch_metrics_execution_router import _compute_execution_rollup
from .batch_metrics_decision_router import _compute_decision_rollup

# Aggregate router
router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(execution_router)
router.include_router(decision_router)
router.include_router(diff_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "execution_router",
    "decision_router",
    "diff_router",
    # Helpers (backward compat)
    "_compute_execution_rollup",
    "_compute_decision_rollup",
]
