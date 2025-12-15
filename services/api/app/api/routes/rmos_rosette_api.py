# Patch N11.2 + N12.1 + N14.1 + N10/N14 + N14.x + Bundle #13 - RMOS Rosette API
#
# N11.2: initial stub endpoints
# N12.1: wire endpoints into the N12 core math skeleton while preserving
#        the JSON shape expected by the current frontend.
# N14.1: per-ring CNC export endpoint
# N10/N14: JobLog + LiveMonitor hooks
# N14.x: Operator report generation (Bundle #10)
# N14.x: Operator report PDF export (Bundle #11)
# Bundle #12: job_id surfacing + UI download button
# Bundle #13: CNC History view + Advanced Safety

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

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


# ========== Pydantic models (payloads) ==========

class RingConfig(BaseModel):
    """Configuration for a single rosette ring."""
    ring_id: Optional[int] = Field(None, description="Ring identifier")
    radius_mm: float = Field(45.0, description="Ring radius in millimeters")
    width_mm: float = Field(3.0, description="Ring width in millimeters")
    tile_length_mm: float = Field(5.0, description="Target tile length in millimeters")
    kerf_mm: float = Field(0.3, description="Saw kerf width in millimeters")
    herringbone_angle_deg: float = Field(0.0, description="Herringbone alternation angle")
    twist_angle_deg: float = Field(0.0, description="Ring twist angle for spiral patterns")


class SegmentRingRequest(BaseModel):
    """Request to segment a ring into tiles."""
    ring: RingConfig


class GenerateSlicesRequest(BaseModel):
    """Request to generate saw slices from segmentation."""
    ring_id: int = Field(..., description="Ring identifier")
    segmentation: Dict[str, Any] = Field(..., description="Segmentation result from /segment-ring")
    kerf_mm: float = Field(0.3, description="Saw kerf width")
    herringbone_angle_deg: float = Field(0.0, description="Herringbone angle")
    twist_angle_deg: float = Field(0.0, description="Ring twist angle")


class RosettePatternsListResponse(BaseModel):
    """Response containing list of rosette patterns."""
    patterns: List[Dict[str, Any]]


class PreviewRequest(BaseModel):
    """
    Request body for RMOS Rosette preview.

    For N12.2 we keep it simple:
      - rings: array of RingConfig
      - pattern_id: optional string
    The backend recomputes segmentation and slices from the ring configs.
    """
    pattern_id: Optional[str] = Field(None, description="Optional pattern identifier")
    rings: List[RingConfig] = Field(..., description="Array of ring configurations")


class PreviewRingSummary(BaseModel):
    """Summary of a single ring in preview."""
    ring_id: int = Field(..., description="Ring identifier")
    radius_mm: float = Field(..., description="Ring radius in millimeters")
    width_mm: float = Field(..., description="Ring width in millimeters")
    tile_count: int = Field(..., description="Number of tiles in ring")
    slice_count: int = Field(..., description="Number of slices in ring")


class PreviewResponse(BaseModel):
    """Response for multi-ring preview."""
    pattern_id: Optional[str] = Field(None, description="Pattern identifier if provided")
    rings: List[PreviewRingSummary] = Field(..., description="Array of ring summaries")


# ========== N14.1 CNC Export Models ==========

class JigAlignmentModel(BaseModel):
    """Jig alignment parameters for CNC setup."""
    origin_x_mm: float = Field(0.0, description="X origin of jig in machine coordinates")
    origin_y_mm: float = Field(0.0, description="Y origin of jig in machine coordinates")
    rotation_deg: float = Field(0.0, description="Rotation of jig relative to machine axes")


class EnvelopeModel(BaseModel):
    """Machine envelope (working volume) bounds."""
    x_min_mm: float = Field(0.0, description="Minimum X coordinate")
    y_min_mm: float = Field(0.0, description="Minimum Y coordinate")
    z_min_mm: float = Field(-50.0, description="Minimum Z coordinate (negative is below work surface)")
    x_max_mm: float = Field(1000.0, description="Maximum X coordinate")
    y_max_mm: float = Field(1000.0, description="Maximum Y coordinate")
    z_max_mm: float = Field(0.0, description="Maximum Z coordinate (0 is work surface)")


