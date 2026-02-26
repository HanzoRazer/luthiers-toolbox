# services/api/app/rmos/api/__init__.py
"""
RMOS HTTP APIs package.

This package contains FastAPI routers that expose RMOS 2.0 features over HTTP:
- logs_routes: RMOS event logging and export
- rmos_feasibility_router: Canonical feasibility endpoint (governance)
- rmos_runs_router: Run artifact index and query API
"""

from .rmos_feasibility_router import router as feasibility_router
from .rmos_runs_router import router as runs_router

__all__ = [
    "feasibility_router",
    "runs_router",
]
