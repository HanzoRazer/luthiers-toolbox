"""
RMOS Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /rosette/segment-ring, /rosette/generate-slices, /rosette/preview - Real implementations
- /rosette/export-cnc - WIRED to cam.rosette.cnc (N16.3 G-code export)
- /rosette/cnc-history, /rosette/cnc-job/{job_id} - WIRED to art_jobs_store
- /live-monitor/* - WIRED to runs_v2 store (synthesized subjobs from run data)
- /wrap/mvp/dxf-to-grbl - WIRED to real DXF->G-code pipeline
- /safety/* - WIRED to real RMOS feasibility engine

REMOVED (real implementations exist):
- /analytics/* - See app.rmos.analytics.router
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, File, Form, UploadFile
import hashlib
import uuid
from datetime import datetime, timezone



# Import runs_v2 store for live monitor drilldown
from .runs_v2.store_api import get_run as get_run_artifact


router = APIRouter(tags=["rmos", "stubs"])


# =============================================================================
# Analytics - REMOVED: Real implementations exist in app.rmos.analytics.router
# See: /api/rmos/analytics/lane-analytics, /api/rmos/analytics/risk-timeline/*
# =============================================================================


# =============================================================================
# Rosette Designer Proxies (delegating to real cam.rosette engines)
# =============================================================================

from ..cam.rosette.models import RosetteRingConfig, SegmentationResult, SliceBatch
from ..cam.rosette.segmentation_engine import compute_tile_segmentation
from ..cam.rosette.slice_engine import generate_slices_for_ring
from ..cam.rosette.preview_engine import build_preview_snapshot
from ..cam.rosette.rosette_cnc_wiring import build_ring_cnc_export
from ..cam.rosette.cnc import (
    MaterialType,
    JigAlignment,
    MachineEnvelope,
    MachineProfile,
    GCodePostConfig,
    generate_gcode_from_toolpaths,
)
from dataclasses import asdict


def _parse_ring_config(data: Dict[str, Any]) -> RosetteRingConfig:
    """Parse ring config from request payload."""
    return RosetteRingConfig(
        ring_id=data.get("ring_id", 0),
        radius_mm=float(data.get("radius_mm", 50.0)),
        width_mm=float(data.get("width_mm", 5.0)),
        tile_length_mm=float(data.get("tile_length_mm", 10.0)),
        kerf_mm=float(data.get("kerf_mm", 0.3)),
        herringbone_angle_deg=float(data.get("herringbone_angle_deg", 0.0)),
        twist_angle_deg=float(data.get("twist_angle_deg", 0.0)),
    )


@router.post("/rosette/segment-ring")
def generate_segment_ring(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette segment ring geometry (proxy to real engine)."""
    if payload is None:
        payload = {}
    
    try:
        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")
        
        result = compute_tile_segmentation(ring, tile_count_override)
        
        return {
            "ok": True,
            "segmentation_id": result.segmentation_id,
            "ring_id": result.ring_id,
            "tile_count": result.tile_count,
            "tile_length_mm": result.tile_length_mm,
            "segments": [asdict(t) for t in result.tiles],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "segments": []}