class CNCExportRequest(BaseModel):
    """
    Request body for per-ring CNC export.

    Expects:
      - ring: RingConfig (same as used elsewhere)
      - slice_batch: dict from /generate-slices
      - material: "hardwood" | "softwood" | "composite"
      - jig_alignment: machine origin / rotation
      - envelope: optional machine envelope override
    """
    ring: RingConfig
    slice_batch: Dict[str, Any]
    material: MaterialType
    jig_alignment: JigAlignmentModel = Field(default_factory=JigAlignmentModel)
    envelope: Optional[EnvelopeModel] = None


class CNCSegmentModel(BaseModel):
    """A single CNC toolpath segment."""
    x_start_mm: float
    y_start_mm: float
    z_start_mm: float
    x_end_mm: float
    y_end_mm: float
    z_end_mm: float
    feed_mm_per_min: float


class CNCSafetyModel(BaseModel):
    """Safety decision for CNC operation."""
    decision: str
    risk_level: str
    requires_override: bool
    reasons: List[str]


class CNCSimulationModel(BaseModel):
    """CNC simulation results."""
    passes: int
    estimated_runtime_sec: float
    max_feed_mm_per_min: float
    envelope_ok: bool


class CNCExportResponse(BaseModel):
    """Response for per-ring CNC export."""
    job_id: str = Field(..., description="JobLog identifier for traceability and report retrieval")
    ring_id: int
    toolpaths: List[CNCSegmentModel]
    jig_alignment: JigAlignmentModel
    safety: CNCSafetyModel
    simulation: CNCSimulationModel
    metadata: Dict[str, Any]
    operator_report_md: Optional[str] = Field(None, description="Markdown operator checklist")


# ========== Internal helpers to convert dataclasses → dicts ==========

def _segmentation_to_dict(seg: SegmentationResult) -> Dict[str, Any]:
    """
    Convert SegmentationResult dataclass into the JSON shape used by
    the frontend (same as old stub).
    """
    return {
        "segmentation_id": seg.segmentation_id,
        "ring_id": seg.ring_id,
        "tile_count": seg.tile_count,
        "tile_length_mm": seg.tile_length_mm,
        "tiles": [
            {
                "tile_index": t.tile_index,
                "theta_start_deg": t.theta_start_deg,
                "theta_end_deg": t.theta_end_deg,
            }
            for t in seg.tiles
        ],
    }


def _slice_batch_to_dict(batch) -> Dict[str, Any]:
    """
    Convert SliceBatch dataclass into the JSON shape used by the
    frontend stub, with some extra fields added.

    Previous stub shape was:
      {
        "batch_id": "...",
        "ring_id": ...,
        "slices": [
          {
            "slice_index": ...,
            "tile_index": ...,
            "angle_deg": ...,
            "theta_start_deg": ...,
            "theta_end_deg": ...,
            "kerf_mm": ...,
            "herringbone_flip": ...,
            "herringbone_angle_deg": ...
          },
          ...
        ]
      }

    N12.1 keeps that but also exposes:
      - angle_raw_deg
      - angle_final_deg
      - twist_angle_deg
    """
    slices: List[Dict[str, Any]] = []
    for s in batch.slices:
        slices.append(
            {
                "slice_index": s.slice_index,
                "tile_index": s.tile_index,
                # Keep 'angle_deg' compatible with old stub by mapping to final angle.
                "angle_deg": s.angle_final_deg,
                "angle_raw_deg": s.angle_raw_deg,
                "angle_final_deg": s.angle_final_deg,
                "theta_start_deg": s.theta_start_deg,
                "theta_end_deg": s.theta_end_deg,
                "kerf_mm": s.kerf_mm,
                "herringbone_flip": s.herringbone_flip,
                "herringbone_angle_deg": s.herringbone_angle_deg,
                "twist_angle_deg": s.twist_angle_deg,
            }
        )

    return {
        "batch_id": batch.batch_id,
        "ring_id": batch.ring_id,
        "slices": slices,
    }


# ========== Routes ==========

