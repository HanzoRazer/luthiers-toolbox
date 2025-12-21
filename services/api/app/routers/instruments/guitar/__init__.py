"""
Guitar Instruments Router
=========================

Aggregates all guitar model instrument routers.

Structure:
  /api/instruments/guitar/{model_id}/...

Models (dedicated routers):
  - archtop: Jazz archtop guitar specs and templates
  - om: OM acoustic guitar specs  
  - stratocaster: Fender Stratocaster specs
  - smart: Smart Guitar IoT integration info

Dynamic Registry (all 19 models):
  - /{model_id}/spec - Specifications from registry
  - /{model_id}/geometry - Computed geometry
  - /{model_id}/info - Model overview
  - /{model_id}/assets - Asset files (for ASSETS_ONLY models)

Wave 20: Option C API Restructuring - Full Registry Coverage
"""

from fastapi import APIRouter

# Dedicated model routers (COMPLETE status or special handling)
from .archtop_instrument_router import router as archtop_router
from .om_instrument_router import router as om_router
from .stratocaster_instrument_router import router as stratocaster_router
from .smart_instrument_router import router as smart_router

# Dynamic registry routers (all 19 models)
from .registry_router import router as registry_router
from .assets_router import router as assets_router

router = APIRouter(tags=["Guitar", "Instruments"])

# Mount dedicated model routers first (higher specificity)
router.include_router(archtop_router, prefix="/archtop", tags=["Archtop"])
router.include_router(om_router, prefix="/om", tags=["OM"])
router.include_router(stratocaster_router, prefix="/stratocaster", tags=["Stratocaster"])
router.include_router(smart_router, prefix="/smart", tags=["Smart Guitar"])

# Mount registry router LAST - catches all other {model_id} patterns
# This serves /spec, /geometry, /info for ANY model in registry
router.include_router(registry_router, tags=["Registry"])

# Assets router for e2e file serving
router.include_router(assets_router, tags=["Assets"])

__all__ = ["router"]
