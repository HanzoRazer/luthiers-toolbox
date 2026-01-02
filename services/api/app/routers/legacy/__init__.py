"""
Legacy Alias Routers
====================

Backward compatibility layer for old API routes.
Forwards requests to new canonical endpoints via 308 redirects.

Phase 2 of Option C migration - keep for one release cycle.

Response Behavior:
  HTTP 308 Permanent Redirect (preserves method and body)

Wave 15 → Wave 20: Option C API Restructuring (December 2025)
"""

from fastapi import APIRouter

from .guitar_legacy_router import router as guitar_legacy_router
from .smart_guitar_legacy_router import router as smart_guitar_legacy_router
from .guitar_model_redirects import router as guitar_model_redirects_router

router = APIRouter(tags=["Legacy", "Deprecated"])

# Mount legacy routers (info endpoints)
router.include_router(guitar_legacy_router)
router.include_router(smart_guitar_legacy_router)

# Mount 308 redirect handlers for removed legacy guitar model routers
# These catch /api/guitar/{model}/cam/{model}/* → /api/cam/guitar/{model}/*
router.include_router(guitar_model_redirects_router)

__all__ = ["router"]