@router.post("/segment-ring")
def segment_ring(payload: SegmentRingRequest) -> Dict[str, Any]:
    """
    N12.1: uses the N12 segmentation engine (compute_tile_segmentation)
    but returns the same JSON shape as the N11 stub.
    
    Computes ring segmentation into tiles using N12 core math.
    
    Args:
        payload: Ring configuration
    
    Returns:
        Segmentation result with tile array
    """
    ring_cfg = payload.ring

    ring = RosetteRingConfig(
        ring_id=ring_cfg.ring_id or 0,
        radius_mm=ring_cfg.radius_mm,
        width_mm=ring_cfg.width_mm,
        tile_length_mm=ring_cfg.tile_length_mm,
        kerf_mm=ring_cfg.kerf_mm,
        herringbone_angle_deg=ring_cfg.herringbone_angle_deg,
        twist_angle_deg=ring_cfg.twist_angle_deg,
    )

    seg = compute_tile_segmentation(ring)

    return _segmentation_to_dict(seg)


@router.post("/generate-slices")
def generate_slices(payload: GenerateSlicesRequest) -> Dict[str, Any]:
    """
    N12.1: converts the incoming segmentation JSON into a SegmentationResult,
    rebuilds a RosetteRingConfig from the request, runs the full N12 skeleton
    (slice generation + kerf + twist + herringbone), and returns the result
    in the same structure as the old stub.
    
    Generates saw slices from segmentation with physics applied.
    
    Args:
        payload: Slice generation parameters
    
    Returns:
        Slice batch with processed slices
    """
    # Rebuild ring config
    ring = RosetteRingConfig(
        ring_id=payload.ring_id,
        radius_mm=payload.segmentation.get("radius_mm", 45.0),
        width_mm=payload.segmentation.get("width_mm", 3.0),
        tile_length_mm=payload.segmentation.get("tile_length_mm", 5.0),
        kerf_mm=payload.kerf_mm,
        herringbone_angle_deg=payload.herringbone_angle_deg,
        twist_angle_deg=payload.twist_angle_deg,
    )

    # Rebuild SegmentationResult from the incoming segmentation dict
    seg_tiles = []
    tiles_json = payload.segmentation.get("tiles", [])

    for t in tiles_json:
        seg_tiles.append(
            Tile(
                tile_index=t.get("tile_index", 0),
                theta_start_deg=t.get("theta_start_deg", 0.0),
                theta_end_deg=t.get("theta_end_deg", 0.0),
            )
        )

    seg = SegmentationResult(
        segmentation_id=payload.segmentation.get("segmentation_id", "seg_from_client"),
        ring_id=payload.ring_id,
        tile_count=payload.segmentation.get("tile_count", len(seg_tiles)),
        tile_length_mm=payload.segmentation.get("tile_length_mm", ring.tile_length_mm),
        tiles=seg_tiles,
    )

    # Run N12 skeleton pipeline
    batch = generate_slices_for_ring(ring, seg)
    kerfed = apply_kerf_physics(ring, batch.slices)
    twisted = apply_twist(ring, kerfed)
    final_slices = apply_herringbone_engine(ring, twisted)
    batch.slices = final_slices

    return _slice_batch_to_dict(batch)


@router.get("/patterns", response_model=RosettePatternsListResponse)
def list_rosette_patterns() -> RosettePatternsListResponse:
    """
    Lists 'rosette' patterns stored in the PatternStore (N11.1).

    This allows the UI to fetch predefined / saved rosette patterns.
    
    Returns:
        List of rosette patterns with metadata
    """
    store = SQLitePatternStore()
    records = store.list_by_type('rosette')

    items: List[Dict[str, Any]] = []
    for r in records:
        items.append({
            "pattern_id": r.get("pattern_id"),
            "name": r.get("name"),
            "pattern_type": r.get("pattern_type"),
            "ring_count": r.get("ring_count"),
            "rosette_geometry": r.get("rosette_geometry"),
            "metadata": r.get("metadata"),
        })

    return RosettePatternsListResponse(patterns=items)


