"""
Router Truth Endpoint - Runtime route table introspection.

Dumps the actual mounted routes at runtime so you can confirm
which lane is actually mounted after deploy.

Usage:
    curl http://localhost:8000/api/_meta/routing-truth | jq '.deprecated_count'
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from starlette.routing import Route

router = APIRouter(prefix="/api/_meta", tags=["_meta"])


def _is_deprecated_path(path: str) -> Optional[str]:
    """
    Returns a reason string if deprecated, else None.
    """
    if path.startswith("/api/art-studio"):
        return "legacy_art_studio_lane"
    if path.startswith("/rosette"):
        return "transitional_no_api_prefix_lane"
    return None


@router.get("/routing-truth")
async def routing_truth(request: Request) -> Dict[str, Any]:
    """
    "Routing Truth" Audit endpoint.

    Returns the concrete runtime route table as seen by FastAPI, so you can
    confirm which lane is actually mounted after deploy.

    This is intentionally lightweight and read-only.
    """
    app = request.app
    items: List[Dict[str, Any]] = []

    for r in app.routes:
        if not isinstance(r, Route):
            continue

        path = getattr(r, "path", "")
        methods = sorted(list(getattr(r, "methods", []) or []))
        name = getattr(r, "name", None)

        deprecated_reason = _is_deprecated_path(path)

        items.append(
            {
                "path": path,
                "methods": methods,
                "name": name,
                "deprecated": bool(deprecated_reason),
                "deprecated_reason": deprecated_reason,
            }
        )

    # stable ordering helps diffing
    items.sort(key=lambda x: (x["path"], ",".join(x["methods"])))

    return {
        "count": len(items),
        "deprecated_count": sum(1 for x in items if x["deprecated"]),
        "routes": items,
    }
