# RMOS Rosette API - CNC Export, History, G-code generation

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from .rmos_rosette_schemas import (
    RingConfig,
    SegmentRingRequest,
    GenerateSlicesRequest,
    RosettePatternsListResponse,
    PreviewRequest,
    PreviewRingSummary,
    PreviewResponse,
    JigAlignmentModel,
    EnvelopeModel,
    CNCExportRequest,
    CNCSegmentModel,
    CNCSafetyModel,
    CNCSimulationModel,
    CNCExportResponse,
    CNCHistoryItem,
    CNCHistoryResponse,
    CNCToolpathStatsModel,
    CNCJobDetailResponse,
)
from ...cam.rosette import (
    # N12 core math
    RosetteRingConfig,
    Tile,
    SegmentationResult,
    SliceBatch,
    compute_tile_segmentation,
    generate_slices_for_ring,
    apply_kerf_physics,
    apply_twist,
    apply_herringbone_engine,
    # N12.2 preview wiring
    compute_ring_geometry,
    build_preview_snapshot,
    # N14.1 CNC wiring
    build_ring_cnc_export,
)
from ...cam.rosette.cnc import (
    MaterialType,
    JigAlignment,
    MachineEnvelope,
    MachineProfile,  # N16.5
    GCodePostConfig,  # N16.5
    generate_gcode_from_toolpaths,  # N16.3
    select_material_feed_rule,  # N16.4
    get_machine_config,  # N16.7
)
from ...cam.rosette.models import Slice
from ...stores.sqlite_pattern_store import SQLitePatternStore
from ...stores.sqlite_joblog_store import (
    SQLiteJobLogStore,
    JOB_TYPE_ROSETTE_CNC_EXPORT,
)
from ...infra.live_monitor import publish_event
from ...reports.operator_report import build_operator_markdown_report
from ...reports.pdf_renderer import markdown_to_pdf_bytes

router = APIRouter(
    prefix="/api/rmos/rosette",
    tags=["rmos-rosette"],
)

# ---

def _segmentation_to_dict(seg: SegmentationResult) -> Dict[str, Any]:
    """Convert SegmentationResult to JSON dict."""
    return {"segmentation_id": seg.segmentation_id, "ring_id": seg.ring_id, "tile_count": seg.tile_count,
            "tile_length_mm": seg.tile_length_mm,
            "tiles": [{"tile_index": t.tile_index, "theta_start_deg": t.theta_start_deg, "theta_end_deg": t.theta_end_deg} for t in seg.tiles]}

def _slice_batch_to_dict(batch) -> Dict[str, Any]:
    """Convert SliceBatch to JSON dict."""
    slices = [{"slice_index": s.slice_index, "tile_index": s.tile_index, "angle_deg": s.angle_final_deg,
               "angle_raw_deg": s.angle_raw_deg, "angle_final_deg": s.angle_final_deg, "theta_start_deg": s.theta_start_deg,
               "theta_end_deg": s.theta_end_deg, "kerf_mm": s.kerf_mm, "herringbone_flip": s.herringbone_flip,
               "herringbone_angle_deg": s.herringbone_angle_deg, "twist_angle_deg": s.twist_angle_deg} for s in batch.slices]
    return {"batch_id": batch.batch_id, "ring_id": batch.ring_id, "slices": slices}

# ---

@router.post("/segment-ring")
def segment_ring(payload: SegmentRingRequest) -> Dict[str, Any]:
    """N12.1: uses the N12 segmentation engine (compute_tile_segmentation)"""
    ring_cfg = payload.ring

    ring = RosetteRingConfig(ring_id=ring_cfg.ring_id or 0, radius_mm=ring_cfg.radius_mm, width_mm=ring_cfg.width_mm,
        tile_length_mm=ring_cfg.tile_length_mm, kerf_mm=ring_cfg.kerf_mm,
        herringbone_angle_deg=ring_cfg.herringbone_angle_deg, twist_angle_deg=ring_cfg.twist_angle_deg)

    seg = compute_tile_segmentation(ring)

    return _segmentation_to_dict(seg)