@router.post("/preview", response_model=PreviewResponse)
def preview_rosette(payload: PreviewRequest) -> PreviewResponse:
    """
    N12.2: Multi-ring preview endpoint.

    - Accepts pattern_id (optional) and an array of ring configs.
    - Uses N12 ring engine to compute segmentation + slices for each ring.
    - Feeds data into build_preview_snapshot to get a multi-ring summary.
    - Returns a simple summary payload with tile_count & slice_count per ring.
    
    Args:
        payload: Preview request with rings array
    
    Returns:
        Preview response with ring summaries
    """
    ring_cfgs = payload.rings or []

    # Convert RingConfig → RosetteRingConfig
    ring_objs: List[RosetteRingConfig] = []
    for idx, rc in enumerate(ring_cfgs):
        ring_objs.append(
            RosetteRingConfig(
                ring_id=rc.ring_id if rc.ring_id is not None else idx,
                radius_mm=rc.radius_mm,
                width_mm=rc.width_mm,
                tile_length_mm=rc.tile_length_mm,
                kerf_mm=rc.kerf_mm,
                herringbone_angle_deg=rc.herringbone_angle_deg,
                twist_angle_deg=rc.twist_angle_deg,
            )
        )

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

    summaries: List[PreviewRingSummary] = []
    for r in payload_rings:
        summaries.append(
            PreviewRingSummary(
                ring_id=r.get("ring_id", 0),
                radius_mm=r.get("radius_mm", 0.0),
                width_mm=r.get("width_mm", 0.0),
                tile_count=r.get("tile_count", 0),
                slice_count=r.get("slice_count", 0),
            )
        )

    return PreviewResponse(
        pattern_id=snapshot.pattern_id,
        rings=summaries,
    )


# ========== N16.3 CNC Helper Functions ==========

def _build_cnc_inputs_from_payload(
    payload: CNCExportRequest,
) -> tuple[RosetteRingConfig, SliceBatch, MaterialType, JigAlignment, MachineEnvelope]:
    """
    N16.3 - Shared helper to convert CNCExportRequest payload into
    the inputs required by build_ring_cnc_export.

    This mirrors the same mapping used in export_cnc_for_ring.
    Adjust the field access if your request model differs.
    """
    # Ring
    ring_model = payload.ring
    ring_cfg = RosetteRingConfig(
        ring_id=ring_model.ring_id or 0,
        radius_mm=ring_model.radius_mm,
        width_mm=ring_model.width_mm,
        tile_length_mm=ring_model.tile_length_mm,
        kerf_mm=ring_model.kerf_mm,
        herringbone_angle_deg=ring_model.herringbone_angle_deg,
        twist_angle_deg=ring_model.twist_angle_deg,
    )

    # SliceBatch
    batch_json = payload.slice_batch
    ring_id = batch_json.get("ring_id", ring_cfg.ring_id)
    slices_json = batch_json.get("slices", [])

    slices: List[Slice] = []
    for s in slices_json:
        slices.append(
            Slice(
                slice_index=s.get("slice_index", 0),
                tile_index=s.get("tile_index", 0),
                angle_raw_deg=s.get("angle_raw_deg", s.get("angle_deg", 0.0)),
                angle_final_deg=s.get("angle_final_deg", s.get("angle_deg", 0.0)),
                theta_start_deg=s.get("theta_start_deg", 0.0),
                theta_end_deg=s.get("theta_end_deg", 0.0),
                kerf_mm=s.get("kerf_mm", ring_model.kerf_mm),
                herringbone_flip=s.get("herringbone_flip", False),
                herringbone_angle_deg=s.get("herringbone_angle_deg", ring_model.herringbone_angle_deg),
                twist_angle_deg=s.get("twist_angle_deg", ring_model.twist_angle_deg),
            )
        )

    slice_batch = SliceBatch(
        batch_id=batch_json.get("batch_id", f"slice_batch_ring_{ring_id}"),
        ring_id=ring_id,
        slices=slices,
    )

    # Material
    material: MaterialType = payload.material

    # Jig alignment
    jig_model = payload.jig_alignment
    jig = JigAlignment(
        origin_x_mm=jig_model.origin_x_mm,
        origin_y_mm=jig_model.origin_y_mm,
        rotation_deg=jig_model.rotation_deg,
    )

    # Machine envelope
    if payload.envelope is not None:
        env_model = payload.envelope
        envelope = MachineEnvelope(
            x_min_mm=env_model.x_min_mm,
            x_max_mm=env_model.x_max_mm,
            y_min_mm=env_model.y_min_mm,
            y_max_mm=env_model.y_max_mm,
            z_min_mm=env_model.z_min_mm,
            z_max_mm=env_model.z_max_mm,
        )
    else:
        # Fallback envelope
        envelope = MachineEnvelope()

    return ring_cfg, slice_batch, material, jig, envelope


