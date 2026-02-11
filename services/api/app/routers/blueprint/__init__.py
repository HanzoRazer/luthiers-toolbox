"""
Blueprint Router Package
========================

AI-Powered Blueprint Digitization System integrating Claude Sonnet 4 AI
for dimensional analysis (Phase 1) with OpenCV computer vision for
intelligent geometry extraction (Phase 2).

Endpoints (mounted at /blueprint):
- POST /analyze: AI dimensional analysis with Claude Sonnet 4
- POST /to-svg: Export annotated SVG with dimensions
- POST /to-dxf: DXF export (placeholder, use /vectorize-geometry)
- POST /vectorize-geometry: OpenCV edge detection + DXF/SVG export

Module Structure:
- constants.py: Validation constants, service imports, feature flags
- phase1_router.py: AI analysis (/analyze, /to-svg)
- phase2_router.py: OpenCV vectorization (/to-dxf, /vectorize-geometry)

Data Flow (Blueprint -> CAM):
1. Upload PDF/image -> /analyze (Claude extracts scale + dimensions)
2. AI analysis -> /to-svg (Phase 1 annotated SVG with measurements)
3. Same image -> /vectorize-geometry (OpenCV detects edges/contours)
4. DXF output -> blueprint_cam_bridge.py -> extract_loops_from_dxf()
5. LWPOLYLINE loops -> adaptive pocketing -> toolpath generation
"""

from fastapi import APIRouter

from .phase1_router import router as phase1_router
from .phase2_router import router as phase2_router

# Aggregate router with common prefix and tags
router = APIRouter(prefix="/blueprint", tags=["blueprint"])

# Include all sub-routers
router.include_router(phase1_router)
router.include_router(phase2_router)

# Re-export feature flags for external use
from .constants import (
    ANALYZER_AVAILABLE,
    VECTORIZER_AVAILABLE,
    PHASE2_AVAILABLE,
)

__all__ = [
    "router",
    "ANALYZER_AVAILABLE",
    "VECTORIZER_AVAILABLE",
    "PHASE2_AVAILABLE",
]
