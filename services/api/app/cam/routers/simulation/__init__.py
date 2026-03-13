"""
CAM Simulation Routers (Consolidated)

G-code parsing and toolpath simulation.

Consolidated from 2 separate routers into simulation_consolidated_router.py:
    - gcode_sim_router (1 route)
    - upload_router (1 route)

Total: 2 routes under /api/cam/simulation
"""

from .simulation_consolidated_router import router

__all__ = ["router"]