# ========== N14.1 + N10/N14 CNC Export Endpoint ==========

@router.post("/export-cnc", response_model=CNCExportResponse)
def export_cnc_for_ring(payload: CNCExportRequest) -> CNCExportResponse:
    """
    N14.1 + N10/N14 + N14.x: Per-ring CNC export endpoint with JobLog, LiveMonitor, and operator report.

    Steps:
      1) Rebuild RosetteRingConfig and SliceBatch from the request.
      2) Create a JobLog entry (status='running').
      3) Build toolpaths, safety decision, export bundle, and simulation.
      4) Generate operator report Markdown.
      5) Update JobLog with results + report (status='completed' or 'failed').
      6) Emit a LiveMonitor 'rosette_cnc_export' event.
    """
    # 1) Rebuild ring config from request
    rc = payload.ring
    ring_cfg = RosetteRingConfig(
        ring_id=rc.ring_id or 0,
        radius_mm=rc.radius_mm,
        width_mm=rc.width_mm,
        tile_length_mm=rc.tile_length_mm,
        kerf_mm=rc.kerf_mm,
        herringbone_angle_deg=rc.herringbone_angle_deg,
        twist_angle_deg=rc.twist_angle_deg,
    )

    # 2) Rebuild SliceBatch from incoming slice_batch JSON
    batch_json = payload.slice_batch
    ring_id = batch_json.get("ring_id", ring_cfg.ring_id)
    slices_json = batch_json.get("slices", [])

    slices: List[Slice] = []
    for s in slices_json:
        slices.append(
            Slice(
                slice_index=s.get("slice_index", 0),
                tile_index=s.get("tile_index", 0),
                angle_raw_deg=s.get("angle_raw_deg", s.get("angle_deg", 0.0)),
                angle_final_deg=s.get("angle_final_deg", s.get("angle_deg", 0.0)),
                theta_start_deg=s.get("theta_start_deg", 0.0),
                theta_end_deg=s.get("theta_end_deg", 0.0),
                kerf_mm=s.get("kerf_mm", rc.kerf_mm),
                herringbone_flip=s.get("herringbone_flip", False),
                herringbone_angle_deg=s.get("herringbone_angle_deg", rc.herringbone_angle_deg),
                twist_angle_deg=s.get("twist_angle_deg", rc.twist_angle_deg),
            )
        )

    slice_batch = SliceBatch(
        batch_id=batch_json.get("batch_id", f"slice_batch_ring_{ring_id}"),
        ring_id=ring_id,
        slices=slices,
    )

    # 3) Build JigAlignment and MachineEnvelope
    ja = payload.jig_alignment
    jig = JigAlignment(
        origin_x_mm=ja.origin_x_mm,
        origin_y_mm=ja.origin_y_mm,
        rotation_deg=ja.rotation_deg,
    )

    if payload.envelope is not None:
        env_model = payload.envelope
        envelope = MachineEnvelope(
            x_min_mm=env_model.x_min_mm,
            y_min_mm=env_model.y_min_mm,
            z_min_mm=env_model.z_min_mm,
            x_max_mm=env_model.x_max_mm,
            y_max_mm=env_model.y_max_mm,
            z_max_mm=env_model.z_max_mm,
        )
    else:
        envelope = MachineEnvelope()

    # 4) Create JobLog entry (status='running')
    joblog = SQLiteJobLogStore()
    jig_origin_dict = {
        "origin_x_mm": jig.origin_x_mm,
        "origin_y_mm": jig.origin_y_mm,
        "rotation_deg": jig.rotation_deg,
    }
    envelope_dict = {
        "x_min_mm": envelope.x_min_mm,
        "y_min_mm": envelope.y_min_mm,
        "z_min_mm": envelope.z_min_mm,
        "x_max_mm": envelope.x_max_mm,
        "y_max_mm": envelope.y_max_mm,
        "z_max_mm": envelope.z_max_mm,
    }

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

    except Exception as exc:
        # Best-effort: mark job failed and rethrow
        joblog.complete_job_with_results(
            job_id=job_id,
            status="failed",
            results={"error": str(exc)},
        )
        raise

    # 9) Flatten into response model (includes operator report)
    segments = [
        CNCSegmentModel(
            x_start_mm=seg.x_start_mm,
            y_start_mm=seg.y_start_mm,
            z_start_mm=seg.z_start_mm,
            x_end_mm=seg.x_end_mm,
            y_end_mm=seg.y_end_mm,
            z_end_mm=seg.z_end_mm,
            feed_mm_per_min=seg.feed_mm_per_min,
        )
        for seg in export_bundle.toolpaths.segments
    ]

    safety = CNCSafetyModel(
        decision=export_bundle.safety_decision.decision,
        risk_level=export_bundle.safety_decision.risk_level,
        requires_override=export_bundle.safety_decision.requires_override,
        reasons=list(export_bundle.safety_decision.reasons),
    )

    simulation = CNCSimulationModel(
        passes=sim_result.passes,
        estimated_runtime_sec=sim_result.estimated_runtime_sec,
        max_feed_mm_per_min=sim_result.max_feed_mm_per_min,
        envelope_ok=sim_result.envelope_ok,
    )

    jig_model = JigAlignmentModel(
        origin_x_mm=jig.origin_x_mm,
        origin_y_mm=jig.origin_y_mm,
        rotation_deg=jig.rotation_deg,
    )

    return CNCExportResponse(
        job_id=job_id,
        ring_id=export_bundle.ring_id,
        toolpaths=segments,
        jig_alignment=jig_model,
        safety=safety,
        simulation=simulation,
        metadata=export_bundle.metadata,
        operator_report_md=operator_report_md,
    )


