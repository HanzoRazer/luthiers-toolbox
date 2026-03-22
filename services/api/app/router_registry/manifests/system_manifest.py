"""Auth, system, and utilities routers."""

from typing import List

from ..models import RouterSpec

SYSTEM_ROUTERS: List[RouterSpec] = [
    RouterSpec(
        module="app.routers.health_router",
        prefix="/api",
        tags=["Health"],
        required=True,
        category="core",
    ),
    RouterSpec(
        module="app.governance.governance_consolidated_router",
        prefix="",
        tags=["Meta", "Governance"],
        required=True,
        category="core",
    ),
    RouterSpec(
        module="app.routers.auth_router",
        prefix="",
        tags=["Auth"],
        required=True,
        category="core",
    ),
    RouterSpec(
        module="app.core.job_queue.router",
        prefix="",
        tags=["Jobs", "Async"],
        required=False,
        category="core",
    ),
    RouterSpec(
        module="app.vision.router",
        prefix="",
        tags=["Vision"],
        category="vision",
    ),
    RouterSpec(
        module="app.advisory.blob_router",
        prefix="",
        tags=["Advisory", "Blobs"],
        category="vision",
    ),
    # REMOVED: app._experimental.ai_cam_router (archived, 0 consumers)
    # REMOVED: app._experimental.joblog_router (archived, 0 consumers)
    RouterSpec(
        module="app.routers.learned_overrides_router",
        prefix="/api",
        tags=["Feeds", "Learned"],
        category="experimental",
    ),
    RouterSpec(
        module="app.routers.analytics_router",
        prefix="/api",
        tags=["Analytics"],
        category="analytics",
    ),
    RouterSpec(
        module="app.ai_context_adapter.routes",
        prefix="",
        tags=["AI Context"],
        category="ai",
    ),
    RouterSpec(
        module="app.routers.ai.assistant_router",
        prefix="",  # Router has /api/ai/assistant prefix
        tags=["AI Assistant", "Compendium"],
        category="ai",
    ),
    RouterSpec(
        module="app.routers.ai.defect_detection_router",
        prefix="",  # Router has /api/ai/defects prefix
        tags=["AI Defects", "Vision", "Wood Analysis"],
        category="ai",
    ),
    RouterSpec(
        module="app.routers.ai.wood_grading_router",
        prefix="",  # Router has /api/ai/wood-grading prefix
        tags=["AI", "Wood Assessment"],
        category="ai",
    ),
    RouterSpec(
        module="app.routers.ai.recommendations_router",
        prefix="",  # Router has /api/ai/recommendations prefix
        tags=["AI", "Recommendations"],
        category="ai",
    ),
    RouterSpec(
        module="app.agentic.router",
        prefix="",  # Router has /api/agentic prefix
        tags=["Agentic", "Spine"],
        category="ai",
    ),
    RouterSpec(
        module="app.routers.misc_stub_routes",
        prefix="/api",
        tags=["Stubs"],
        category="stubs",
    ),
    RouterSpec(
        module="app.analyzer.router",
        prefix="",
        tags=["Analyzer"],
        category="analyzer",
    ),
    RouterSpec(
        module="app.workflow.sessions.routes",
        prefix="",
        tags=["Workflow", "Sessions"],
        category="workflow",
    ),
    RouterSpec(
        module="app.materials.router",
        router_attr="registry_router",
        prefix="",
        tags=["Materials", "Registry"],
        category="materials",
    ),
    RouterSpec(
        module="app.materials.router",
        router_attr="system_router",
        prefix="",
        tags=["Materials", "System"],
        category="materials",
    ),
]
