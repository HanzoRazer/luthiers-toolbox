"""Tooling Router Package (Consolidated).

Thin wrapper that re-exports from focused sub-modules:
- post_processor_router.py (2 routes)
- tool_library_router.py (5 routes)

Total: 7 routes under /api/tooling

LANE: UTILITY (machine and tool configuration)
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .post_processor_router import router as post_processor_router
from .tool_library_router import router as tool_library_router

# Re-export helpers for backward compatibility
from .post_processor_router import (
    SUPPORTED_POST_IDS,
    _load_posts,
    _post_title,
)

# Aggregate router
router = APIRouter(tags=["Tooling"])

# Mount sub-routers (no additional prefix - endpoints already have /posts and /library)
router.include_router(post_processor_router)
router.include_router(tool_library_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "post_processor_router",
    "tool_library_router",
    # Re-exports
    "SUPPORTED_POST_IDS",
    "_load_posts",
    "_post_title",
]
