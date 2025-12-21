"""
Legacy Alias Routers
====================

Backward compatibility layer for old API routes.
Forwards requests to new canonical endpoints.

Phase 2 of Option C migration - keep for one release cycle.

Response Headers:
  X-Deprecated-Route: true
  X-New-Route: <canonical endpoint>

Wave 15: Option C API Restructuring (December 2025)
"""

from fastapi import APIRouter

from .guitar_legacy_router import router as guitar_legacy_router
from .smart_guitar_legacy_router import router as smart_guitar_legacy_router

router = APIRouter(tags=["Legacy", "Deprecated"])

# Mount legacy routers
router.include_router(guitar_legacy_router)
router.include_router(smart_guitar_legacy_router)

__all__ = ["router"]
