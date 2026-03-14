"""Consolidated CAM Utility Router.

Thin wrapper that re-exports from focused sub-modules:
- backup_router.py (3 routes)
- benchmark_router.py (3 routes)
- compare_router.py (1 route)
- optimization_router.py (2 routes)
- polygon_router.py (1 route)
- settings_router.py (3 routes)

Total: 13 routes for CAM utilities.
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .backup_router import router as backup_router
from .benchmark_router import router as benchmark_router
from .compare_router import router as compare_router
from .optimization_router import router as optimization_router
from .polygon_router import router as polygon_router
from .settings_router import router as settings_router

# Re-export schemas for backward compatibility
from .benchmark_router import BenchReq, SpiralReq, TrochReq
from .optimization_router import (
    FeedsSpeedsRequest,
    FeedsSpeedsResponse,
    LoopIn,
    OptIn,
)
from .polygon_router import PolyOffsetReq
from .settings_router import (
    CamBackupIn,
    LineNumberCfg,
    MachineCamDefaults,
    MachineIn,
    MachineLimits,
    PostIn,
    PostOptions,
    PresetIn,
)

# Aggregate router
router = APIRouter()
router.include_router(backup_router)
router.include_router(benchmark_router)
router.include_router(compare_router)
router.include_router(optimization_router)
router.include_router(polygon_router)
router.include_router(settings_router)

__all__ = [
    # Routers
    "router",
    "backup_router",
    "benchmark_router",
    "compare_router",
    "optimization_router",
    "polygon_router",
    "settings_router",
    # Schemas (backward compat)
    "SpiralReq",
    "TrochReq",
    "BenchReq",
    "LoopIn",
    "OptIn",
    "FeedsSpeedsRequest",
    "FeedsSpeedsResponse",
    "PolyOffsetReq",
    "MachineLimits",
    "MachineCamDefaults",
    "MachineIn",
    "LineNumberCfg",
    "PostOptions",
    "PostIn",
    "PresetIn",
    "CamBackupIn",
]
