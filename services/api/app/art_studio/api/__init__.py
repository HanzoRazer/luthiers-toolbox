"""Art Studio API Routes - Bundle 31.0 + Phase 5 Consolidation"""

from .pattern_routes import router as pattern_router
from .generator_routes import router as generator_router
from .preview_routes import router as preview_router
from .snapshot_routes import router as snapshot_router

# Phase 5: Consolidated rosette routes
from .rosette_jobs_routes import router as rosette_jobs_router
from .rosette_compare_routes import router as rosette_compare_router
from .rosette_pattern_routes import router as rosette_pattern_router

__all__ = [
    "pattern_router",
    "generator_router",
    "preview_router",
    "snapshot_router",
    # Phase 5: Consolidated rosette routes
    "rosette_jobs_router",
    "rosette_compare_router",
    "rosette_pattern_router",
]
