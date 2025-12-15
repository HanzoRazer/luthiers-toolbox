# Patch N14.1 + N14.x + Bundle #13 (Part B) + N16.1 + N16.2 - Rosette → CNC wiring (per-ring export)
#
# This module bridges the N12 rosette geometry (SliceBatch, RosetteRingConfig)
# with the N14 CNC core skeleton (toolpaths, safety, export bundle).
#
# N14.1 behavior:
#   - Uses a simple linear toolpath builder (diagonal segments by index).
#   - Safety only checks the machine envelope.
#   - Simulation uses a heuristic runtime estimator.
#
# N14.x additions:
#   - Operator report generation (Markdown checklist)
#
# Bundle #13 (Part B):
#   - Advanced safety: kerf drift limits, feed rate validation
#   - Wire kerf physics into safety evaluation
#
# N16.1 (Bundle #2):
#   - Switch to build_ring_arc_toolpaths for accurate circular chord geometry
#   - Add Z-depth computation based on ring width
#   - Enrich metadata with origin and segment_count for UI/JobLog consumers
#
# N16.2 (Bundle #3):
#   - Multi-pass Z stepping (2-4 passes down to target depth)
#   - Each pass is full ring toolpath at shallower Z
#   - Adds z_passes_mm and target_depth_mm to metadata
#
# Later N14.x patches will:
#   - Add G-code text generation.

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any, Tuple, Optional

from .models import RosetteRingConfig, SliceBatch
from .cnc import (
    MaterialType,
    select_feed_rule,
    select_material_feed_rule,  # N16.4 NEW
    JigAlignment,
    MachineEnvelope,
    build_linear_toolpaths,  # kept for backward compatibility
    build_ring_arc_toolpaths,  # N16.1
    build_ring_arc_toolpaths_multipass,  # N16.2
    evaluate_cnc_safety,
    build_export_bundle_skeleton,
    simulate_toolpaths,
    CNCExportBundle,
    CNCSimulationResult,
    compute_kerf_physics,
)
from ...reports.operator_report import build_operator_markdown_report


def _compute_cut_depth_mm(
    ring: RosetteRingConfig,
    material: MaterialType,
) -> float:
    """
    N16.1 - Simple heuristic for Z cut depth.

    For now:
      - Use half of ring width (assuming width_mm ~ inlay width),
      - Clamp to a max of 2.0 mm depth for safety,
      - Negative Z means "into" the material.

    This is intentionally conservative and can be replaced with a
    more sophisticated rule later or made user-configurable.
    """
    width_mm = float(getattr(ring, "width_mm", 1.0) or 1.0)
    nominal_depth = width_mm * 0.5
    depth = min(nominal_depth, 2.0)
    return -depth


def _compute_z_passes_mm(
    total_depth_mm: float,
    max_step_mm: float = 0.6,
) -> list[float]:
    """
    N16.2 - Compute a list of Z depths for multi-pass cutting.

    total_depth_mm: negative number (e.g., -1.8)
    max_step_mm:    positive "per pass" limit (default 0.6 mm)

    Strategy:
      - Determine how many passes are needed so that each pass
        removes <= max_step_mm of depth.
      - Distribute depths evenly from shallow to final depth.
      - All depths are negative (Z "into" material).

    Example:
      total_depth_mm=-1.5, max_step_mm=0.6 → 3 passes at [-0.5, -1.0, -1.5]
    """
    if total_depth_mm >= 0:
        # No cutting or invalid input; just return the same depth once
        return [total_depth_mm]

    depth_abs = abs(total_depth_mm)
    if depth_abs <= max_step_mm:
        return [total_depth_mm]

    # How many passes do we need?
    from math import ceil

    num_passes = max(2, int(ceil(depth_abs / max_step_mm)))
    step = depth_abs / float(num_passes)

    depths: list[float] = []
    for i in range(1, num_passes + 1):
        z = -step * i
        # Ensure we don't exceed the target depth
        if abs(z) > depth_abs:
            z = -depth_abs
        depths.append(z)

    return depths


