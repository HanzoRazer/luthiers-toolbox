"""
Guitar Instruments Router
=========================

Aggregates all guitar model instrument routers.

Structure:
  /api/instruments/guitar/{model_id}/...

Dynamic Registry (all 20+ models):
  - /                        - List all models
  - /smart/bundle            - Smart Guitar IoT bundle info
  - /{model_id}/spec         - Specifications from registry
  - /{model_id}/geometry     - Computed geometry
  - /{model_id}/info         - Model overview
  - /{model_id}/templates    - Available templates
  - /{model_id}/assets       - Asset files (for ASSETS_ONLY models)

Wave 20: Option C API Restructuring - Consolidated to single registry router
"""

from fastapi import APIRouter

# Dynamic registry router handles ALL models including archtop, om, stratocaster, smart
from .registry_router import router as registry_router
from .assets_router import router as assets_router

router = APIRouter(tags=["Guitar", "Instruments"])

# Registry router handles all models dynamically
# /smart/bundle is defined BEFORE /{model_id}/... routes in registry_router.py
router.include_router(registry_router, tags=["Registry"])

# Assets router for e2e file serving
router.include_router(assets_router, tags=["Assets"])

__all__ = ["router"]