@router.post("/generate-slices")
def generate_slices(payload: GenerateSlicesRequest) -> Dict[str, Any]:
    """N12.1: converts the incoming segmentation JSON into a SegmentationResult,"""
    # Rebuild ring config
    ring = RosetteRingConfig(ring_id=payload.ring_id, radius_mm=payload.segmentation.get("radius_mm", 45.0),
        width_mm=payload.segmentation.get("width_mm", 3.0), tile_length_mm=payload.segmentation.get("tile_length_mm", 5.0),
        kerf_mm=payload.kerf_mm, herringbone_angle_deg=payload.herringbone_angle_deg, twist_angle_deg=payload.twist_angle_deg)

    # Rebuild SegmentationResult from the incoming segmentation dict
    seg_tiles = []
    tiles_json = payload.segmentation.get("tiles", [])

    seg_tiles = [Tile(tile_index=t.get("tile_index", 0), theta_start_deg=t.get("theta_start_deg", 0.0),
                      theta_end_deg=t.get("theta_end_deg", 0.0)) for t in tiles_json]

    seg = SegmentationResult(segmentation_id=payload.segmentation.get("segmentation_id", "seg_from_client"),
        ring_id=payload.ring_id, tile_count=payload.segmentation.get("tile_count", len(seg_tiles)),
        tile_length_mm=payload.segmentation.get("tile_length_mm", ring.tile_length_mm), tiles=seg_tiles)

    # Run N12 skeleton pipeline
    batch = generate_slices_for_ring(ring, seg)
    kerfed = apply_kerf_physics(ring, batch.slices)
    twisted = apply_twist(ring, kerfed)
    final_slices = apply_herringbone_engine(ring, twisted)
    batch.slices = final_slices

    return _slice_batch_to_dict(batch)

@router.get("/patterns", response_model=RosettePatternsListResponse)
def list_rosette_patterns() -> RosettePatternsListResponse:
    """Lists 'rosette' patterns stored in the PatternStore (N11.1)."""
    store = SQLitePatternStore()
    records = store.list_by_type('rosette')

    items = [{"pattern_id": r.get("pattern_id"), "name": r.get("name"), "pattern_type": r.get("pattern_type"),
              "ring_count": r.get("ring_count"), "rosette_geometry": r.get("rosette_geometry"), "metadata": r.get("metadata")} for r in records]

    return RosettePatternsListResponse(patterns=items)

@router.post("/preview", response_model=PreviewResponse)
def preview_rosette(payload: PreviewRequest) -> PreviewResponse:
    """N12.2: Multi-ring preview endpoint."""
    ring_cfgs = payload.rings or []

    # Convert RingConfig → RosetteRingConfig
    ring_objs = [RosetteRingConfig(ring_id=rc.ring_id if rc.ring_id is not None else idx, radius_mm=rc.radius_mm,
        width_mm=rc.width_mm, tile_length_mm=rc.tile_length_mm, kerf_mm=rc.kerf_mm,
        herringbone_angle_deg=rc.herringbone_angle_deg, twist_angle_deg=rc.twist_angle_deg) for idx, rc in enumerate(ring_cfgs)]

    # Compute geometry for each ring using the N12 ring engine
    seg_map: Dict[int, SegmentationResult] = {}
    batch_map: Dict[int, SliceBatch] = {}

    for ring in ring_objs:
        seg, batch = compute_ring_geometry(ring)
        seg_map[ring.ring_id] = seg
        batch_map[ring.ring_id] = batch

    # Build preview snapshot
    snapshot = build_preview_snapshot(
        pattern_id=payload.pattern_id,
        rings=ring_objs,
        segmentations=seg_map,
        slice_batches=batch_map,
    )

    # Extract ring summaries from snapshot payload
    payload_rings = snapshot.payload.get("rings", [])

    summaries = [PreviewRingSummary(ring_id=r.get("ring_id", 0), radius_mm=r.get("radius_mm", 0.0),
        width_mm=r.get("width_mm", 0.0), tile_count=r.get("tile_count", 0), slice_count=r.get("slice_count", 0)) for r in payload_rings]

    return PreviewResponse(
        pattern_id=snapshot.pattern_id,
        rings=summaries,
    )

# ---

