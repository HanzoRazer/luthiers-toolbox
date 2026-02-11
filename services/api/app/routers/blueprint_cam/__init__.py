"""
Blueprint CAM Bridge Router Package
====================================

DXF-to-Toolpath integration layer connecting Phase 2 Blueprint vectorization
output to existing CAM systems (Adaptive Pocket Engine Module L, DXF Preflight).

Endpoints (mounted at /cam/blueprint):
- POST /reconstruct-contours: Chain LINE + SPLINE into closed loops
- POST /preflight: DXF validation before CAM processing
- POST /to-adaptive: Convert DXF to adaptive pocket toolpath

Module Structure:
- extraction.py: DXF loop extraction utilities
- contour_router.py: Contour reconstruction endpoint
- preflight_router.py: DXF validation endpoint
- adaptive_router.py: Adaptive pocket integration endpoint

Data Flow (DXF -> G-code):
1. Phase 2 vectorization -> DXF with LWPOLYLINE entities
2. extract_loops_from_dxf() -> Parse closed polylines
3. Pass to Module L.1 -> plan_adaptive_l1() for toolpath
4. to_toolpath() -> Convert to G-code moves
"""

from fastapi import APIRouter

from .contour_router import router as contour_router
from .preflight_router import router as preflight_router
from .adaptive_router import router as adaptive_router

# Aggregate router with common prefix and tags
router = APIRouter(prefix="/cam/blueprint", tags=["blueprint-cam-bridge"])

# Include all sub-routers
router.include_router(contour_router)
router.include_router(preflight_router)
router.include_router(adaptive_router)

# Re-export extraction utility for external use
from .extraction import extract_loops_from_dxf

__all__ = [
    "router",
    "extract_loops_from_dxf",
]
