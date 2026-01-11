"""
Optional helper to mount auxiliary saw lab routers from one place.
If you already mount saw_lab.batch_router.router elsewhere, you can
include execution_metrics_router.router there instead of using this.
"""

from __future__ import annotations

from fastapi import APIRouter

from .batch_router import router as batch_router
from .execution_metrics_router import router as execution_metrics_router


router = APIRouter()
router.include_router(batch_router)
router.include_router(execution_metrics_router)
