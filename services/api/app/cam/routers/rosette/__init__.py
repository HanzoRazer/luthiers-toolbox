"""
CAM Rosette Routers Package
===========================

Rosette toolpath planning, G-code generation, and job management.

Sub-modules:
- rosette_toolpath_router.py (2 routes: /plan-toolpath, /post-gcode)
- rosette_jobs_router.py (2 routes: /jobs, /jobs/{job_id})

Total: 4 routes under /api/rosette/cam

Extracted from:
    - routers/art_studio_rosette_router.py (CAM endpoints only, lines 679-807)

Dependencies:
    - services/rosette_cam_bridge.py
    - services/art_jobs_store.py
"""

from fastapi import APIRouter

# Import from consolidated wrapper (backward compat)
from .cam_router import router as cam_router

# Import sub-routers directly
from .rosette_toolpath_router import router as toolpath_router
from .rosette_jobs_router import router as jobs_router

# Re-export models
from .rosette_toolpath_router import (
    RosetteToolpathPlanRequest,
    RosetteToolpathPlanResponse,
    RosettePostGcodeRequest,
    RosettePostGcodeResponse,
)
from .rosette_jobs_router import (
    RosetteCamJobCreateRequest,
    RosetteCamJobIdResponse,
    RosetteCamJobResponse,
)

# Aggregate all rosette CAM routers
router = APIRouter()
router.include_router(cam_router)

__all__ = [
    # Main router
    "router",
    "cam_router",
    # Sub-routers
    "toolpath_router",
    "jobs_router",
    # Toolpath models
    "RosetteToolpathPlanRequest",
    "RosetteToolpathPlanResponse",
    "RosettePostGcodeRequest",
    "RosettePostGcodeResponse",
    # Jobs models
    "RosetteCamJobCreateRequest",
    "RosetteCamJobIdResponse",
    "RosetteCamJobResponse",
]
