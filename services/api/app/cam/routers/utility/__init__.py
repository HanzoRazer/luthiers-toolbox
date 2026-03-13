"""
CAM Utility Routers (Consolidated)

Settings, backup, compare, optimization, and other utilities.

Consolidated from 6 separate routers into utility_consolidated_router.py:
    - backup_router (3 routes)
    - benchmark_router (3 routes)
    - compare_router (1 route)
    - optimization_router (2 routes)
    - polygon_router (1 route)
    - settings_router (3 routes)

Total: 13 routes under /api/cam/utility
"""

from .utility_consolidated_router import (
    router,
    backup_router,
    benchmark_router,
    compare_router,
    optimization_router,
    polygon_router,
    settings_router,
)

__all__ = [
    "router",
    "backup_router",
    "benchmark_router",
    "compare_router",
    "optimization_router",
    "polygon_router",
    "settings_router",
]