# ========== N16.3 G-code Export Endpoint ==========

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
    """
    N16.3+N16.4+N16.5+N16.7 - Per-ring G-code export with:
      - material-specific spindle presets (N16.4),
      - machine post profile (GRBL / FANUC) (N16.5),
      - hardware-tuned machine configs (N16.7),
      - basic tool change (Tn M6) and header/footer templates.

    Behavior:
      - If machine_id is provided and known, it selects the MachineConfig,
        which defines profile, safe Z, default tool, and default program number.
      - Query parameters tool_id and program_number override machine defaults.
      - If machine_id is not provided, the older profile/tool_id/program_number
        behavior is used with a generic safe Z.
    """
    # Build CNC inputs identical to /export-cnc
    ring_cfg, slice_batch, material, jig, envelope = _build_cnc_inputs_from_payload(
        payload
    )

    # Build toolpaths using the full N16.x stack
    export_bundle, sim_result = build_ring_cnc_export(
        ring=ring_cfg,
        slice_batch=slice_batch,
        material=material,
        jig_alignment=jig,
        envelope=envelope,
    )

    # Material-specific spindle + depth, via FeedRule (N16.4)
    feed_rule = select_material_feed_rule(material)

    # Resolve machine config (if any) (N16.7)
    machine_cfg = None
    if machine_id is not None:
        machine_cfg = get_machine_config(machine_id)
        if machine_cfg is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown machine_id '{machine_id}'",
            )

    # Effective profile (N16.7: machine config overrides generic profile)
    if machine_cfg is not None:
        effective_profile = machine_cfg.profile
        effective_safe_z = machine_cfg.default_safe_z_mm
        effective_tool_id = tool_id if tool_id != 1 else machine_cfg.default_tool_id
        effective_program_number = (
            program_number
            if program_number is not None
            else machine_cfg.default_program_number
        )
    else:
        effective_profile = profile
        effective_safe_z = 5.0  # generic safe Z fallback
        effective_tool_id = tool_id
        effective_program_number = program_number

    post = GCodePostConfig(
        profile=effective_profile,
        program_number=effective_program_number,
        safe_z_mm=effective_safe_z,
        spindle_rpm=feed_rule.spindle_rpm,  # N16.4: material-specific spindle
        tool_id=effective_tool_id,
    )

    gcode_text = generate_gcode_from_toolpaths(
        plan=export_bundle.toolpaths,
        post=post,
    )

    # Compose filename with ring + profile (+ machine_id if present)
    suffix = effective_profile.value
    if machine_cfg is not None:
        suffix = f"{machine_cfg.machine_id}_{suffix}"
    filename = f"rosette_ring_{ring_cfg.ring_id}_{suffix}.gcode"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(
        content=gcode_text,
        media_type="text/plain",
        headers=headers,
    )


