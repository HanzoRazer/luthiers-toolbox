"""
Optional helper to mount auxiliary saw lab routers from one place.
If you already mount saw_lab.batch_router.router elsewhere, you can
include execution_lifecycle_router.router there instead of using this.
"""

from __future__ import annotations

from fastapi import APIRouter

from .batch_router import router as batch_router
from .batch_query_router import router as batch_query_router
from .batch_learning_router import router as batch_learning_router
from .batch_metrics_router import router as batch_metrics_router
from .batch_gcode_router import router as batch_gcode_router
# Consolidated metrics lookup router (3 routes)
# Replaces: metrics_lookup, latest_batch_chain, metrics_latest_by_execution
from .metrics_lookup_consolidated_router import router as metrics_lookup_consolidated_router
# Consolidated toolpaths router (5 routes)
# Replaces: toolpaths_lookup, toolpaths_validate, toolpaths_lint, toolpaths_download
from .toolpaths_router import router as toolpaths_router

# Consolidated execution lifecycle router (7 routes)
# Replaces: execution_abort, execution_complete, execution_confirmation,
#           execution_metrics, execution_start_from_toolpaths, execution_status
from .execution_lifecycle_router import router as execution_lifecycle_router


router = APIRouter()
router.include_router(batch_router)
router.include_router(batch_query_router)
router.include_router(batch_learning_router)
router.include_router(batch_metrics_router)
router.include_router(batch_gcode_router)
router.include_router(metrics_lookup_consolidated_router)
router.include_router(toolpaths_router)
router.include_router(execution_lifecycle_router)
