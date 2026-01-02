"""
CAM Axis Router
===============

Canonical API for CAM operations: toolpaths, G-code, DXF export, previews.
All manufacturing operations live here.

Structure:
  /api/cam/{instrument_type}/{model_id}/...

Examples:
  /api/cam/guitar/archtop/contours
  /api/cam/guitar/stratocaster/preview
  /api/cam/guitar/om/templates

Wave 15: Option C API Restructuring (December 2025)
"""

from fastapi import APIRouter

from .guitar import router as guitar_router

router = APIRouter(tags=["CAM"])

# Mount instrument type sub-routers
router.include_router(guitar_router, prefix="/guitar", tags=["Guitar", "CAM"])

__all__ = ["router"]
