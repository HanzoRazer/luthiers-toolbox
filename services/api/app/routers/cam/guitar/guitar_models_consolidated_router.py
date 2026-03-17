"""Guitar Models CAM Routers (Consolidated)

Thin wrapper that re-exports from focused sub-modules:
- archtop_cam_router.py (5 routes)
- om_cam_router.py (4 routes)
- stratocaster_cam_router.py (4 routes)
- flying_v_cam_router.py (5 routes — FV-GAP-05, FV-GAP-10)

Total: 18 routes under /api/cam/guitar/{model}

LANE: UTILITY (template/asset operations)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
    Archtop (/archtop):
        POST /contours/csv      - Generate contours from CSV
        POST /contours/outline  - Generate contours from DXF
        POST /fit               - Calculate bridge fit parameters
        POST /bridge            - Generate floating bridge DXF
        POST /saddle            - Generate compensated saddle profile

    OM (/om):
        GET /templates          - List DXF templates
        GET /graduation         - Get graduation maps
        GET /kits               - List CNC kits
        GET /download/{path}    - Download template file

    Stratocaster (/stratocaster):
        GET /templates          - List DXF templates
        GET /bom                - Bill of materials
        GET /preview            - SVG preview
        GET /download/{path}    - Download template file

    Flying V (/flying_v):
        GET /spec               - Spec summary (cavity dimensions)
        POST /toolpath/control_cavity  - Control cavity pocket G-code
        POST /toolpath/neck_pocket     - Neck pocket mortise G-code
        POST /toolpath/pickup          - Pickup cavity G-code
        POST /validate                 - Depth validation (with preflight)

Wave 15/20: Option C API Restructuring
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .archtop_cam_router import router as archtop_router
from .om_cam_router import router as om_router
from .stratocaster_cam_router import router as stratocaster_router
from .flying_v_cam_router import router as flying_v_router

# Re-export schemas for backward compatibility
from .archtop_cam_router import (
    ArchtopBridgeRequest,
    ArchtopContourCSVRequest,
    ArchtopContourOutlineRequest,
    ArchtopFitRequest,
    ArchtopSaddleRequest,
)
from .om_cam_router import (
    OM_BASE,
    OMGraduationMap,
    OMKit,
    OMTemplate,
)
from .stratocaster_cam_router import (
    STRAT_BASE,
    StratocasterBOMItem,
    StratocasterBOMResponse,
)

# Aggregate router
router = APIRouter(tags=["Guitar", "CAM"])
router.include_router(archtop_router, prefix="/archtop", tags=["Archtop", "CAM"])
router.include_router(om_router, prefix="/om", tags=["OM", "CAM"])
router.include_router(stratocaster_router, prefix="/stratocaster", tags=["Stratocaster", "CAM"])
router.include_router(flying_v_router, prefix="/flying_v", tags=["Flying V", "CAM"])

__all__ = [
    # Routers
    "router",
    "archtop_router",
    "om_router",
    "stratocaster_router",
    "flying_v_router",
    # Archtop schemas
    "ArchtopContourCSVRequest",
    "ArchtopContourOutlineRequest",
    "ArchtopFitRequest",
    "ArchtopBridgeRequest",
    "ArchtopSaddleRequest",
    # OM schemas
    "OM_BASE",
    "OMTemplate",
    "OMGraduationMap",
    "OMKit",
    # Stratocaster schemas
    "STRAT_BASE",
    "StratocasterBOMItem",
    "StratocasterBOMResponse",
]
