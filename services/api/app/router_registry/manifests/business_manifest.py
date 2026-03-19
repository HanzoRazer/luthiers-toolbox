"""Business, Blueprint, and Instruments routers."""

from typing import List

from ..models import RouterSpec

BUSINESS_ROUTERS: List[RouterSpec] = [
    RouterSpec(
        module="app.routers.blueprint",
        prefix="/api",
        tags=["Blueprint"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.routers.blueprint_cam",
        prefix="/api",
        tags=["Blueprint CAM Bridge"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.routers.legacy_dxf_exports_router",
        prefix="",
        tags=["DXF", "Exports"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.blueprint.save_router",
        prefix="",
        tags=["Blueprint", "Save"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.routers.instruments.guitar.headstock_inlay_router",
        prefix="/api",
        tags=["Instruments", "Headstock Inlay"],
        category="instruments",
    ),
    RouterSpec(
        module="app.routers.instrument_router",
        prefix="",
        tags=["Instrument"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.neck_router",
        prefix="/api",
        tags=["Neck", "Generator"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.neck.headstock_transition_export",
        prefix="/api/headstock/transition",
        router_attr="router",
        tags=["headstock-transition"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.music",
        prefix="/api/music",
        tags=["Music", "Temperaments"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.project_assets_router",
        prefix="/api",
        tags=["Projects"],
        category="projects",
    ),
    RouterSpec(
        module="app.projects.router",
        prefix="",
        tags=["Projects", "Instruments"],
        category="projects",
    ),
    RouterSpec(
        module="app.business.router",
        prefix="",
        tags=["Business"],
        category="business",
    ),
    RouterSpec(
        module="app.instrument_geometry.neck_taper.api_router",
        prefix="",
        tags=["Instrument", "Neck Taper"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.instruments.guitar.pickup_calculator_router",
        prefix="/api",
        tags=["Instruments", "Guitar", "Calculators"],
        category="instrument_geometry",
    ),
    RouterSpec(
        module="app.routers.instruments.guitar.electric_body_router",
        prefix="/api",
        tags=["Instruments", "Guitar", "Generators"],
        category="instrument_geometry",
    ),
    RouterSpec(
        module="app.routers.binding_design_router",
        prefix="/api/binding",
        tags=["Binding", "Design", "Orchestration"],
        category="instrument_geometry",
    ),
    RouterSpec(
        module="app.routers.saddle_compensation_router",
        prefix="",
        tags=["Instruments", "Bridge", "Calculators"],
        category="instrument",
    ),
    # ── GEOMETRY-010: Side bending parameters ──
    RouterSpec(
        module="app.routers.instrument_geometry_router",
        prefix="",
        tags=["Instruments", "Side Bending", "Calculators"],
        category="instrument_geometry",
    ),
]