def _build_cnc_inputs_from_payload(
    payload: CNCExportRequest,
) -> tuple[RosetteRingConfig, SliceBatch, MaterialType, JigAlignment, MachineEnvelope]:
    """N16.3 - Shared helper to convert CNCExportRequest payload into"""
    rm = payload.ring
    ring_cfg = RosetteRingConfig(ring_id=rm.ring_id or 0, radius_mm=rm.radius_mm, width_mm=rm.width_mm,
        tile_length_mm=rm.tile_length_mm, kerf_mm=rm.kerf_mm,
        herringbone_angle_deg=rm.herringbone_angle_deg, twist_angle_deg=rm.twist_angle_deg)

    # SliceBatch
    batch_json = payload.slice_batch
    ring_id = batch_json.get("ring_id", ring_cfg.ring_id)
    slices_json = batch_json.get("slices", [])

    slices = [Slice(slice_index=s.get("slice_index", 0), tile_index=s.get("tile_index", 0),
        angle_raw_deg=s.get("angle_raw_deg", s.get("angle_deg", 0.0)), angle_final_deg=s.get("angle_final_deg", s.get("angle_deg", 0.0)),
        theta_start_deg=s.get("theta_start_deg", 0.0), theta_end_deg=s.get("theta_end_deg", 0.0), kerf_mm=s.get("kerf_mm", rm.kerf_mm),
        herringbone_flip=s.get("herringbone_flip", False), herringbone_angle_deg=s.get("herringbone_angle_deg", rm.herringbone_angle_deg),
        twist_angle_deg=s.get("twist_angle_deg", rm.twist_angle_deg)) for s in slices_json]

    slice_batch = SliceBatch(batch_id=batch_json.get("batch_id", f"slice_batch_ring_{ring_id}"), ring_id=ring_id, slices=slices)

    # Material
    material: MaterialType = payload.material

    jm = payload.jig_alignment
    jig = JigAlignment(origin_x_mm=jm.origin_x_mm, origin_y_mm=jm.origin_y_mm, rotation_deg=jm.rotation_deg)

    if payload.envelope is not None:
        em = payload.envelope
        envelope = MachineEnvelope(x_min_mm=em.x_min_mm, x_max_mm=em.x_max_mm, y_min_mm=em.y_min_mm,
            y_max_mm=em.y_max_mm, z_min_mm=em.z_min_mm, z_max_mm=em.z_max_mm)
    else:
        envelope = MachineEnvelope()

    return ring_cfg, slice_batch, material, jig, envelope

# ---

@router.post("/export-cnc", response_model=CNCExportResponse)
def export_cnc_for_ring(payload: CNCExportRequest) -> CNCExportResponse:
    """N14.1 + N10/N14 + N14.x: Per-ring CNC export endpoint with JobLog, LiveMonitor, and operator report."""
    # 1) Re-use shared payload parser
    ring_cfg, slice_batch, material, jig, envelope = _build_cnc_inputs_from_payload(payload)

    # 2) Create JobLog entry (status='running')
    joblog = SQLiteJobLogStore()
    jig_origin_dict = {"origin_x_mm": jig.origin_x_mm, "origin_y_mm": jig.origin_y_mm, "rotation_deg": jig.rotation_deg}
    envelope_dict = {"x_min_mm": envelope.x_min_mm, "y_min_mm": envelope.y_min_mm, "z_min_mm": envelope.z_min_mm,
                     "x_max_mm": envelope.x_max_mm, "y_max_mm": envelope.y_max_mm, "z_max_mm": envelope.z_max_mm}

    job = joblog.create_rosette_cnc_export_job(
        pattern_id=None,  # can be wired later to pattern_id from UI if available
        ring_id=ring_cfg.ring_id,
        material=payload.material.value,
        jig_origin=jig_origin_dict,
        envelope=envelope_dict,
        parameters_extra={
            "batch_id": slice_batch.batch_id,
        },
    )
    job_id = job['id']

    # 5) Call the wiring function to build export bundle + simulation
    try:
        export_bundle, sim_result = build_ring_cnc_export(
            ring=ring_cfg,
            slice_batch=slice_batch,
            material=payload.material,
            jig_alignment=jig,
            envelope=envelope,
        )

        # 6) Generate operator report Markdown
        operator_report_md = build_operator_markdown_report(
            job_id=job_id,
            export_bundle=export_bundle,
            simulation=sim_result,
            pattern_id=None,  # Can be wired to pattern_id if available
        )

        # 7) Update JobLog with results + report (status='completed')
        joblog.complete_job_with_results(
            job_id=job_id,
            status="completed",
            results={
                "safety": {
                    "decision": export_bundle.safety_decision.decision,
                    "risk_level": export_bundle.safety_decision.risk_level,
                    "requires_override": export_bundle.safety_decision.requires_override,
                    "reasons": export_bundle.safety_decision.reasons,
                },
                "simulation": {
                    "passes": sim_result.passes,
                    "estimated_runtime_sec": sim_result.estimated_runtime_sec,
                    "max_feed_mm_per_min": sim_result.max_feed_mm_per_min,
                    "envelope_ok": sim_result.envelope_ok,
                },
                "metadata": export_bundle.metadata,
                "operator_report_md": operator_report_md,
            },
        )

        # 8) Emit LiveMonitor event
        publish_event(
            "rosette_cnc_export",
            {
                "job_id": job_id,
                "ring_id": export_bundle.ring_id,
                "material": payload.material.value,
                "safety_decision": export_bundle.safety_decision.decision,
                "safety_risk_level": export_bundle.safety_decision.risk_level,
                "requires_override": export_bundle.safety_decision.requires_override,
                "runtime_sec": sim_result.estimated_runtime_sec,
            },
        )

    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        # Best-effort: mark job failed and rethrow
        joblog.complete_job_with_results(
            job_id=job_id,
            status="failed",
            results={"error": str(exc)},
        )
        raise

    # 9) Flatten into response model (includes operator report)
    segments = [CNCSegmentModel(x_start_mm=seg.x_start_mm, y_start_mm=seg.y_start_mm, z_start_mm=seg.z_start_mm,
        x_end_mm=seg.x_end_mm, y_end_mm=seg.y_end_mm, z_end_mm=seg.z_end_mm, feed_mm_per_min=seg.feed_mm_per_min)
        for seg in export_bundle.toolpaths.segments]

    sd = export_bundle.safety_decision
    safety = CNCSafetyModel(decision=sd.decision, risk_level=sd.risk_level, requires_override=sd.requires_override, reasons=list(sd.reasons))

    simulation = CNCSimulationModel(passes=sim_result.passes, estimated_runtime_sec=sim_result.estimated_runtime_sec,
        max_feed_mm_per_min=sim_result.max_feed_mm_per_min, envelope_ok=sim_result.envelope_ok)

    jig_model = JigAlignmentModel(origin_x_mm=jig.origin_x_mm, origin_y_mm=jig.origin_y_mm, rotation_deg=jig.rotation_deg)

    return CNCExportResponse(job_id=job_id, ring_id=export_bundle.ring_id, toolpaths=segments,
        jig_alignment=jig_model, safety=safety, simulation=simulation,
        metadata=export_bundle.metadata, operator_report_md=operator_report_md)

