"""
Guitar CAM Router
=================

Aggregates all guitar model CAM routers.

Structure:
  /api/cam/guitar/{model_id}/...

Models (dedicated routers):
  - archtop: Archtop contour generation, bridge fitting, saddle
  - om: OM graduation maps, CNC kits
  - stratocaster: Body routing, cavity templates, BOM
  - smart: (stub — not yet implemented)

Dynamic Registry (all 19 models):
  - /{model_id}/health       - CAM health check
  - /{model_id}/capabilities - Available operations
  - /{model_id}/templates    - CAM templates
  - /{model_id}/contours/*   - Contour generation
  - /{model_id}/toolpaths/*  - Toolpath generation

Wave 20: Option C API Restructuring - Full Registry Coverage
Recovery Wave 27.2: Restored archtop, om, stratocaster, registry routers.
smart_cam_router removed (DISCARD — no unique logic).
"""

from fastapi import APIRouter

# Dedicated model routers (restored from __RECOVERED__ Wave 27.2)
from .archtop_cam_router import router as archtop_router
from .om_cam_router import router as om_router
from .stratocaster_cam_router import router as stratocaster_router

# Dynamic registry router (all 19 models)
from .registry_cam_router import router as registry_router

router = APIRouter(tags=["Guitar", "CAM"])

# Mount dedicated model routers first (higher specificity)
router.include_router(archtop_router,    prefix="/archtop",     tags=["Archtop", "CAM"])
router.include_router(om_router,         prefix="/om",          tags=["OM", "CAM"])
router.include_router(stratocaster_router, prefix="/stratocaster", tags=["Stratocaster", "CAM"])

# Mount registry router LAST — catches all other {model_id} patterns.
# This serves CAM stubs for ANY model in the instrument registry.
router.include_router(registry_router, tags=["Registry", "CAM"])

__all__ = ["router"]
