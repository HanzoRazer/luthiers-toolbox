"""
Geometry Router Package
=======================

Aggregates all geometry routers for import/export operations.

Endpoints:
  POST /import           - Parse DXF/SVG/JSON to canonical format
  POST /parity           - Validate design vs toolpath accuracy
  POST /export           - Single format export (DXF or SVG)
  POST /export_gcode     - G-code with post-processor headers/footers
  POST /export_gcode_governed - G-code with RMOS artifact persistence
  POST /export_bundle    - Single post bundle (DXF + SVG + NC)
  POST /export_bundle_multi - Multi-post bundle (N x NC files)

Wave 20: Decomposition from geometry_router.py (1,100 lines -> 5 files)
"""

from fastapi import APIRouter

from .import_router import router as import_router
from .export_router import router as export_router
from .bundle_router import router as bundle_router

router = APIRouter(tags=["geometry"])

# Include sub-routers
router.include_router(import_router)
router.include_router(export_router)
router.include_router(bundle_router)

__all__ = ["router"]