# ---

@router.post("/export-gcode")
def export_gcode_for_ring(
    payload: CNCExportRequest,
    profile: MachineProfile = Query(
        MachineProfile.GRBL,
        description="G-code profile (ignored if machine_id is set)",
    ),
    tool_id: int = Query(
        1,
        ge=1,
        le=99,
        description="Tool number (overrides machine default if provided)",
    ),
    program_number: int | None = Query(
        None,
        description="FANUC O-number (overrides machine default if provided)",
    ),
    machine_id: str | None = Query(
        None,
        description="Optional machine identifier (e.g. 'bcm_2030ca', 'fanuc_demo')",
    ),
) -> Response:
    """N16.3+N16.4+N16.5+N16.7 - Per-ring G-code export with:"""
    # Build CNC inputs identical to /export-cnc
    ring_cfg, slice_batch, material, jig, envelope = _build_cnc_inputs_from_payload(
        payload
    )

    # Build toolpaths using the full N16.x stack
    export_bundle, sim_result = build_ring_cnc_export(ring=ring_cfg, slice_batch=slice_batch,
        material=material, jig_alignment=jig, envelope=envelope)

    # Material-specific spindle + depth, via FeedRule (N16.4)
    feed_rule = select_material_feed_rule(material)

    # Resolve machine config (if any) (N16.7)
    machine_cfg = None
    if machine_id is not None:
        machine_cfg = get_machine_config(machine_id)
        if machine_cfg is None:
            raise HTTPException(status_code=400, detail=f"Unknown machine_id '{machine_id}'")

    # Effective profile (N16.7: machine config overrides generic profile)
    if machine_cfg is not None:
        effective_profile = machine_cfg.profile
        effective_safe_z = machine_cfg.default_safe_z_mm
        effective_tool_id = tool_id if tool_id != 1 else machine_cfg.default_tool_id
        effective_program_number = program_number if program_number is not None else machine_cfg.default_program_number
    else:
        effective_profile = profile
        effective_safe_z = 5.0  # generic safe Z fallback
        effective_tool_id = tool_id
        effective_program_number = program_number

    post = GCodePostConfig(profile=effective_profile, program_number=effective_program_number,
        safe_z_mm=effective_safe_z, spindle_rpm=feed_rule.spindle_rpm, tool_id=effective_tool_id)

    gcode_text = generate_gcode_from_toolpaths(plan=export_bundle.toolpaths, post=post)

    # Compose filename with ring + profile (+ machine_id if present)
    suffix = effective_profile.value
    if machine_cfg is not None:
        suffix = f"{machine_cfg.machine_id}_{suffix}"
    filename = f"rosette_ring_{ring_cfg.ring_id}_{suffix}.gcode"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(content=gcode_text, media_type="text/plain", headers=headers)

