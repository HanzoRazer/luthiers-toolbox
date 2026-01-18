"""
Optional helper to mount auxiliary saw lab routers from one place.
If you already mount saw_lab.batch_router.router elsewhere, you can
include execution_metrics_router.router there instead of using this.
"""

from __future__ import annotations

from fastapi import APIRouter

from .batch_router import router as batch_router
from .execution_metrics_router import router as execution_metrics_router
from .metrics_lookup_router import router as metrics_lookup_router
from .latest_batch_chain_router import router as latest_batch_chain_router
from .metrics_latest_by_execution_router import router as metrics_latest_by_execution_router
from .toolpaths_lookup_router import router as toolpaths_lookup_router
from .toolpaths_validate_router import router as toolpaths_validate_router


router = APIRouter()
router.include_router(batch_router)
router.include_router(execution_metrics_router)
router.include_router(metrics_lookup_router)
router.include_router(latest_batch_chain_router)
router.include_router(metrics_latest_by_execution_router)
router.include_router(toolpaths_lookup_router)
router.include_router(toolpaths_validate_router)
