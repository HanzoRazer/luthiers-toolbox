"""Vision Producer Plane - Canonical API for AI Image Generation (Consolidated).

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.vision.generation_router import router as generation_router
    from app.vision.segmentation_router import router as segmentation_router

Sub-modules:
- generation_router.py (5 routes: /providers, /generate, /vocabulary, /prompt, /feedback)
- segmentation_router.py (2 routes: /segment, /photo-to-gcode)

Total: 7 routes under /api/vision

LANE: PRODUCER (generates/analyzes assets via AI, writes to CAS)
The Ledger Plane (RMOS) handles attach/review/promote governance.
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .generation_router import router as generation_router
from .segmentation_router import router as segmentation_router
from .analyze_generated_router import router as analyze_generated_router

# Re-export schemas for backward compatibility
from .schemas import (
    VisionAsset,
    VisionGenerateRequest,
    VisionGenerateResponse,
    VisionPromptPreviewRequest,
    VisionPromptPreviewResponse,
    VisionVocabularyResponse,
    SegmentResponse,
    PhotoToGcodeResponse,
)

# Re-export helpers for backward compatibility
from .generation_router import ProvidersResponse, _blob_download_url

# Aggregate router
router = APIRouter(prefix="/api/vision", tags=["Vision"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(generation_router)
router.include_router(segmentation_router)
router.include_router(analyze_generated_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "generation_router",
    "segmentation_router",
    "analyze_generated_router",
    # Schemas
    "VisionAsset",
    "VisionGenerateRequest",
    "VisionGenerateResponse",
    "VisionPromptPreviewRequest",
    "VisionPromptPreviewResponse",
    "VisionVocabularyResponse",
    "SegmentResponse",
    "PhotoToGcodeResponse",
    # Helpers
    "ProvidersResponse",
    "_blob_download_url",
]
