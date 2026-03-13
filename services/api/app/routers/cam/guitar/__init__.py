"""
Guitar CAM Router (Consolidated)
=================================

Aggregates all guitar model CAM routers.

Structure:
  /api/cam/guitar/{model_id}/...

Models (consolidated in guitar_models_consolidated_router.py):
  - archtop: Archtop contour generation, bridge fitting, saddle
  - om: OM graduation maps, CNC kits
  - stratocaster: Body routing, cavity templates, BOM

Dynamic Registry (all 19 models):
  - /{model_id}/health       - CAM health check
  - /{model_id}/capabilities - Available operations
  - /{model_id}/templates    - CAM templates
  - /{model_id}/contours/*   - Contour generation
  - /{model_id}/toolpaths/*  - Toolpath generation

Wave 20: Option C API Restructuring - Full Registry Coverage
Wave 27.2: Restored archtop, om, stratocaster, registry routers.
Wave 28: Consolidated archtop + om + stratocaster into single router.
"""

from fastapi import APIRouter

# Consolidated model routers (archtop, om, stratocaster)
from .guitar_models_consolidated_router import (
    router as models_router,
    archtop_router,
    om_router,
    stratocaster_router,
)

# Dynamic registry router (all 19 models)
from .registry_cam_router import router as registry_router

router = APIRouter(tags=["Guitar", "CAM"])

# Mount consolidated model routers first (higher specificity)
router.include_router(models_router)

# Mount registry router LAST — catches all other {model_id} patterns.
# This serves CAM stubs for ANY model in the instrument registry.
router.include_router(registry_router, tags=["Registry", "CAM"])

__all__ = ["router", "archtop_router", "om_router", "stratocaster_router"]
