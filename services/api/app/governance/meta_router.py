"""
Meta router for introspection endpoints.

Provides the /api/_meta/routing-truth endpoint for CI gates
to validate that documented endpoints are actually mounted.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

router = APIRouter(prefix="/api/_meta", tags=["Meta", "Governance"])


def _get_routes_from_app(app: Any) -> List[Dict[str, Any]]:
    """Extract route information from the FastAPI app."""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "methods": sorted(route.methods - {"HEAD", "OPTIONS"}) if route.methods else [],
                "name": route.name or "",
                "endpoint": route.endpoint.__name__ if route.endpoint else "",
            })
    return sorted(routes, key=lambda r: r["path"])


@router.get("/routing-truth")
async def routing_truth(request: Request) -> Dict[str, Any]:
    """
    Return all mounted routes for CI validation.

    Used by scripts/check_routing_truth.py to compare
    runtime routes against services/api/app/data/endpoint_truth.json.
    """
    routes = _get_routes_from_app(request.app)
    return {
        "routes": routes,
        "count": len(routes),
    }
