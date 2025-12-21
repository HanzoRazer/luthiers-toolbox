"""
CAM Relief Carving Routers

Heightmap loading, roughing, and finishing operations.

Migrated from:
    - routers/cam_relief_router.py     → toolpath_router (proxy)
    - routers/cam_relief_v160_router.py → preview_router (proxy)

Note: Proxies to existing routers until full migration.
"""

from fastapi import APIRouter

# Proxy imports from existing routers (transitional)
try:
    from ....routers.cam_relief_router import router as toolpath_router
except ImportError:
    toolpath_router = None

try:
    from ....routers.cam_relief_v160_router import router as preview_router
except ImportError:
    preview_router = None

# Aggregate all relief routers
router = APIRouter()

if toolpath_router:
    router.include_router(toolpath_router)
if preview_router:
    router.include_router(preview_router)

__all__ = ["router"]
