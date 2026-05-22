"""CAM domain routers (core, subsystem, config, saw lab, consolidated)."""

from typing import List

from ..models import RouterSpec

CAM_ROUTERS: List[RouterSpec] = [
    RouterSpec(
        module="app.routers.simulation_consolidated_router",
        prefix="/api/cam/sim",
        tags=["CAM Simulation"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.geometry",
        prefix="/api/geometry",
        tags=["Geometry"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.tooling",
        prefix="/api/tooling",
        tags=["Tooling"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.material_router",
        prefix="/api",
        tags=["Material", "Energy Model"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.adaptive",
        prefix="/api",
        tags=["Adaptive Pocketing"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.cam.routers.monitoring",
        prefix="/api/cam",
        tags=["CAM Monitoring"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.cam.routers.utility",
        prefix="/api/cam",
        tags=["CAM Utility"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.cam_learn_router",
        prefix="/api/cam/learn",
        tags=["CAM Learning"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.gcode_consolidated_router",
        prefix="/api",
        tags=["G-code", "CAM"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.adaptive_preview_router",
        prefix="/api",
        tags=["Adaptive", "Preview"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.dxf_adaptive_consolidated_router",
        router_attr="router",
        prefix="/api",
        tags=["cam", "dxf", "adaptive"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.dxf_preflight_router",
        prefix="/api",
        tags=["DXF", "Preflight"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.polygon_offset_router",
        prefix="/api",
        tags=["Geometry", "Polygon"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.bridge_presets_router",
        prefix="/api",
        tags=["CAM Bridge"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.machines_consolidated_router",
        prefix="/api/machines",
        tags=["Machines"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.posts_consolidated_router",
        prefix="/api/posts",
        tags=["Post Processors"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.registry_router",
        prefix="/api/registry",
        tags=["Data Registry"],
        category="config",
    ),
    RouterSpec(
        module="app.saw_lab.__init_router__",
        prefix="",
        tags=["Saw Lab", "Batch"],
        required=True,
        category="saw_lab",
    ),
    RouterSpec(
        module="app.routers.retract",
        prefix="/api/cam/retract",
        tags=["CAM", "Retract Patterns"],
        category="misc",
    ),
    RouterSpec(
        module="app.routers.cam_pipeline_preset_run_router",
        prefix="/api",
        tags=["CAM", "Pipeline"],
        category="misc",
    ),
    RouterSpec(
        module="app.routers.cam_risk_router",
        prefix="/api",
        tags=["CAM", "Risk"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.probe",
        prefix="/api",
        tags=["Probe", "CAM"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.routers.job_intelligence_router",
        prefix="/api/cam",
        tags=["CAM", "Job Intelligence"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.routers.bridge_export_router",
        prefix="/api/cam",
        tags=["CAM", "Bridge"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.routers.fret_slots_router",
        prefix="/api/cam",
        tags=["CAM", "Fret Slots"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.nut_slot_router",
        prefix="/api/cam",
        tags=["CAM", "Nut Slot"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.postprocessor_boundary_router",
        prefix="/api/cam",
        tags=["CAM", "Postprocessor", "Compatibility"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.dxf_translator_router",
        prefix="/api/cam",
        tags=["CAM", "DXF", "Translator"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.export_lifecycle_router",
        prefix="/api/cam",
        tags=["CAM", "Export", "Lifecycle"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.lifecycle_capability_router",
        prefix="/api/cam",
        tags=["CAM", "Lifecycle", "Capabilities"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_capability_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Capabilities"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translation_artifact_router",
        prefix="",
        tags=["CAM", "Translation", "Artifacts"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translation_artifact_authorization_router",
        prefix="",
        tags=["CAM", "Translation", "Authorization"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translation_provenance_router",
        prefix="",
        tags=["CAM", "Translation", "Provenance"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_readiness_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Readiness"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_execution_quarantine_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Quarantine"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_governance_dossier_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Governance", "Dossier"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_governance_review_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Governance", "Review"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_governance_review_ledger_router",
        prefix="/api/cam",
        tags=["CAM", "Translator", "Governance", "Ledger"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.translator_governance_continuity_router",
        prefix="",
        tags=["CAM", "Translator", "Governance", "Continuity"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.ontology_reconciliation_router",
        prefix="",
        tags=["CAM", "Ontology", "Governance", "Reconciliation"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.lifecycle_promotion_router",
        prefix="",
        tags=["CAM", "Lifecycle", "Promotion"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.rosette.photo_batch_router",
        prefix="",
        tags=["CAM", "Rosette", "Batch"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.guitar",
        prefix="/api/cam/guitar",
        tags=["CAM", "Guitar"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam_post_v155_router",
        prefix="/api/cam/post",
        tags=["CAM", "Post", "GCode"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam_relief_router",
        prefix="/api",
        tags=["CAM", "Relief"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cnc_production.presets_router",
        prefix="/api",
        tags=["CNC", "Presets"],
        category="cnc",
    ),
    RouterSpec(
        module="app.cam.routers",
        router_attr="cam_router",
        prefix="/api/cam",
        tags=["CAM Consolidated"],
        category="consolidated",
    ),
    RouterSpec(
        module="app.compare.routers",
        router_attr="compare_router",
        prefix="/api/compare",
        tags=["Compare Consolidated"],
        category="consolidated",
    ),
    RouterSpec(
        module="app.cam.headstock.router",
        prefix="",
        tags=["CAM", "Headstock", "Inlay"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam.cam_workspace_router",
        prefix="/api/cam-workspace",
        router_attr="router",
        tags=["cam-workspace"],
        category="cam",
    ),
    # ── HEADSTOCK-001: DXF export with veneer + binding ──
    RouterSpec(
        module="app.routers.headstock.dxf_export",
        prefix="/api/export",
        tags=["Export", "Headstock", "DXF"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.export.curve_export_router",
        prefix="/api/export",
        tags=["Export", "Curve", "DXF"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.export.rosette_pdf_router",
        prefix="/api/export",
        tags=["Export", "Rosette", "PDF"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.woodworking_router",
        prefix="/api/woodworking",
        tags=["Woodworking"],
        category="cam",
    ),
    # ── ARCHTOP: Contours, stiffness, modal analysis ──
    RouterSpec(
        module="app.routers.archtop_router",
        prefix="",  # Router has its own /api/archtop prefix
        tags=["Archtop", "CAM"],
        category="cam",
    ),
    # ── BODY SOLVER: BOE ↔ IBG integration ──
    RouterSpec(
        module="app.routers.body_solver_router",
        prefix="",  # Router has its own /api/body prefix
        tags=["Body Solver", "IBG"],
        category="cam",
    ),
    # ── MRP-2B: Body Export Bridge (BOE → Export Object) ──
    RouterSpec(
        module="app.routers.export.body_export_router",
        prefix="/api/export",
        tags=["Export", "Body", "MRP"],
        category="cam",
    ),
    # ── MRP-3B: DXF Translator Endpoint (Export Object → DXF) ──
    # DEPRECATED: Use /api/translate/{target} instead (MRP-4A)
    RouterSpec(
        module="app.routers.export.dxf_translate_router",
        prefix="/api/export/translate",
        tags=["Export", "Translate", "DXF", "MRP"],
        category="cam",
    ),
    # ── MRP-4A: Multi-Target Translator Endpoint ──
    RouterSpec(
        module="app.routers.export.translate_router",
        prefix="/api/translate",
        tags=["Export", "Translate", "MRP"],
        category="cam",
    ),
    # ── CAM 7W: Manufacturing Replay Intelligence ──
    RouterSpec(
        module="app.routers.cam.manufacturing_replay_router",
        prefix="",
        tags=["CAM", "Manufacturing", "Replay", "Review"],
        category="cam",
    ),
    # ── CAM 7X: Federated Manufacturing Semantics ──
    RouterSpec(
        module="app.routers.cam.federated_semantics_router",
        prefix="",
        tags=["CAM", "Federation", "Semantics"],
        category="cam",
    ),
    # ── CAM 7Y: Federation CI Enforcement & Drift Baseline ──
    RouterSpec(
        module="app.routers.cam.federation_ci_router",
        prefix="",
        tags=["CAM", "Federation", "CI"],
        category="cam",
    ),
    # ── CAM 7Z: Governance Baseline Freeze & Release Readiness ──
    RouterSpec(
        module="app.routers.cam.governance_freeze_router",
        prefix="",
        tags=["CAM", "Governance", "Release"],
        category="cam",
    ),
]