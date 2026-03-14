"""
CAM Utility Routers

Split into focused sub-modules:
    - backup_router.py (3 routes)
    - benchmark_router.py (3 routes)
    - compare_router.py (1 route)
    - optimization_router.py (2 routes)
    - polygon_router.py (1 route)
    - settings_router.py (3 routes)

Total: 13 routes under /api/cam/utility

All public API is re-exported here for backward compatibility.
"""

from .utility_consolidated_router import (
    # Routers
    router,
    backup_router,
    benchmark_router,
    compare_router,
    optimization_router,
    polygon_router,
    settings_router,
    # Schemas (backward compat)
    SpiralReq,
    TrochReq,
    BenchReq,
    LoopIn,
    OptIn,
    FeedsSpeedsRequest,
    FeedsSpeedsResponse,
    PolyOffsetReq,
    MachineLimits,
    MachineCamDefaults,
    MachineIn,
    LineNumberCfg,
    PostOptions,
    PostIn,
    PresetIn,
    CamBackupIn,
)

__all__ = [
    # Routers
    "router",
    "backup_router",
    "benchmark_router",
    "compare_router",
    "optimization_router",
    "polygon_router",
    "settings_router",
    # Schemas
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