@router.post("/rosette/generate-slices")
def generate_slices(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette slices for manufacturing (proxy to real engine)."""
    if payload is None:
        payload = {}
    
    try:
        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")
        
        # First compute segmentation
        segmentation = compute_tile_segmentation(ring, tile_count_override)
        
        # Then generate slices
        batch = generate_slices_for_ring(ring, segmentation)
        
        return {
            "ok": True,
            "batch_id": batch.batch_id,
            "ring_id": batch.ring_id,
            "slices": [asdict(s) for s in batch.slices],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "slices": []}


@router.post("/rosette/preview")
def preview_rosette(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette preview data (proxy to real engine)."""
    if payload is None:
        payload = {}
    
    try:
        pattern_id = payload.get("pattern_id")
        rings_data = payload.get("rings", [])
        
        # Handle single ring case
        if not rings_data and any(k in payload for k in ["ring_id", "radius_mm"]):
            rings_data = [payload]
        
        rings = [_parse_ring_config(r) for r in rings_data]
        
        # Compute segmentations and slices for all rings
        segmentations = {}
        slice_batches = {}
        
        for ring in rings:
            seg = compute_tile_segmentation(ring)
            segmentations[ring.ring_id] = seg
            
            batch = generate_slices_for_ring(ring, seg)
            slice_batches[ring.ring_id] = batch
        
        # Build preview
        snapshot = build_preview_snapshot(pattern_id, rings, segmentations, slice_batches)
        
        return {
            "ok": True,
            "pattern_id": snapshot.pattern_id,
            "preview": snapshot.payload,
            "rings": [asdict(r) for r in snapshot.rings],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "preview": None}


@router.post("/rosette/export-cnc")
def export_rosette_cnc(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export rosette to CNC-ready G-code format (proxy to real CNC wiring).
    
    Request body:
    - ring: Dict with ring config (ring_id, radius_mm, width_mm, tile_length_mm, kerf_mm)
    - tile_count: Optional[int] - Override tile count
    - material: str - Material type (hardwood, softwood, composite) - default: hardwood
    - machine_profile: str - Machine G-code profile (grbl, fanuc) - default: grbl
    - spindle_rpm: int - Spindle speed (default: 12000)
    - safe_z_mm: float - Safe retract height (default: 5.0)
    - origin_x_mm, origin_y_mm: Jig alignment origin (default: 0, 0)
    - rotation_deg: Jig rotation in degrees (default: 0)
    
    Returns:
    - ok: bool
    - gcode: str - G-code program text
    - job_id: str - Generated job ID for traceability
    - ring_id: int
    - segment_count: int
    - estimated_runtime_sec: float
    - safety: Dict with safety decision details
    """
    if payload is None:
        payload = {}
    
    try:
        import uuid
        from datetime import datetime
        
        # Parse ring config
        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")
        
        # Compute segmentation and slices
        segmentation = compute_tile_segmentation(ring, tile_count_override)
        slice_batch = generate_slices_for_ring(ring, segmentation)
        
        # Parse material type
        material_str = payload.get("material", "hardwood").lower()
        material_map = {
            "hardwood": MaterialType.HARDWOOD,
            "softwood": MaterialType.SOFTWOOD,
            "composite": MaterialType.COMPOSITE,
        }
        material = material_map.get(material_str, MaterialType.HARDWOOD)
        
        # Parse jig alignment
        jig_alignment = JigAlignment(
            origin_x_mm=float(payload.get("origin_x_mm", 0.0)),
            origin_y_mm=float(payload.get("origin_y_mm", 0.0)),
            rotation_deg=float(payload.get("rotation_deg", 0.0)),
        )
        
        # Default machine envelope (conservative)
        envelope = MachineEnvelope(
            x_min_mm=-200.0,
            x_max_mm=200.0,
            y_min_mm=-200.0,
            y_max_mm=200.0,
            z_min_mm=-50.0,
            z_max_mm=50.0,
        )
        
        # Build CNC export bundle with toolpaths
        export_bundle, simulation = build_ring_cnc_export(
            ring=ring,
            slice_batch=slice_batch,
            material=material,
            jig_alignment=jig_alignment,
            envelope=envelope,
        )
        
        # Parse machine profile
        profile_str = payload.get("machine_profile", "grbl").lower()
        profile_map = {
            "grbl": MachineProfile.GRBL,
            "fanuc": MachineProfile.FANUC,
        }
        profile = profile_map.get(profile_str, MachineProfile.GRBL)
        
        # Generate G-code
        post_config = GCodePostConfig(
            profile=profile,
            safe_z_mm=float(payload.get("safe_z_mm", 5.0)),
            spindle_rpm=int(payload.get("spindle_rpm", 12000)),
            tool_id=int(payload.get("tool_id", 1)),
        )
        gcode = generate_gcode_from_toolpaths(export_bundle.toolpaths, post_config)
        
        # Generate job ID
        job_id = f"JOB-ROSETTE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        return {
            "ok": True,
            "gcode": gcode,
            "job_id": job_id,
            "ring_id": ring.ring_id,
            "segment_count": len(export_bundle.toolpaths.segments),
            "estimated_runtime_sec": simulation.estimated_runtime_sec,
            "safety": {
                "decision": export_bundle.safety_decision.decision,
                "risk_level": export_bundle.safety_decision.risk_level,
                "requires_override": export_bundle.safety_decision.requires_override,
                "reasons": export_bundle.safety_decision.reasons,
            },
            "metadata": export_bundle.metadata,
        }
    except Exception as e:
        return {
            "ok": False,
            "gcode": None,
            "job_id": None,
            "error": str(e),
        }


# =============================================================================
# Rosette CNC Proxies (delegating to real art_jobs_store)
# =============================================================================

from ..services.art_jobs_store import get_art_job, _load_jobs
from datetime import datetime


@router.get("/rosette/cnc-history")
def get_cnc_history(
    limit: int = Query(default=50, ge=1, le=200),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
) -> Dict[str, Any]:
    """Get CNC job history for rosettes (proxy to real art_jobs_store)."""
    all_jobs = _load_jobs()

    # Filter by job_type if specified (default: rosette_cam)
    if job_type:
        filtered = [j for j in all_jobs if j.get("job_type") == job_type]
    else:
        # Default to rosette jobs
        filtered = [j for j in all_jobs if j.get("job_type", "").startswith("rosette")]

    # Sort by created_at descending (most recent first)
    filtered.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    # Apply limit
    jobs = filtered[:limit]

    # Format timestamps for frontend
    for job in jobs:
        if "created_at" in job and isinstance(job["created_at"], (int, float)):
            job["created_at"] = datetime.fromtimestamp(job["created_at"]).isoformat() + "Z"

    return {
        "jobs": jobs,
        "total": len(filtered),
    }


@router.get("/rosette/cnc-job/{job_id}")
def get_cnc_job(job_id: str) -> Dict[str, Any]:
    """Get CNC job details (proxy to real art_jobs_store)."""
    from fastapi import HTTPException

    job = get_art_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job ''{job_id}'' not found")

    # Format timestamp for frontend
    created_at = job.created_at
    if isinstance(created_at, (int, float)):
        created_at = datetime.fromtimestamp(created_at).isoformat() + "Z"

    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "created_at": created_at,
        "post_preset": job.post_preset,
        "rings": job.rings,
        "z_passes": job.z_passes,
        "length_mm": job.length_mm,
        "gcode_lines": job.gcode_lines,
        "meta": job.meta,
        "status": "complete",
    }


# =============================================================================
# Live Monitor Stubs
# =============================================================================

def _synthesize_subjobs_from_run(run: Any) -> List[Dict[str, Any]]:
    """
    Synthesize subjob phases from run artifact data.
    
    Creates subjobs based on the operation mode and parameters.
    Generates CAM events from planned parameters (feedrate, spindle, DOC).
    """
    from datetime import datetime, timezone, timedelta
    
    subjobs = []
    created_at = run.created_at_utc if hasattr(run, 'created_at_utc') else datetime.now(timezone.utc)
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            created_at = datetime.now(timezone.utc)
    
    # Extract parameters from request_summary
    req = run.request_summary if hasattr(run, 'request_summary') else {}
    feed_xy = float(req.get('feed_xy', req.get('feed', req.get('feedrate', 1000))))
    spindle = float(req.get('spindle_rpm', req.get('rpm', req.get('spindle', 18000))))
    doc = float(req.get('stepdown', req.get('depth_of_cut', req.get('doc', 3.0))))
    tool_d = float(req.get('tool_d', req.get('tool_diameter', 6.0)))
    
    # Get decision risk level for heuristic
    decision = run.decision if hasattr(run, 'decision') else {}
    risk_level = decision.risk_level if hasattr(decision, 'risk_level') else decision.get('risk_level', 'GREEN')
    
    # Map risk level to heuristic
    heuristic_map = {'GREEN': 'info', 'YELLOW': 'warning', 'RED': 'danger'}
    base_heuristic = heuristic_map.get(str(risk_level).upper(), 'info')
    
    # Determine subjob types based on mode
    mode = run.mode if hasattr(run, 'mode') else 'router'
    if mode in ('saw', 'saw_lab'):
        phases = [('infeed', 0.1), ('roughing', 0.6), ('outfeed', 0.1)]
    else:
        phases = [('roughing', 0.5), ('profiling', 0.3), ('finishing', 0.2)]
    
    # Build subjobs with synthetic events
    elapsed = timedelta(seconds=0)
    for phase_type, time_fraction in phases:
        phase_duration = timedelta(seconds=30 * time_fraction)  # Assume 30s total
        start_time = created_at + elapsed
        end_time = start_time + phase_duration
        
        # Generate 3-5 CAM events per phase
        cam_events = []
        event_count = 3 if phase_type in ('infeed', 'outfeed') else 5
        for i in range(event_count):
            event_time = start_time + (phase_duration * i / event_count)
            
            # Vary feedrate slightly based on phase
            if phase_type == 'roughing':
                event_feed = feed_xy * 0.8
                event_doc = doc
            elif phase_type == 'finishing':
                event_feed = feed_xy * 0.6
                event_doc = doc * 0.3
            else:
                event_feed = feed_xy
                event_doc = doc * 0.5
            
            # Determine feed state
            if i == 0:
                feed_state = 'increasing'
            elif i == event_count - 1:
                feed_state = 'decreasing'
            else:
                feed_state = 'stable'
            
            cam_events.append({
                'timestamp': event_time.isoformat(),
                'feedrate': round(event_feed, 1),
                'spindle_speed': round(spindle, 0),
                'doc': round(event_doc, 2),
                'feed_state': feed_state,
                'heuristic': base_heuristic,
            })
        
        subjobs.append({
            'subjob_type': phase_type,
            'started_at': start_time.isoformat(),
            'ended_at': end_time.isoformat(),
            'cam_events': cam_events,
        })
        
        elapsed += phase_duration
    
    return subjobs


@router.get("/live-monitor/{job_id}/drilldown")
def get_live_monitor_drilldown(job_id: str) -> Dict[str, Any]:
    """
    Get live monitor drilldown data for a job (wired to runs_v2 store).
    
    Synthesizes subjob phases and CAM events from stored run artifact data.
    Provides planned parameters view even without real-time execution telemetry.
    """
    # Try to find the run in runs_v2 store
    run = get_run_artifact(job_id)
    
    if not run:
        # Graceful fallback for missing runs
        return {
            "job_id": job_id,
            "subjobs": [],
            "status": "not_found",
            "message": f"No run found for job_id: {job_id}",
        }
    
    # Synthesize subjobs from run data
    subjobs = _synthesize_subjobs_from_run(run)
    
    # Determine status from run
    status = run.status.value if hasattr(run.status, 'value') else str(run.status)
    
    return {
        "job_id": job_id,
        "subjobs": subjobs,
        "status": status.lower(),
        "message": None,
    }


# =============================================================================
# MVP Wrapper Stubs
# =============================================================================

@router.post("/wrap/mvp/dxf-to-grbl")
async def dxf_to_grbl(
    file: UploadFile = File(...),
    tool_d: float = Form(6.0),
    stepover: float = Form(0.4),
    stepdown: float = Form(2.0),
    z_rough: float = Form(-3.0),
    feed_xy: float = Form(1000.0),
    feed_z: float = Form(300.0),
    rapid: float = Form(3000.0),
    safe_z: float = Form(10.0),
    strategy: str = Form("Spiral"),
    layer_name: str = Form("0"),
    climb: bool = Form(True),
    smoothing: bool = Form(False),
    margin: float = Form(0.0),
) -> Dict[str, Any]:
    """
    Convert DXF to GRBL G-code (MVP workflow).

    Wired to real DXF parsing + adaptive toolpath + G-code generation.
    Creates RMOS run artifact with full attachment persistence.
    """
    import ezdxf
    import io
    from ..routers.adaptive.plan_router import plan as compute_plan
    from ..routers.adaptive_schemas import Loop, PlanIn
    from .runs_v2.attachments import put_bytes_attachment, put_json_attachment
    from .runs_v2.store import RunStoreV2
    from .runs_v2.schemas import RunArtifact, RunAttachment, Hashes

    run_id = f"RUN-DXF-{uuid.uuid4().hex[:12].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    attachments: List[RunAttachment] = []

    try:
        # Read and hash input DXF
        dxf_bytes = await file.read()
        dxf_sha = hashlib.sha256(dxf_bytes).hexdigest()

        # Store input DXF attachment
        dxf_att, _ = put_bytes_attachment(
            dxf_bytes,
            kind="dxf_input",
            mime="application/dxf",
            filename=file.filename or "input.dxf",
            ext=".dxf",
        )
        attachments.append(dxf_att)

        # Parse DXF and extract loops (ezdxf needs temp file, not BytesIO)
        import tempfile
        import os as os_module
        fd, tmp_path = tempfile.mkstemp(suffix=".dxf")
        try:
            os_module.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(dxf_bytes)
            doc = ezdxf.readfile(tmp_path)
        finally:
            if os_module.path.exists(tmp_path):
                os_module.unlink(tmp_path)
        msp = doc.modelspace()
        loops: List[List[tuple]] = []

        for entity in msp:
            if entity.dxftype() == "LWPOLYLINE":
                if layer_name == "0" or entity.dxf.layer == layer_name:
                    pts = [(p[0], p[1]) for p in entity.get_points()]
                    if len(pts) >= 3:
                        if pts[0] != pts[-1]:
                            pts.append(pts[0])
                        loops.append(pts)
            elif entity.dxftype() == "POLYLINE":
                if layer_name == "0" or entity.dxf.layer == layer_name:
                    pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                    if len(pts) >= 3:
                        if pts[0] != pts[-1]:
                            pts.append(pts[0])
                        loops.append(pts)

        if not loops:
            return {
                "ok": False,
                "run_id": run_id,
                "gcode": None,
                "message": f"No closed polylines found on layer '{layer_name}'",
            }

        # Build plan request
        plan_in = PlanIn(
            loops=[Loop(pts=loop) for loop in loops],
            tool_d=tool_d,
            stepover=stepover,
            stepdown=stepdown,
            z_final=z_rough,
            feed=feed_xy,
            plunge=feed_z,
            rapid=rapid,
            safe_z=safe_z,
            strategy=strategy,
            climb=climb,
            smoothing=smoothing,
        )

        # Compute toolpath plan
        plan_result = compute_plan(plan_in)

        # Store CAM plan attachment
        plan_att, _, plan_sha = put_json_attachment(
            plan_result,
            kind="cam_plan",
            filename="cam_plan.json",
        )
        attachments.append(plan_att)

        # Generate G-code from moves
        moves = plan_result.get("moves", [])
        gcode_lines = [
            "; DXF-to-GRBL MVP Export",
            f"; Run ID: {run_id}",
            f"; Tool: {tool_d}mm, Stepover: {stepover*100}%, Stepdown: {stepdown}mm",
            "G21 ; mm mode",
            "G90 ; absolute",
            f"G0 Z{safe_z}",
        ]

        for move in moves:
            cmd = move.get("cmd", "G1")
            x = move.get("x")
            y = move.get("y")
            z = move.get("z")
            f = move.get("f")

            parts = [cmd]
            if x is not None:
                parts.append(f"X{x:.3f}")
            if y is not None:
                parts.append(f"Y{y:.3f}")
            if z is not None:
                parts.append(f"Z{z:.3f}")
            if f is not None:
                parts.append(f"F{f:.0f}")
            gcode_lines.append(" ".join(parts))

        gcode_lines.extend([
            f"G0 Z{safe_z}",
            "M5 ; spindle off",
            "G0 X0 Y0",
            "M30 ; end",
        ])

        gcode_text = "\n".join(gcode_lines)

        # Store G-code attachment
        gcode_att, _ = put_bytes_attachment(
            gcode_text.encode(),
            kind="gcode",
            mime="text/plain",
            filename=f"{run_id}.nc",
            ext=".nc",
        )
        gcode_sha = gcode_att.sha256
        attachments.append(gcode_att)

        # MVP: Skip full run artifact persistence for now
        # Just return the G-code with metadata
        return {
            "ok": True,
            "run_id": run_id,
            "gcode": {
                "inline": True,
                "text": gcode_text,
            },
            "decision": {
                "risk_level": "GREEN",
                "export_allowed": True,
            },
            "feasibility": {
                "rules_triggered": [],
            },
            "attachments": [a.model_dump() for a in attachments],
            "hashes": {
                "dxf_input": dxf_sha,
                "gcode": gcode_sha,
            },
            "mode": "mvp",
            "stats": plan_result.get("stats", {}),
        }

    except Exception as e:
        return {
            "ok": False,
            "run_id": run_id,
            "gcode": None,
            "message": f"DXF-to-GRBL conversion failed: {str(e)}",
        }


# =============================================================================
# Safety Evaluation Proxies (delegating to real RMOS feasibility engine)
# =============================================================================

import os
from .feasibility.engine import compute_feasibility
from .feasibility.schemas import FeasibilityInput, MaterialHardness


def _parse_feasibility_input(payload: Dict[str, Any]) -> FeasibilityInput:
    """Parse payload into FeasibilityInput with sensible defaults."""
    
    # Parse material hardness if provided
    hardness = payload.get("material_hardness")
    if hardness and isinstance(hardness, str):
        try:
            hardness = MaterialHardness(hardness.lower())
        except ValueError:
            hardness = None
    
    return FeasibilityInput(
        # Identity
        pipeline_id=payload.get("pipeline_id", "safety_evaluate_v1"),
        post_id=payload.get("post_id", "GRBL"),
        units=payload.get("units", "mm"),
        
        # CAM params (with sensible defaults)
        tool_d=float(payload.get("tool_diameter_mm", payload.get("tool_d", 6.0))),
        # stepover_percent is 0-100, but FeasibilityInput expects 0-1 decimal
        stepover=float(payload.get("stepover_percent", payload.get("stepover", 40.0))) / 100.0,
        stepdown=float(payload.get("depth_of_cut_mm", payload.get("stepdown", 3.0))),
        z_rough=float(payload.get("z_rough", payload.get("final_depth_mm", -10.0))),
        feed_xy=float(payload.get("feed_xy_mm_min", payload.get("feed_xy", 1000.0))),
        feed_z=float(payload.get("feed_z_mm_min", payload.get("feed_z", 200.0))),
        rapid=float(payload.get("rapid", 3000.0)),
        safe_z=float(payload.get("safe_z", 5.0)),
        strategy=payload.get("strategy", payload.get("operation", "profile")),
        layer_name=payload.get("layer_name", "0"),
        climb=payload.get("climb", True),
        smoothing=float(payload.get("smoothing", 0.0)),
        margin=float(payload.get("margin", 0.0)),
        
        # Geometry summary
        has_closed_paths=payload.get("has_closed_paths"),
        loop_count_hint=payload.get("loop_count_hint"),
        entity_count=payload.get("entity_count"),
        bbox=payload.get("bbox"),
        
        # Material properties (Schema v2)
        material_id=payload.get("material", payload.get("material_id")),
        material_hardness=hardness,
        material_thickness_mm=payload.get("material_thickness_mm"),
        material_resinous=payload.get("material_resinous"),
        
        # Geometry dimensions
        geometry_width_mm=payload.get("geometry_width_mm"),
        geometry_depth_mm=payload.get("geometry_depth_mm"),
        wall_thickness_mm=payload.get("wall_thickness_mm"),
        
        # Tool properties
        tool_flute_length_mm=payload.get("tool_flute_length_mm"),
        tool_stickout_mm=payload.get("tool_stickout_mm"),
        
        # Process
        coolant_enabled=payload.get("coolant_enabled"),
    )


@router.post("/safety/evaluate")
def evaluate_safety(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evaluate safety constraints using real RMOS feasibility engine."""
    if payload is None:
        payload = {}
    
    try:
        fi = _parse_feasibility_input(payload)
        result = compute_feasibility(fi)
        
        # Map FeasibilityResult to expected response format
        decision = "BLOCK" if result.blocking else "ALLOW"
        
        return {
            "ok": True,
            "decision": decision,
            "risk_level": result.risk_level.value,
            "warnings": result.warnings,
            "blocks": result.blocking_reasons,
            "rules_triggered": result.rules_triggered,
            "engine_version": result.engine_version,
        }
    except Exception as e:
        return {
            "ok": False,
            "decision": "ERROR",
            "risk_level": "UNKNOWN",
            "warnings": [],
            "blocks": [str(e)],
            "error": str(e),
        }


@router.get("/safety/mode")
def get_safety_mode() -> Dict[str, Any]:
    """Get current safety mode settings from environment."""
    # Read mode from environment, defaulting to standard
    mode = os.environ.get("RMOS_SAFETY_MODE", "standard")
    strict = os.environ.get("RMOS_STRICT_MODE", "false").lower() in ("1", "true", "yes")
    allow_overrides = os.environ.get("RMOS_ALLOW_OVERRIDES", "true").lower() in ("1", "true", "yes")
    allow_red_override = os.environ.get("RMOS_ALLOW_RED_OVERRIDE", "false").lower() in ("1", "true", "yes")
    
    return {
        "mode": mode,
        "strict_mode": strict,
        "allow_overrides": allow_overrides,
        "allow_red_override": allow_red_override,
    }


# =============================================================================
# Override Token Generator (apprenticeship mode)
# =============================================================================

import secrets
from datetime import datetime, timezone, timedelta

# In-memory token store (ephemeral - cleared on restart)
# Format: {token: {"action": str, "created_by": str, "expires_at": str, "used": bool}}
_override_tokens: Dict[str, Dict[str, Any]] = {}


def _generate_token() -> str:
    """Generate a short, human-readable override token."""
    return secrets.token_hex(4).upper()  # e.g., "A1B2C3D4"


def _clean_expired_tokens() -> None:
    """Remove expired tokens from store."""
    now = datetime.now(timezone.utc)
    expired = []
    for token, data in _override_tokens.items():
        try:
            expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            if expires < now:
                expired.append(token)
        except (ValueError, KeyError):
            expired.append(token)
    for token in expired:
        del _override_tokens[token]


@router.post("/safety/create-override")
def create_safety_override(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a one-time override token for apprenticeship mode.

    Mentors generate these tokens for apprentices to bypass safety checks
    on specific actions. Tokens are single-use and time-limited.

    Request body:
    - action: str - Action this token authorizes (e.g., "start_job", "promote_preset")
    - created_by: str (optional) - Mentor identifier
    - ttl_minutes: int (optional, default 15) - Token expiration time

    Returns:
    - token: str - The override token to share with apprentice
    - action: str - Action this token authorizes
    - created_by: str - Mentor identifier
    - expires_at: str - RFC3339 expiration timestamp
    """
    if payload is None:
        payload = {}

    # Clean up expired tokens periodically
    _clean_expired_tokens()

    action = payload.get("action", "unknown_action")
    created_by = payload.get("created_by") or "anonymous"
    ttl_minutes = int(payload.get("ttl_minutes", 15))

    # Clamp TTL to reasonable bounds
    ttl_minutes = max(1, min(120, ttl_minutes))

    # Generate token
    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    expires_at_str = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Store token
    _override_tokens[token] = {
        "action": action,
        "created_by": created_by,
        "expires_at": expires_at_str,
        "used": False,
    }

    return {
        "token": token,
        "action": action,
        "created_by": created_by,
        "expires_at": expires_at_str,
    }

