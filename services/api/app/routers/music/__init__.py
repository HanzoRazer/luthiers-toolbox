"""
Music Axis Router
=================

Canonical API for music theory: temperaments, tunings, scales.
Shared across all instrument types.

Structure:
  /api/music/temperament/...

Examples:
  /api/music/temperament/health
  /api/music/temperament/compare
  /api/music/temperament/systems

Wave 15: Option C API Restructuring (December 2025)
"""

from fastapi import APIRouter

from .temperament_router import router as temperament_router

router = APIRouter(tags=["Music"])

# Mount music sub-routers
router.include_router(temperament_router, prefix="/temperament", tags=["Temperaments"])

__all__ = ["router"]
