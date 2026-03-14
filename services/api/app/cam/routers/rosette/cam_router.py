"""
Rosette CAM Router (Consolidated Wrapper)
=========================================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.cam.routers.rosette.rosette_toolpath_router import router as toolpath_router
    from app.cam.routers.rosette.rosette_jobs_router import router as jobs_router

Sub-modules:
- rosette_toolpath_router.py (2 routes: /plan-toolpath, /post-gcode)
- rosette_jobs_router.py (2 routes: /jobs, /jobs/{job_id})

Total: 4 routes under /api/rosette/cam

LANE: OPERATION (toolpath) / UTILITY (jobs)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
"""

from fastapi import APIRouter

# Import sub-routers
from .rosette_toolpath_router import router as toolpath_router
from .rosette_jobs_router import router as jobs_router

# Re-export models for backward compatibility
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

# Aggregate router
router = APIRouter(tags=["Rosette CAM"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(toolpath_router)
router.include_router(jobs_router)


__all__ = [
    # Router
    "router",
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
