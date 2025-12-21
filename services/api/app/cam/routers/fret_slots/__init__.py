"""
CAM Fret Slots Routers

Fret slot CAM preview and multi-post export.

Migrated from:
    - routers/cam_fret_slots_router.py       → preview_router (proxy)
    - routers/cam_fret_slots_export_router.py → export_router (proxy)

Note: Proxies to existing routers until full migration.
"""

from fastapi import APIRouter

# Proxy imports from existing routers (transitional)
try:
    from ....routers.cam_fret_slots_router import router as preview_router
except ImportError:
    preview_router = None

try:
    from ....routers.cam_fret_slots_export_router import router as export_router
except ImportError:
    export_router = None

# Aggregate all fret_slots routers
router = APIRouter()

if preview_router:
    router.include_router(preview_router)
if export_router:
    router.include_router(export_router)

__all__ = ["router"]
