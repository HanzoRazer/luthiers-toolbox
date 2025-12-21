"""
CAM Utility Routers

Settings, backup, compare, optimization, and other utilities.

Migrated from:
    - routers/cam_opt_router.py          → optimization_router.py
    - routers/cam_settings_router.py     → settings_router.py
    - routers/cam_backup_router.py       → backup_router.py
    - routers/cam_compare_diff_router.py → compare_router.py
    - routers/cam_polygon_offset_router.py → polygon_router.py
    - routers/cam_adaptive_benchmark_router.py → benchmark_router.py

Endpoints (under /api/cam/utility):
    POST /opt/what_if           - What-if optimizer
    GET  /settings/summary      - Settings summary counts
    GET  /settings/export       - Export CAM configuration
    POST /settings/import       - Import CAM configuration
    POST /backup/snapshot       - Force backup snapshot
    GET  /backup/list           - List backup files
    GET  /backup/download/{name} - Download backup file
    GET  /compare/diff          - Compare job runs
    POST /polygon_offset.nc     - Polygon offset G-code
    POST /offset_spiral.svg     - Offset spiral visualization
    POST /trochoid_corners.svg  - Trochoidal corners visualization
    POST /bench                 - Performance benchmark
"""

from fastapi import APIRouter

from .optimization_router import router as optimization_router
from .settings_router import router as settings_router
from .backup_router import router as backup_router
from .compare_router import router as compare_router
from .polygon_router import router as polygon_router
from .benchmark_router import router as benchmark_router

# Aggregate all utility routers
router = APIRouter()
router.include_router(optimization_router, prefix="/opt")
router.include_router(settings_router, prefix="/settings")
router.include_router(backup_router, prefix="/backup")
router.include_router(compare_router, prefix="/compare")
router.include_router(polygon_router)  # No prefix, uses endpoint path directly
router.include_router(benchmark_router)  # No prefix, uses endpoint path directly

__all__ = [
    "router",
    "optimization_router",
    "settings_router",
    "backup_router",
    "compare_router",
    "polygon_router",
    "benchmark_router",
]
