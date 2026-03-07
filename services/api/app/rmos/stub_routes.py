"""
RMOS Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /rosette/* - Rosette designer operations
- /live-monitor/* - Live monitoring drilldown
- /wrap/mvp/* - DXF to G-code MVP wrapper
- /safety/* - Safety evaluation endpoints

REMOVED (real implementations exist):
- /analytics/* - See app.rmos.analytics.router
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query


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
    """Export rosette to CNC-ready format."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "gcode": None,
        "job_id": None,
        "message": "Stub: CNC export not yet implemented (requires full N12 ring engine)",
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

@router.get("/live-monitor/{job_id}/drilldown")
def get_live_monitor_drilldown(job_id: str) -> Dict[str, Any]:
    """Get live monitor drilldown data for a job."""
    return {
        "job_id": job_id,
        "metrics": [],
        "events": [],
        "status": "unknown",
        "message": "Stub: live monitor not yet implemented",
    }


# =============================================================================
# MVP Wrapper Stubs
# =============================================================================

@router.post("/wrap/mvp/dxf-to-grbl")
def dxf_to_grbl(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert DXF to GRBL G-code (MVP workflow)."""
    if payload is None:
        payload = {}
    return {
        "ok": False,
        "gcode": None,
        "run_id": None,
        "message": "Stub: DXF-to-GRBL conversion not yet implemented. Use /api/cam/adaptive/* endpoints.",
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

