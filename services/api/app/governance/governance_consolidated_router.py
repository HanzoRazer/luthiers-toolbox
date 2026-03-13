"""
Governance Router (Consolidated)
=================================

API governance endpoints for introspection and metrics.

Consolidated from:
    - meta_router.py (routing truth endpoint)
    - metrics_router.py (prometheus metrics)

Endpoints:
    GET /api/_meta/routing-truth  - List all mounted routes
    GET /api/_meta/metrics        - Prometheus exposition
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute

from .endpoint_stats import snapshot_prometheus_text
from ..observability.metrics import render_prometheus as render_rmos_cam_metrics


router = APIRouter(prefix="/api/_meta", tags=["Meta", "Governance"])


# ===========================================================================
# ROUTING TRUTH ENDPOINTS
# ===========================================================================

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


# ===========================================================================
# METRICS ENDPOINTS
# ===========================================================================

def _enabled() -> bool:
    v = (os.getenv("ENDPOINT_METRICS_ENABLED") or "true").strip().lower()
    return v not in {"0", "false", "no", "off"}


def _rmos_metrics_enabled() -> bool:
    v = (os.getenv("RMOS_METRICS_ENABLED") or "true").strip().lower()
    return v not in {"0", "false", "no", "off"}


@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus exposition endpoint.

    Env:
      ENDPOINT_METRICS_ENABLED=true|false
      ENDPOINT_METRICS_MAX_SERIES=2000            # cap series
      ENDPOINT_METRICS_OTHER_LABEL=__other__      # overflow bucket
      ENDPOINT_OTEL_ENABLED=true|false            # optional OTEL emission elsewhere
      RMOS_METRICS_ENABLED=true|false             # H7.2.2 CAM endpoint metrics
    """
    if not _enabled():
        return PlainTextResponse("# metrics disabled\n", status_code=404)

    parts = [snapshot_prometheus_text()]

    # H7.2.2: Append RMOS CAM endpoint metrics if enabled
    if _rmos_metrics_enabled():
        parts.append(render_rmos_cam_metrics())

    return PlainTextResponse("".join(parts), media_type="text/plain; version=0.0.4")


__all__ = ["router"]
