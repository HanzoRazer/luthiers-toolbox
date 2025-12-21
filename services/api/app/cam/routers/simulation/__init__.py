"""
CAM Simulation Routers

G-code parsing and toolpath simulation.

Migrated from:
    - routers/cam_sim_router.py      → gcode_sim_router.py
    - routers/cam_simulate_router.py → upload_router.py

Endpoints (under /api/cam/simulation):
    POST /simulate_gcode    - Simulate inline G-code
    POST /upload            - Upload and simulate G-code file
"""

from fastapi import APIRouter

from .gcode_sim_router import router as gcode_sim_router
from .upload_router import router as upload_router

# Aggregate all simulation routers
router = APIRouter()
router.include_router(gcode_sim_router)
router.include_router(upload_router)

__all__ = ["router", "gcode_sim_router", "upload_router"]
