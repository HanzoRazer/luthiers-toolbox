"""
CAM Router Aggregator

Combines all CAM category routers into a single router for clean
main.py registration. Each category gets its own prefix under /api/cam/.

Example:
    from app.cam.routers import cam_router
    app.include_router(cam_router, prefix="/api/cam", tags=["CAM"])

This creates endpoints like:
    POST /api/cam/drilling/gcode
    POST /api/cam/toolpath/roughing
    POST /api/cam/rosette/plan-toolpath
    etc.
"""

from fastapi import APIRouter

# Import category routers (will be populated as migration progresses)
# Each category __init__.py exports a 'router' that combines its endpoints

# Phase 3.1: Utility
try:
    from .utility import router as utility_router
except ImportError:
    utility_router = None

# Phase 3.2: Monitoring
try:
    from .monitoring import router as monitoring_router
except ImportError:
    monitoring_router = None

# Phase 3.3: Toolpath
try:
    from .toolpath import router as toolpath_router
except ImportError:
    toolpath_router = None

# Phase 3.4: Drilling
try:
    from .drilling import router as drilling_router
except ImportError:
    drilling_router = None

# Phase 3.5: Simulation
try:
    from .simulation import router as simulation_router
except ImportError:
    simulation_router = None

# Phase 3.6: Export
try:
    from .export import router as export_router
except ImportError:
    export_router = None

# Phase 3.7: Relief
try:
    from .relief import router as relief_router
except ImportError:
    relief_router = None

# Phase 3.8: Risk
try:
    from .risk import router as risk_router
except ImportError:
    risk_router = None

# Phase 3.9: Fret Slots
try:
    from .fret_slots import router as fret_slots_router
except ImportError:
    fret_slots_router = None

# Phase 3.10: Pipeline
try:
    from .pipeline import router as pipeline_router
except ImportError:
    pipeline_router = None

# Phase 2: Rosette CAM
try:
    from .rosette import router as rosette_router
except ImportError:
    rosette_router = None


# =============================================================================
# AGGREGATOR ROUTER
# =============================================================================

cam_router = APIRouter()

# Register all available category routers
if drilling_router:
    cam_router.include_router(drilling_router, prefix="/drilling", tags=["CAM Drilling"])

if fret_slots_router:
    cam_router.include_router(fret_slots_router, prefix="/fret_slots", tags=["CAM Fret Slots"])

if relief_router:
    cam_router.include_router(relief_router, prefix="/relief", tags=["CAM Relief"])

if risk_router:
    cam_router.include_router(risk_router, prefix="/risk", tags=["CAM Risk"])

if rosette_router:
    cam_router.include_router(rosette_router, prefix="/rosette", tags=["CAM Rosette"])

if simulation_router:
    cam_router.include_router(simulation_router, prefix="/simulation", tags=["CAM Simulation"])

if toolpath_router:
    cam_router.include_router(toolpath_router, prefix="/toolpath", tags=["CAM Toolpath"])

if export_router:
    cam_router.include_router(export_router, prefix="/export", tags=["CAM Export"])

if monitoring_router:
    cam_router.include_router(monitoring_router, prefix="/monitoring", tags=["CAM Monitoring"])

if pipeline_router:
    cam_router.include_router(pipeline_router, prefix="/pipeline", tags=["CAM Pipeline"])

if utility_router:
    cam_router.include_router(utility_router, prefix="/utility", tags=["CAM Utility"])


__all__ = ["cam_router"]
