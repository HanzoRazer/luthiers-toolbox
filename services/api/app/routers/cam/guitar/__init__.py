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

GEN-4 Body G-code (project-driven):
  - /stratocaster/body/gcode - Strat body from project
  - /les_paul/body/gcode     - LP body from project
  - /flying_v/body/gcode     - Flying V from project
  - /{model_id}/neck/gcode   - Neck G-code from project

Wave 20: Option C API Restructuring - Full Registry Coverage
Wave 27.2: Restored archtop, om, stratocaster, registry routers.
Wave 28: Consolidated archtop + om + stratocaster into single router.
Wave 29: GEN-4 body_gcode_router added.
"""

from fastapi import APIRouter

# Consolidated model routers (archtop, om, stratocaster, flying_v)
from .guitar_models_consolidated_router import (
    router as models_router,
    archtop_router,
    om_router,
    stratocaster_router,
    flying_v_router,
)

# Body G-code router (GEN-4) - project-driven CAM generation
from .body_gcode_router import router as body_gcode_router

# Dynamic registry router (all 19 models)
from .registry_cam_router import router as registry_router

router = APIRouter(tags=["Guitar", "CAM"])

# Mount consolidated model routers first (higher specificity)
router.include_router(models_router)

# Mount body G-code router (GEN-4) - before registry to take precedence
router.include_router(body_gcode_router, tags=["G-code", "GEN-4"])

# Mount registry router LAST — catches all other {model_id} patterns.
# This serves CAM stubs for ANY model in the instrument registry.
router.include_router(registry_router, tags=["Registry", "CAM"])

__all__ = ["router", "archtop_router", "om_router", "stratocaster_router", "flying_v_router", "body_gcode_router"]