def build_ring_cnc_export(
    ring: RosetteRingConfig,
    slice_batch: SliceBatch,
    material: MaterialType,
    jig_alignment: JigAlignment,
    envelope: MachineEnvelope,
) -> Tuple[CNCExportBundle, CNCSimulationResult]:
    """
    Build a CNCExportBundle + simulation result for a single rosette ring.

    N16.2:
      - Computes a target Z depth and then a list of Z passes (multi-pass),
      - Uses build_ring_arc_toolpaths_multipass to generate toolpaths,
      - Keeps safety, kerf physics, and metadata wiring intact.

    Inputs:
      - ring:           RosetteRingConfig for the ring being exported
      - slice_batch:    SliceBatch from N12 geometry pipeline
      - material:       MaterialType (hardwood, softwood, composite)
      - jig_alignment:  JigAlignment describing origin and rotation
      - envelope:       MachineEnvelope for safety checks

    Outputs:
      - CNCExportBundle
      - CNCSimulationResult
    """
    # 1) Select feed rule for the material (N16.4: includes spindle_rpm and max_z_step_mm)
    feed_rule = select_material_feed_rule(material)
    feed = feed_rule.feed_recommend_mm_per_min

    # 2) Convert SliceBatch.slices into list[dict] for the arc toolpath builder
    slices_dicts: list[Dict[str, Any]] = [asdict(s) for s in slice_batch.slices]

    # 3) Compute target Z depth (negative) and multi-pass depths using material-specific step
    target_depth_mm = _compute_cut_depth_mm(ring, material)
    z_passes_mm = _compute_z_passes_mm(
        total_depth_mm=target_depth_mm,
        max_step_mm=feed_rule.max_z_step_mm,  # N16.4: material-specific depth limit
    )

    # 4) Build multi-pass arc-based toolpaths
    toolpaths = build_ring_arc_toolpaths_multipass(
        ring_id=ring.ring_id,
        slices=slices_dicts,
        ring_radius_mm=ring.radius_mm,
        feed_mm_per_min=feed,
        origin_x_mm=jig_alignment.origin_x_mm,
        origin_y_mm=jig_alignment.origin_y_mm,
        rotation_deg=jig_alignment.rotation_deg,
        z_passes_mm=z_passes_mm,
    )

    # 5) Compute kerf physics for this ring (using number of slices)
    kerf = compute_kerf_physics(
        kerf_mm=ring.kerf_mm,
        radius_mm=ring.radius_mm,
        tile_count=len(slice_batch.slices) or None,
    )

    # 6) Evaluate safety with envelope + feed + kerf drift
    safety_decision = evaluate_cnc_safety(
        toolpaths=toolpaths,
        envelope=envelope,
        kerf_result=kerf,
        safe_feed_max_mm_per_min=feed_rule.feed_max_mm_per_min,
        max_drift_deg=2.0,  # baseline drift limit; can be tuned per material
    )

    # 7) Build export bundle
    export_bundle = build_export_bundle_skeleton(
        ring_id=ring.ring_id,
        toolpaths=toolpaths,
        jig_alignment=jig_alignment,
        safety_decision=safety_decision,
    )

    # Enrich metadata for downstream consumers (UI, JobLog, reports)
    meta = export_bundle.metadata or {}
    origin_meta = {
        "origin_x_mm": jig_alignment.origin_x_mm,
        "origin_y_mm": jig_alignment.origin_y_mm,
        "rotation_deg": jig_alignment.rotation_deg,
    }
    meta.setdefault("origin", origin_meta)
    meta["segment_count"] = len(toolpaths.segments)
    meta["z_passes_mm"] = z_passes_mm
    meta["target_depth_mm"] = target_depth_mm
    export_bundle.metadata = meta

    # 8) Run simulation
    simulation_result = simulate_toolpaths(toolpaths)

    return export_bundle, simulation_result


def build_ring_operator_report_md(
    job_id: Optional[str],
    export_bundle: CNCExportBundle,
    simulation: CNCSimulationResult,
    pattern_id: Optional[str] = None,
) -> str:
    """
    Convenience wrapper so higher layers can request an operator report
    without importing the reports module directly.

    Args:
        job_id: JobLog ID for traceability
        export_bundle: CNC export bundle with toolpaths, safety, metadata
        simulation: Simulation results with runtime estimates
        pattern_id: Optional pattern identifier

    Returns:
        Markdown-formatted operator checklist

    Example:
        report = build_ring_operator_report_md(
            job_id="JOB-ROSETTE-20251201-123456-abc123",
            export_bundle=bundle,
            simulation=sim_result,
            pattern_id="rosette_001"
        )
    """
    return build_operator_markdown_report(
        job_id=job_id,
        export_bundle=export_bundle,
        simulation=simulation,
        pattern_id=pattern_id,
    )
