# services/api/app/rmos/api/__init__.py
"""
RMOS HTTP APIs package.

This package contains FastAPI routers that expose RMOS 2.0 features over HTTP:
- mode_preview_routes: Directional workflow mode preview
- constraint_search_routes: Constraint-first design search
- log_routes: RMOS event logging and export
- rmos_feasibility_router: Canonical feasibility endpoint (governance)
- rmos_toolpaths_router: Toolpath generation with server-side enforcement
- rmos_runs_router: Run artifact index and query API
- rmos_workflow_router: Workflow session management
"""

from .constraint_search_routes import router as constraint_search_router
from .log_routes import router as log_router
from .rmos_feasibility_router import router as feasibility_router
from .rmos_toolpaths_router import router as toolpaths_router
from .rmos_runs_router import router as runs_router
from .rmos_workflow_router import router as workflow_router

__all__ = [
    "constraint_search_router",
    "log_router",
    "feasibility_router",
    "toolpaths_router",
    "runs_router",
    "workflow_router",
]
