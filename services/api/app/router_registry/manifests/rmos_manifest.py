"""RMOS domain routers."""

from typing import List

from ..models import RouterSpec

RMOS_ROUTERS: List[RouterSpec] = [
    RouterSpec(
        module="app.rmos",
        router_attr="rmos_router",
        prefix="/api/rmos",
        tags=["RMOS"],
        required=True,
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.api_runs",
        prefix="/api/rmos",
        tags=["RMOS", "Runs"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.advisory_router",
        prefix="/api/rmos",
        tags=["RMOS", "Advisory"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.exports",
        prefix="",
        tags=["RMOS", "Operator Pack"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.router_query",
        prefix="/api/rmos",
        tags=["RMOS", "Runs v2 Query"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.api.rmos_runs_router",
        prefix="",
        tags=["RMOS", "Runs API"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.api.logs_routes",
        prefix="/api/rmos",
        tags=["RMOS", "Logs v2"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.rosette_cam_router",
        prefix="/api/rmos",
        tags=["RMOS", "Rosette", "CAM"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.safety_router",
        prefix="/api/rmos",
        tags=["RMOS", "Safety"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.live_monitor_router",
        prefix="/api/rmos",
        tags=["RMOS", "Live Monitor"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.mvp_router",
        prefix="/api/rmos",
        tags=["RMOS", "MVP"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.analytics.router",
        prefix="/api/rmos",
        tags=["RMOS", "Analytics"],
        category="rmos",
    ),
    RouterSpec(
        module="app.routers.strip_family_router",
        prefix="/api/rmos",
        tags=["RMOS", "Strip Families"],
        category="misc",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.acoustics_router",
        prefix="/api/rmos/acoustics",
        tags=["RMOS", "Acoustics"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.validation.router",
        prefix="",
        tags=["RMOS", "Validation"],
        category="rmos",
    ),
]
