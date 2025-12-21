"""
CAM Rosette Routers

Rosette toolpath planning, G-code generation, and job management.

Extracted from:
    - routers/art_studio_rosette_router.py (CAM endpoints only, lines 679-807)

Dependencies:
    - services/rosette_cam_bridge.py
    - services/art_jobs_store.py

Endpoints:
    POST /plan-toolpath     - Generate toolpath moves
    POST /post-gcode        - Convert moves to G-code
    POST /jobs              - Create CAM job for pipeline
    GET  /jobs/{job_id}     - Get CAM job details
"""

from fastapi import APIRouter

from .cam_router import router as cam_router

# Aggregate all rosette CAM routers
router = APIRouter()
router.include_router(cam_router)

__all__ = ["router", "cam_router"]