# ---

@router.get("/operator-report-pdf/{job_id}")
def download_operator_report_pdf(job_id: str) -> Response:
    """Bundle #11 - Download Operator Report as PDF."""
    joblog = SQLiteJobLogStore()
    job = joblog.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["job_type"] != JOB_TYPE_ROSETTE_CNC_EXPORT:
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not a rosette CNC export job")

    operator_report_md = job["results"].get("operator_report_md") if isinstance(job["results"], dict) else None
    if not operator_report_md:
        raise HTTPException(status_code=404, detail="Operator report not found for this job")

    # Render Markdown → PDF
    pdf_bytes = markdown_to_pdf_bytes(markdown_text=operator_report_md, title=f"RMOS Operator Report - Job {job_id}")

    filename = f"rmos_operator_report_{job_id}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

# ---

@router.get("/cnc-history", response_model=CNCHistoryResponse)
def get_cnc_history(limit: int = 50) -> CNCHistoryResponse:
    """Bundle #13 (Part A) - RMOS Studio CNC history endpoint."""
    store = SQLiteJobLogStore()
    jobs = store.list_rosette_cnc_exports(limit=limit)

    def _parse_job(job):
        params, results = job.get("parameters") or {}, job.get("results") or {}
        safety = results.get("safety", {}) if isinstance(results, dict) else {}
        sim = results.get("simulation", {}) if isinstance(results, dict) else {}
        created_at_val = job.get("created_at")
        try: created_at = datetime.fromisoformat(created_at_val.replace("Z", "+00:00")) if isinstance(created_at_val, str) else None
        except (ValueError, TypeError): created_at = None
        return CNCHistoryItem(job_id=job["id"], created_at=created_at, status=job.get("status", "unknown"),
            ring_id=params.get("ring_id"), material=params.get("material"), safety_decision=safety.get("decision"),
            safety_risk_level=safety.get("risk_level"), runtime_sec=sim.get("estimated_runtime_sec"), pattern_id=job.get("pattern_id"))
    return CNCHistoryResponse(items=[_parse_job(j) for j in jobs])

@router.get("/cnc-job/{job_id}", response_model=CNCJobDetailResponse)
def get_cnc_job_detail(job_id: str) -> CNCJobDetailResponse:
    """CNC Job detail endpoint."""
    store = JobLogStore()
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.job_type != JOB_TYPE_ROSETTE_CNC_EXPORT:
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not a rosette CNC export job")

    params = job.parameters or {}
    results = job.results or {}

    ring_id = params.get("ring_id")
    material = params.get("material")

    safety_dict = results.get("safety") if isinstance(results, dict) else None
    sim_dict = results.get("simulation") if isinstance(results, dict) else None
    metadata = results.get("metadata") if isinstance(results, dict) else {}
    operator_report_md = results.get("operator_report_md") if isinstance(results, dict) else None

    safety = CNCSafetyModel(decision=safety_dict.get("decision", ""), risk_level=safety_dict.get("risk_level", ""),
        requires_override=bool(safety_dict.get("requires_override", False)),
        reasons=list(safety_dict.get("reasons", []) or [])) if isinstance(safety_dict, dict) else None

    simulation = CNCSimulationModel(passes=sim_dict.get("passes", 0), estimated_runtime_sec=sim_dict.get("estimated_runtime_sec", 0.0),
        max_feed_mm_per_min=sim_dict.get("max_feed_mm_per_min", 0.0), envelope_ok=bool(sim_dict.get("envelope_ok", True))) if isinstance(sim_dict, dict) else None

    origin = metadata.get("origin", {}) if isinstance(metadata, dict) else {}
    tool_stats = CNCToolpathStatsModel(segment_count=metadata.get("segment_count", 0) if isinstance(metadata, dict) else 0,
        origin_x_mm=origin.get("origin_x_mm"), origin_y_mm=origin.get("origin_y_mm"), rotation_deg=origin.get("rotation_deg"))

    created_at_val = results.get("created_at") if isinstance(results, dict) else None
    try: created_at = datetime.fromisoformat(created_at_val.replace("Z", "+00:00")) if isinstance(created_at_val, str) else None
    except (ValueError, TypeError): created_at = None

    return CNCJobDetailResponse(job_id=job.job_id, pattern_id=job.pattern_id, status=job.status,
        ring_id=ring_id, material=material, created_at=created_at, safety=safety, simulation=simulation,
        toolpath_stats=tool_stats, operator_report_md=operator_report_md,
        metadata=metadata if isinstance(metadata, dict) else {}, parameters=params if isinstance(params, dict) else {})
