"""
Blueprint CAM Bridge Router Package
====================================

DXF-to-Toolpath integration layer connecting Phase 2 Blueprint vectorization
output to existing CAM systems (Adaptive Pocket Engine Module L, DXF Preflight).

Endpoints (mounted at /cam/blueprint):
- POST /reconstruct-contours: Chain LINE + SPLINE into closed loops
- POST /preflight: DXF validation before CAM processing
- POST /to-adaptive: Convert DXF to adaptive pocket toolpath
- GET/POST /pipeline-adapter/*: Pipeline to CAM conversion
- POST /preprocess/*: DXF preprocessing pipeline
- POST /geometry-correction/*: DXF dimension correction
- POST /contour-reconstruction/*: LINE/ARC to contour conversion
"""

from fastapi import APIRouter

from .blueprint_cam_core_router import (
    router as core_router,
    contour_router,
    preflight_router,
    pipeline_adapter_router,
    adaptive_router,
)
from .preprocessor_router import router as preprocessor_router
from .geometry_correction_router import router as geometry_correction_router
from .contour_reconstruction_router import router as contour_reconstruction_router

# Aggregate router with common prefix and tags
router = APIRouter(prefix="/cam/blueprint", tags=["blueprint-cam-bridge"])

# Include all sub-routers
router.include_router(core_router)
router.include_router(preprocessor_router)
router.include_router(geometry_correction_router)
router.include_router(contour_reconstruction_router)

# Re-export extraction utility for external use
from .extraction import extract_loops_from_dxf

__all__ = [
    "router",
    "extract_loops_from_dxf",
]
