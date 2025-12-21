"""
CAM Pipeline Routers

Pipeline execution and preset management.

Migrated from:
    - routers/cam_pipeline_router.py     → run_router (proxy)
    - routers/cam_pipeline_preset_run_router.py → presets_router (proxy)

Note: Proxies to existing routers until full migration.
"""

from fastapi import APIRouter

# Proxy imports from existing routers (transitional)
try:
    from ....routers.cam_pipeline_router import router as run_router
except ImportError:
    run_router = None

try:
    from ....routers.cam_pipeline_preset_run_router import router as presets_router
except ImportError:
    presets_router = None

# Aggregate all pipeline routers
router = APIRouter()

if run_router:
    router.include_router(run_router)
if presets_router:
    router.include_router(presets_router)

__all__ = ["router"]
