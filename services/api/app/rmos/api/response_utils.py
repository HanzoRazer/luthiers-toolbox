"""
RMOS Response Utilities

Provides canonical response envelope helpers for consistent API responses.
"""

from typing import Any, Dict, List, Optional


def runs_list_response(
    items: Optional[List[Any]],
    *,
    next_cursor: Optional[str] = None,
    total: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Wrap a list of run artifacts in the canonical response envelope.

    Expected shape:
    {
        "items": [...],
        "next_cursor": null | "cursor_string",
        "total": <int>,
        "limit": <int>,
        "offset": <int>
    }
    """
    items = items or []
    return {
        "items": items,
        "next_cursor": next_cursor,
        "total": total if total is not None else len(items),
        "limit": limit,
        "offset": offset,
    }