# ========== Bundle #11: Operator Report PDF Download ==========

@router.get("/operator-report-pdf/{job_id}")
def download_operator_report_pdf(job_id: str) -> Response:
    """
    Bundle #11 - Download Operator Report as PDF.

    Given a rosette CNC export job_id, this endpoint:
      - fetches the JobLog entry,
      - reads results['operator_report_md'],
      - renders it to PDF bytes,
      - returns as an application/pdf response.

    If the job or report is missing, a 404 is returned.

    Example:
        GET /api/rmos/rosette/operator-report-pdf/JOB-ROSETTE-20251201-153045-abc123
        → downloads "rmos_operator_report_JOB-ROSETTE-20251201-153045-abc123.pdf"
    """
    joblog = SQLiteJobLogStore()
    job = joblog.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["job_type"] != JOB_TYPE_ROSETTE_CNC_EXPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not a rosette CNC export job",
        )

    operator_report_md = None
    if isinstance(job["results"], dict):
        operator_report_md = job["results"].get("operator_report_md")

    if not operator_report_md:
        raise HTTPException(
            status_code=404,
            detail="Operator report not found for this job",
        )

    # Render Markdown → PDF
    pdf_bytes = markdown_to_pdf_bytes(
        markdown_text=operator_report_md,
        title=f"RMOS Operator Report – Job {job_id}",
    )

    filename = f"rmos_operator_report_{job_id}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


# ========== Bundle #13 (Part A): CNC History Endpoint ==========

class CNCHistoryItem(BaseModel):
    """Single CNC export job history item."""
    job_id: str
    created_at: Optional[datetime] = None
    status: str
    ring_id: Optional[int] = None
    material: Optional[str] = None
    safety_decision: Optional[str] = None
    safety_risk_level: Optional[str] = None
    runtime_sec: Optional[float] = None
    pattern_id: Optional[str] = None


class CNCHistoryResponse(BaseModel):
    """Response containing list of CNC export history items."""
    items: List[CNCHistoryItem]


class CNCToolpathStatsModel(BaseModel):
    """Toolpath statistics for CNC job detail."""
    segment_count: int
    origin_x_mm: float | None = None
    origin_y_mm: float | None = None
    rotation_deg: float | None = None


class CNCJobDetailResponse(BaseModel):
    """Complete details for a single CNC export job."""
    job_id: str
    pattern_id: str | None
    status: str
    ring_id: int | None
    material: str | None
    created_at: datetime | None = None

    safety: CNCSafetyModel | None = None
    simulation: CNCSimulationModel | None = None
    toolpath_stats: CNCToolpathStatsModel | None = None

    operator_report_md: str | None = None
    metadata: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}


