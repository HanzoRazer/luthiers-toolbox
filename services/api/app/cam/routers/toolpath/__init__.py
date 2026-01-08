"""
CAM Toolpath Routers

Generic toolpath operations: roughing, biarc, helical, vcarve, relief export.

Migrated from:
    - routers/cam_roughing_router.py     → roughing_router.py
    - routers/cam_biarc_router.py        → biarc_router.py
    - routers/cam_helical_v161_router.py → helical_router.py
    - routers/cam_vcarve_router.py       → vcarve_router.py
    - art_studio/relief_router.py        → relief_export_router.py (OPERATION only)

Endpoints (under /api/cam/toolpath):
    POST /roughing/gcode       - Generate rectangular roughing G-code
    GET  /roughing/info        - Get roughing operation info
    POST /biarc/gcode          - Generate contour-following G-code
    GET  /biarc/info           - Get biarc operation info
    POST /helical_entry        - Generate helical plunge G-code
    GET  /helical_health       - Health check
    POST /vcarve/preview_infill - Generate V-carve infill preview
    POST /vcarve/gcode         - Generate V-carve G-code (OPERATION)
    POST /relief/export-dxf    - Export relief geometry to DXF (OPERATION)
"""

from fastapi import APIRouter

from .roughing_router import router as roughing_router
from .biarc_router import router as biarc_router
from .helical_router import router as helical_router
from .vcarve_router import router as vcarve_router
from .relief_export_router import router as relief_export_router

# Aggregate all toolpath routers
router = APIRouter()
router.include_router(roughing_router, prefix="/roughing")
router.include_router(biarc_router, prefix="/biarc")
router.include_router(helical_router)  # No prefix, uses endpoint path directly
router.include_router(vcarve_router, prefix="/vcarve")
router.include_router(relief_export_router, prefix="/relief")

__all__ = [
    "router",
    "roughing_router",
    "biarc_router",
    "helical_router",
    "vcarve_router",
    "relief_export_router",
]
