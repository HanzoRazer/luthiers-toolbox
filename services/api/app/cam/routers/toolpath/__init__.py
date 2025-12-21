"""
CAM Toolpath Routers

Generic toolpath operations: roughing, biarc, helical, vcarve.

Migrated from:
    - routers/cam_roughing_router.py
    - routers/cam_biarc_router.py
    - routers/cam_helical_v161_router.py
    - routers/cam_vcarve_router.py
"""

from fastapi import APIRouter

router = APIRouter()

# Router will be populated during Phase 3.3 migration

__all__ = ["router"]