@router.get("/cnc-history", response_model=CNCHistoryResponse)
def get_cnc_history(limit: int = 50) -> CNCHistoryResponse:
    """
    Bundle #13 (Part A) - RMOS Studio CNC history endpoint.

    Returns recent rosette CNC export jobs from JobLog with summarized fields.
    
    Example:
        GET /api/rmos/rosette/cnc-history?limit=100
    """
    store = SQLiteJobLogStore()
    jobs = store.list_rosette_cnc_exports(limit=limit)

    items: List[CNCHistoryItem] = []

    for job in jobs:
        params = job.get("parameters") or {}
        results = job.get("results") or {}

        ring_id = params.get("ring_id")
        material = params.get("material")

        safety = results.get("safety", {}) if isinstance(results, dict) else {}
        sim = results.get("simulation", {}) if isinstance(results, dict) else {}

        safety_decision = safety.get("decision")
        safety_risk_level = safety.get("risk_level")
        runtime_sec = sim.get("estimated_runtime_sec")

        # Try to extract created_at from job record
        created_at: Optional[datetime] = None
        created_at_val = job.get("created_at")
        if isinstance(created_at_val, str):
            try:
                created_at = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
            except Exception:
                pass

        items.append(
            CNCHistoryItem(
                job_id=job["id"],
                created_at=created_at,
                status=job.get("status", "unknown"),
                ring_id=ring_id,
                material=material,
                safety_decision=safety_decision,
                safety_risk_level=safety_risk_level,
                runtime_sec=runtime_sec,
                pattern_id=job.get("pattern_id"),
            )
        )

    return CNCHistoryResponse(items=items)


@router.get("/cnc-job/{job_id}", response_model=CNCJobDetailResponse)
def get_cnc_job_detail(job_id: str) -> CNCJobDetailResponse:
    """
    CNC Job detail endpoint.
    
    Bundle #13 (Part A+) - Returns complete details for a single CNC export job.

    Returns:
      - status, ring_id, material
      - safety + simulation
      - toolpath stats (segment_count, origin)
      - operator_report_md
      - raw metadata + parameters
    """
    store = JobLogStore()
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.job_type != JOB_TYPE_ROSETTE_CNC_EXPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not a rosette CNC export job",
        )

    params = job.parameters or {}
    results = job.results or {}

    ring_id = params.get("ring_id")
    material = params.get("material")

    safety_dict = results.get("safety") if isinstance(results, dict) else None
    sim_dict = results.get("simulation") if isinstance(results, dict) else None
    metadata = results.get("metadata") if isinstance(results, dict) else {}
    operator_report_md = (
        results.get("operator_report_md") if isinstance(results, dict) else None
    )

    # Safety
    safety: CNCSafetyModel | None = None
    if isinstance(safety_dict, dict):
        safety = CNCSafetyModel(
            decision=safety_dict.get("decision", ""),
            risk_level=safety_dict.get("risk_level", ""),
            requires_override=bool(safety_dict.get("requires_override", False)),
            reasons=list(safety_dict.get("reasons", []) or []),
        )

    # Simulation
    simulation: CNCSimulationModel | None = None
    if isinstance(sim_dict, dict):
        simulation = CNCSimulationModel(
            passes=sim_dict.get("passes", 0),
            estimated_runtime_sec=sim_dict.get("estimated_runtime_sec", 0.0),
            max_feed_mm_per_min=sim_dict.get("max_feed_mm_per_min", 0.0),
            envelope_ok=bool(sim_dict.get("envelope_ok", True)),
        )

    # Toolpath stats from metadata
    origin = metadata.get("origin", {}) if isinstance(metadata, dict) else {}
    segment_count = metadata.get("segment_count", 0) if isinstance(metadata, dict) else 0
    tool_stats = CNCToolpathStatsModel(
        segment_count=segment_count,
        origin_x_mm=origin.get("origin_x_mm"),
        origin_y_mm=origin.get("origin_y_mm"),
        rotation_deg=origin.get("rotation_deg"),
    )

    # created_at: if/when you start storing it in results or params
    created_at_val = results.get("created_at") if isinstance(results, dict) else None
    created_at: datetime | None = None
    if isinstance(created_at_val, str):
        try:
            created_at = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
        except Exception:
            created_at = None

    return CNCJobDetailResponse(
        job_id=job.job_id,
        pattern_id=job.pattern_id,
        status=job.status,
        ring_id=ring_id,
        material=material,
        created_at=created_at,
        safety=safety,
        simulation=simulation,
        toolpath_stats=tool_stats,
        operator_report_md=operator_report_md,
        metadata=metadata if isinstance(metadata, dict) else {},
        parameters=params if isinstance(params, dict) else {},
    )
