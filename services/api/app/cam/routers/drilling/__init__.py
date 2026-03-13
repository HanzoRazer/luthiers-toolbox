"""
CAM Drilling Routers (Consolidated)

Modal drilling (G81, G83) and pattern drilling operations.

Consolidated from 2 separate routers into drilling_consolidated_router.py:
    - drill_router (3 routes)
    - pattern_router (2 routes)

Total: 5 routes under /api/cam/drilling
"""

from .drilling_consolidated_router import (
    router,
    drill_router,
    pattern_router,
)

__all__ = ["router", "drill_router", "pattern_router"]
