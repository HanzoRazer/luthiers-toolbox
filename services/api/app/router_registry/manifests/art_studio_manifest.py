"""Art Studio domain routers."""

from typing import List

from ..models import RouterSpec

ART_STUDIO_ROUTERS: List[RouterSpec] = [
    RouterSpec(
        module="app.routers.art.root_art_router",
        prefix="",
        tags=["Art Studio", "Root"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.pattern_routes",
        prefix="",
        tags=["Art Studio", "Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.generator_routes",
        prefix="",
        tags=["Art Studio", "Generators"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.snapshot_routes",
        prefix="",
        tags=["Art Studio", "Snapshots"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_jobs_routes",
        prefix="",
        tags=["Art Studio", "Rosette Jobs"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_compare_routes",
        prefix="",
        tags=["Art Studio", "Rosette Compare"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_snapshot_routes",
        prefix="/api/art",
        tags=["Art Studio", "Snapshots v2"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_pattern_routes",
        prefix="",
        tags=["Art Studio", "Rosette Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_manufacturing_routes",
        prefix="",
        tags=["Art Studio", "Rosette Manufacturing"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.preview_routes",
        prefix="/api",
        tags=["Art Studio", "Preview"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.bracing_router",
        prefix="/api",
        tags=["Art Studio", "Bracing"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.inlay_router",
        prefix="/api",
        tags=["Art Studio", "Inlay"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.inlay_pattern_routes",
        prefix="",
        tags=["Art Studio", "Inlay Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_designer_routes",
        prefix="/api/art/rosette-designer",
        tags=["Art Studio", "Rosette Designer"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.preview_consolidated_router",
        prefix="/api/art-studio",
        router_attr="router",
        tags=["art-studio-preview"],
        category="art_studio",
    ),
]
