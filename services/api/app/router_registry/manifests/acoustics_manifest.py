"""Acoustics domain router manifest."""
from ..models import RouterSpec

ACOUSTICS_ROUTERS = [
    RouterSpec(
        module="app.routers.acoustics.plate_router",
        prefix="/api/acoustics/plate",
        router_attr="router",
        tags=["acoustics-plate"],
        category="acoustics",
    ),
]
