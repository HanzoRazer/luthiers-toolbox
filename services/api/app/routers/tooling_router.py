"""Tooling and Post-Processor Management Router (Consolidated).

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from app.routers.tooling:

    from app.routers.tooling import router
    from app.routers.tooling import post_processor_router, tool_library_router

Sub-modules:
- post_processor_router.py (2 routes: /posts, /posts/{id})
- tool_library_router.py (5 routes: /library/tools, /library/materials, /library/validate)

Total: 7 routes under /api/tooling

LANE: UTILITY (machine and tool configuration)
"""
from __future__ import annotations

# Re-export router and sub-routers
from .tooling import router
from .tooling import post_processor_router, tool_library_router

# Re-export helpers for backward compatibility
from .tooling import SUPPORTED_POST_IDS, _load_posts, _post_title

__all__ = [
    "router",
    "post_processor_router",
    "tool_library_router",
    "SUPPORTED_POST_IDS",
    "_load_posts",
    "_post_title",
]
