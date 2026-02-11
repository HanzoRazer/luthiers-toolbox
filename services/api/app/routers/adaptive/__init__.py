"""
Adaptive Pocketing Router Package
=================================

Modular router package for adaptive pocket toolpath generation.

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints (mounted at /cam/pocket/adaptive):
- POST /plan: Generate toolpath from boundary loops
- POST /sim: Simulate toolpath without G-code export
- POST /gcode: Export G-code with post-processor headers/footers
- POST /batch_export: Multi-post ZIP bundle with multiple feed modes
- POST /plan_from_dxf: Upload DXF → extract geometry → generate toolpath

Module Structure:
- helpers.py: Shared helper functions (post profiles, feed translation)
- plan_router.py: Core planning (/plan, /sim)
- gcode_router.py: G-code export (/gcode)
- batch_router.py: Batch export (/batch_export)
- dxf_router.py: DXF upload bridge (/plan_from_dxf)
"""

from fastapi import APIRouter

from .plan_router import router as plan_router
from .gcode_router import router as gcode_router
from .batch_router import router as batch_router
from .dxf_router import router as dxf_router

# Aggregate router with common prefix and tags
router = APIRouter(prefix="/cam/pocket/adaptive", tags=["cam-adaptive"])

# Include all sub-routers
router.include_router(plan_router)
router.include_router(gcode_router)
router.include_router(batch_router)
router.include_router(dxf_router)

__all__ = ["router"]
