"""
Instruments Axis Router
=======================

Canonical API for instrument specifications, geometry, and templates.
All non-CAM instrument data lives here.

Structure:
  /api/instruments/{instrument_type}/{model_id}/...

Examples:
  /api/instruments/guitar/archtop/spec
  /api/instruments/guitar/stratocaster/geometry
  /api/instruments/guitar/smart/info

Wave 15: Option C API Restructuring (December 2025)
"""

from fastapi import APIRouter

from .guitar import router as guitar_router

router = APIRouter(tags=["Instruments"])

# Mount instrument type sub-routers
router.include_router(guitar_router, prefix="/guitar", tags=["Guitar"])

__all__ = ["router"]
