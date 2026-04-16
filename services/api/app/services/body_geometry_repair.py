"""
Body Geometry Repair — Phase 6 CAD Geometry Reconstruction
===========================================================

Phase 6B is the first geometry-intelligence stage in the production Blueprint
Reader path. It does not improve extraction; it improves representation.

ARCHITECTURAL PRINCIPLES (do not violate):
    1. This is a POST-BODY reconstruction stage
    2. It runs AFTER layered_dual_pass, build_layers(), and join_body_gaps()
    3. It does NOT modify extraction logic — extraction is upstream
    4. It is BODY-layer only — non-BODY layers pass through unchanged
    5. It performs CONFIDENCE-GATED geometric substitution:
       - Uses positional deviation to decide if LINE→POLYLINE is safe
       - Acceptance thresholds: mean ≤ 0.5mm, max ≤ 1.5mm
    6. It is FEATURE-FLAGGED — inactive unless explicitly enabled
    7. It preserves LINE FALLBACK for rejected or uncovered geometry
    8. It is ADDITIVE and REVERSIBLE — turn off flags to restore prior behavior

Pipeline position:
    join_body_gaps() → [THIS MODULE] → write_layered_dxf()

Feature flags (all default OFF):
    ENABLE_BODY_REPAIR=1       → Phase 6A: metrics/analysis only
    ENABLE_POLYLINE_OUTPUT=1   → Phase 6B: emit POLYLINE for accepted runs
    ENABLE_ARC_FITTING=1       → Phase 6C: arc fitting (planned)

Phase 6B output:
    - Qualified BODY runs → R12-compatible POLYLINE2D (AC1009)
    - Rejected BODY runs → LINE fallback (unchanged)
    - Non-BODY layers → LINE (unchanged)

Author: Production Shop
Date: 2026-04-15
"""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from .layer_builder import LayeredEntities, LayeredEntity, Layer
from ..cam.unified_dxf_cleaner import Chain, Point

logger = logging.getLogger(__name__)


# ─── Feature Flags ─────────────────────────────────────────────────────────────

def is_body_repair_enabled() -> bool:
    """Check if body repair is enabled via environment variable."""
    return os.environ.get("ENABLE_BODY_REPAIR", "0") == "1"


def is_arc_fitting_enabled() -> bool:
    """Check if arc fitting is enabled (Phase 6C)."""
    return os.environ.get("ENABLE_ARC_FITTING", "0") == "1"


def is_polyline_output_enabled() -> bool:
    """Check if polyline output is enabled (Phase 6B)."""
    return os.environ.get("ENABLE_POLYLINE_OUTPUT", "0") == "1"


# ─── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class ReconstructedPrimitive:
    """
    A CAD primitive detected during geometry repair.

    Phase 6A: Used for metrics/candidates only, not written to DXF yet.
    """
    kind: Literal["line", "polyline", "arc", "circle"]
    layer: str
    points: Optional[List[Tuple[float, float]]] = None  # For line/polyline
    center: Optional[Tuple[float, float]] = None        # For arc/circle
    radius: Optional[float] = None                       # For arc/circle
    start_angle: Optional[float] = None                  # For arc (degrees)
    end_angle: Optional[float] = None                    # For arc (degrees)
    source_contour_id: Optional[int] = None
    mean_error_mm: Optional[float] = None                # Fit quality
    max_error_mm: Optional[float] = None


@dataclass
class PolylineRun:
    """A consolidated polyline run detected in a contour."""
    points: List[Tuple[float, float]]
    start_idx: int
    end_idx: int
    point_count: int

    # Phase 6B: Positional deviation metrics (mm)
    mean_deviation_mm: float = 0.0
    max_deviation_mm: float = 0.0
    accepted: bool = False

    @property
    def segment_count(self) -> int:
        return max(0, self.point_count - 1)


@dataclass
class ArcCandidate:
    """A potential arc detected in a contour segment."""
    center: Tuple[float, float]
    radius: float
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    start_angle: float  # degrees
    end_angle: float    # degrees
    point_count: int
    mean_error_mm: float
    max_error_mm: float
    valid: bool


@dataclass
class BodyRepairMetrics:
    """Metrics from body geometry repair analysis."""
    contour_count: int = 0
    total_points: int = 0
    chain_conversion_ok: bool = True

    # Polyline metrics
    polyline_runs_detected: int = 0
    polyline_total_points: int = 0
    avg_run_length: float = 0.0

    # Phase 6B: Acceptance metrics
    polyline_runs_accepted: int = 0
    polyline_runs_rejected: int = 0
    accepted_points_total: int = 0
    mean_deviation_accepted_mm: float = 0.0
    max_deviation_accepted_mm: float = 0.0

    # Arc metrics
    arc_candidates_detected: int = 0
    arc_candidates_valid: int = 0
    mean_arc_error_mm: float = 0.0
    max_arc_error_mm: float = 0.0

    # Summary
    line_segments_original: int = 0
    potential_reduction_pct: float = 0.0
    actual_reduction_pct: float = 0.0  # Phase 6B: with acceptance filter

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contour_count": self.contour_count,
            "total_points": self.total_points,
            "chain_conversion_ok": self.chain_conversion_ok,
            "polyline_runs_detected": self.polyline_runs_detected,
            "polyline_total_points": self.polyline_total_points,
            "avg_run_length": round(self.avg_run_length, 2),
            "polyline_runs_accepted": self.polyline_runs_accepted,
            "polyline_runs_rejected": self.polyline_runs_rejected,
            "accepted_points_total": self.accepted_points_total,
            "mean_deviation_accepted_mm": round(self.mean_deviation_accepted_mm, 3),
            "max_deviation_accepted_mm": round(self.max_deviation_accepted_mm, 3),
            "arc_candidates_detected": self.arc_candidates_detected,
            "arc_candidates_valid": self.arc_candidates_valid,
            "mean_arc_error_mm": round(self.mean_arc_error_mm, 3),
            "max_arc_error_mm": round(self.max_arc_error_mm, 3),
            "line_segments_original": self.line_segments_original,
            "potential_reduction_pct": round(self.potential_reduction_pct, 1),
            "actual_reduction_pct": round(self.actual_reduction_pct, 1),
        }


@dataclass
class BodyRepairResult:
    """Result from body geometry repair."""
    applied: bool
    phase: str = "6A_validation"
    layered: Optional[LayeredEntities] = None  # Unchanged for Phase 6A
    primitives: List[ReconstructedPrimitive] = field(default_factory=list)
    accepted_primitives: List[ReconstructedPrimitive] = field(default_factory=list)
    metrics: BodyRepairMetrics = field(default_factory=BodyRepairMetrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": self.applied,
            "phase": self.phase,
            "dxf_output_changed": self.phase == "6B_polyline_output" and len(self.accepted_primitives) > 0,
            "primitive_count": len(self.primitives),
            "accepted_primitive_count": len(self.accepted_primitives),
            "metrics": self.metrics.to_dict(),
        }


# ─── Coordinate Conversion ─────────────────────────────────────────────────────

def contour_to_chain(contour: np.ndarray, mm_per_px: float) -> Chain:
    """
    Convert OpenCV contour to Chain in mm coordinates.

    Args:
        contour: np.ndarray shape (N, 1, 2) in pixel coordinates
        mm_per_px: Scale factor (mm per pixel)

    Returns:
        Chain with points in mm coordinates
    """
    # Reshape contour from (N, 1, 2) to (N, 2)
    pts = contour.reshape(-1, 2)

    # Convert to mm and create Points
    points = [
        Point(x=float(pt[0]) * mm_per_px, y=float(pt[1]) * mm_per_px)
        for pt in pts
    ]

    return Chain(points=points)


def chain_to_contour(chain: Chain, mm_per_px: float) -> np.ndarray:
    """
    Convert Chain back to OpenCV contour in pixel coordinates.

    Args:
        chain: Chain with points in mm coordinates
        mm_per_px: Scale factor (mm per pixel)

    Returns:
        np.ndarray shape (N, 1, 2) in pixel coordinates
    """
    if mm_per_px <= 0:
        mm_per_px = 1.0  # Safety fallback

    pts = np.array([
        [p.x / mm_per_px, p.y / mm_per_px]
        for p in chain.points
    ], dtype=np.float32)

    # Reshape to OpenCV format (N, 1, 2)
    return pts.reshape(-1, 1, 2)


def validate_roundtrip(contour: np.ndarray, mm_per_px: float, tolerance_px: float = 0.5) -> bool:
    """
    Validate contour → chain → contour round-trip preserves geometry.

    Args:
        contour: Original contour
        mm_per_px: Scale factor
        tolerance_px: Maximum allowed deviation in pixels

    Returns:
        True if round-trip is within tolerance
    """
    chain = contour_to_chain(contour, mm_per_px)
    reconstructed = chain_to_contour(chain, mm_per_px)

    # Compare point counts
    if contour.shape[0] != reconstructed.shape[0]:
        return False

    # Compare coordinates
    original_pts = contour.reshape(-1, 2)
    recon_pts = reconstructed.reshape(-1, 2)

    max_deviation = np.max(np.abs(original_pts - recon_pts))
    return max_deviation < tolerance_px


# ─── Polyline Consolidation ────────────────────────────────────────────────────

def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Return angle in degrees between two vectors.
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 < 1e-8 or norm2 < 1e-8:
        return 180.0  # Degenerate case

    v1_norm = v1 / norm1
    v2_norm = v2 / norm2

    dot = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    return float(np.degrees(np.arccos(dot)))


def detect_polyline_runs(
    chain: Chain,
    dist_tol_mm: float = 0.75,
    angle_tol_deg: float = 12.0,
) -> List[PolylineRun]:
    """
    Detect contiguous polyline runs in a chain.

    A run is a sequence of points where:
    - Adjacent points are within dist_tol_mm
    - Angular deviation between consecutive segments is within angle_tol_deg

    Args:
        chain: Input chain in mm coordinates
        dist_tol_mm: Maximum distance between consecutive points
        angle_tol_deg: Maximum angular deviation between segments

    Returns:
        List of detected polyline runs
    """
    points = [(p.x, p.y) for p in chain.points]

    if len(points) < 3:
        if len(points) >= 2:
            return [PolylineRun(
                points=points,
                start_idx=0,
                end_idx=len(points) - 1,
                point_count=len(points),
            )]
        return []

    runs = []
    current_run_start = 0
    current_run_points = [points[0], points[1]]

    for i in range(2, len(points)):
        p_prev2 = np.array(current_run_points[-2])
        p_prev = np.array(current_run_points[-1])
        p_curr = np.array(points[i])

        # Check distance continuity
        dist = np.linalg.norm(p_curr - p_prev)
        if dist > dist_tol_mm:
            # Break: distance exceeded
            runs.append(PolylineRun(
                points=current_run_points.copy(),
                start_idx=current_run_start,
                end_idx=i - 1,
                point_count=len(current_run_points),
            ))
            current_run_start = i - 1
            current_run_points = [tuple(p_prev), tuple(p_curr)]
            continue

        # Check angular continuity
        v1 = p_prev - p_prev2
        v2 = p_curr - p_prev

        angle = angle_between_vectors(v1, v2)

        if angle > angle_tol_deg:
            # Break: angle exceeded
            runs.append(PolylineRun(
                points=current_run_points.copy(),
                start_idx=current_run_start,
                end_idx=i - 1,
                point_count=len(current_run_points),
            ))
            current_run_start = i - 1
            current_run_points = [tuple(p_prev), tuple(p_curr)]
        else:
            # Continue run
            current_run_points.append(tuple(p_curr))

    # Add final run
    if current_run_points:
        runs.append(PolylineRun(
            points=current_run_points,
            start_idx=current_run_start,
            end_idx=len(points) - 1,
            point_count=len(current_run_points),
        ))

    return runs


# ─── Positional Deviation (Phase 6B) ──────────────────────────────────────────

def compute_positional_deviation(
    points: List[Tuple[float, float]],
) -> Tuple[float, float]:
    """
    Compute positional deviation of points from a simplified polyline.

    For a sequence of points, computes the perpendicular distance of each
    interior point to the line segment formed by start → end.

    Args:
        points: List of (x, y) coordinates in mm

    Returns:
        (mean_deviation_mm, max_deviation_mm)
    """
    if len(points) < 3:
        return 0.0, 0.0

    # Line from first to last point
    p1 = np.array(points[0])
    p2 = np.array(points[-1])
    line_vec = p2 - p1
    line_len = np.linalg.norm(line_vec)

    if line_len < 1e-8:
        # Degenerate case: start == end
        # Compute distance from each point to start
        deviations = [np.linalg.norm(np.array(p) - p1) for p in points[1:-1]]
        if not deviations:
            return 0.0, 0.0
        return float(np.mean(deviations)), float(np.max(deviations))

    # Unit vector along line
    line_unit = line_vec / line_len

    # Compute perpendicular distance for each interior point
    deviations = []
    for p in points[1:-1]:
        pt = np.array(p)
        # Vector from p1 to point
        v = pt - p1
        # Project onto line
        proj_len = np.dot(v, line_unit)
        proj_point = p1 + proj_len * line_unit
        # Perpendicular distance
        deviation = np.linalg.norm(pt - proj_point)
        deviations.append(deviation)

    if not deviations:
        return 0.0, 0.0

    return float(np.mean(deviations)), float(np.max(deviations))


def evaluate_polyline_acceptance(
    run: PolylineRun,
    mean_tol_mm: float = 0.5,
    max_tol_mm: float = 1.5,
) -> PolylineRun:
    """
    Evaluate a polyline run for acceptance as a consolidated polyline.

    Computes positional deviation and sets accepted flag if within tolerance.

    Args:
        run: PolylineRun to evaluate
        mean_tol_mm: Maximum mean deviation for acceptance
        max_tol_mm: Maximum single-point deviation for acceptance

    Returns:
        Updated PolylineRun with deviation metrics and acceptance flag
    """
    mean_dev, max_dev = compute_positional_deviation(run.points)

    run.mean_deviation_mm = mean_dev
    run.max_deviation_mm = max_dev
    run.accepted = (mean_dev <= mean_tol_mm) and (max_dev <= max_tol_mm)

    return run


# ─── Arc Fitting ───────────────────────────────────────────────────────────────

def fit_circle_3pts(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> Optional[Tuple[float, float, float]]:
    """
    Fit a circle through three points.

    Returns:
        (center_x, center_y, radius) or None if collinear
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    temp = x2 * x2 + y2 * y2
    bc = (x1 * x1 + y1 * y1 - temp) / 2
    cd = (temp - x3 * x3 - y3 * y3) / 2
    det = (x1 - x2) * (y2 - y3) - (x2 - x3) * (y1 - y2)

    if abs(det) < 1e-10:
        return None  # Collinear points

    cx = (bc * (y2 - y3) - cd * (y1 - y2)) / det
    cy = ((x1 - x2) * cd - (x2 - x3) * bc) / det
    r = math.sqrt((cx - x1) ** 2 + (cy - y1) ** 2)

    return (cx, cy, r)


def fit_arc_to_segment(
    points: List[Tuple[float, float]],
    mean_tol_mm: float = 0.5,
    max_tol_mm: float = 1.5,
) -> ArcCandidate:
    """
    Attempt to fit an arc to a segment of points.

    Uses 3-point circle fitting (start, middle, end) then validates
    all points against the fitted circle.

    Args:
        points: List of (x, y) coordinates in mm
        mean_tol_mm: Maximum mean deviation for valid arc
        max_tol_mm: Maximum single-point deviation for valid arc

    Returns:
        ArcCandidate with validity flag
    """
    if len(points) < 5:
        return ArcCandidate(
            center=(0, 0),
            radius=0,
            start_point=points[0] if points else (0, 0),
            end_point=points[-1] if points else (0, 0),
            start_angle=0,
            end_angle=0,
            point_count=len(points),
            mean_error_mm=float('inf'),
            max_error_mm=float('inf'),
            valid=False,
        )

    p1 = points[0]
    p2 = points[len(points) // 2]
    p3 = points[-1]

    result = fit_circle_3pts(p1, p2, p3)

    if result is None:
        # Collinear - not an arc
        return ArcCandidate(
            center=(0, 0),
            radius=0,
            start_point=p1,
            end_point=p3,
            start_angle=0,
            end_angle=0,
            point_count=len(points),
            mean_error_mm=float('inf'),
            max_error_mm=float('inf'),
            valid=False,
        )

    cx, cy, r = result

    # Compute deviation for all points
    errors = []
    for px, py in points:
        dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        errors.append(abs(dist - r))

    mean_err = float(np.mean(errors))
    max_err = float(np.max(errors))

    # Compute angles
    start_angle = math.degrees(math.atan2(p1[1] - cy, p1[0] - cx))
    end_angle = math.degrees(math.atan2(p3[1] - cy, p3[0] - cx))

    valid = mean_err <= mean_tol_mm and max_err <= max_tol_mm

    return ArcCandidate(
        center=(cx, cy),
        radius=r,
        start_point=p1,
        end_point=p3,
        start_angle=start_angle,
        end_angle=end_angle,
        point_count=len(points),
        mean_error_mm=mean_err,
        max_error_mm=max_err,
        valid=valid,
    )


def detect_arc_candidates(
    chain: Chain,
    min_points: int = 5,
    mean_tol_mm: float = 0.5,
    max_tol_mm: float = 1.5,
) -> List[ArcCandidate]:
    """
    Detect potential arcs in a chain.

    Slides a window across the chain and tests each segment for arc fitness.

    Args:
        chain: Input chain in mm coordinates
        min_points: Minimum points in a segment to test
        mean_tol_mm: Maximum mean deviation for valid arc
        max_tol_mm: Maximum single-point deviation

    Returns:
        List of arc candidates (valid and invalid for metrics)
    """
    points = [(p.x, p.y) for p in chain.points]

    if len(points) < min_points:
        return []

    candidates = []

    # Use polyline runs as natural segmentation
    runs = detect_polyline_runs(chain)

    for run in runs:
        if run.point_count >= min_points:
            candidate = fit_arc_to_segment(
                run.points,
                mean_tol_mm=mean_tol_mm,
                max_tol_mm=max_tol_mm,
            )
            candidates.append(candidate)

    return candidates


# ─── Main Repair Function ──────────────────────────────────────────────────────

def repair_body_geometry(
    layered: LayeredEntities,
    spec_name: Optional[str] = None,
    mean_tol_mm: float = 0.5,
    max_tol_mm: float = 1.5,
) -> BodyRepairResult:
    """
    Analyze BODY geometry for CAD reconstruction opportunities.

    Phase 6A: Validation only — computes metrics without modifying output.
    Phase 6B: Emits accepted polylines to DXF (when ENABLE_POLYLINE_OUTPUT=1).

    Args:
        layered: LayeredEntities with body contours
        spec_name: Optional instrument spec name (for future use)
        mean_tol_mm: Maximum mean deviation for polyline acceptance
        max_tol_mm: Maximum single-point deviation for polyline acceptance

    Returns:
        BodyRepairResult with metrics and candidate primitives
    """
    if not is_body_repair_enabled():
        return BodyRepairResult(
            applied=False,
            phase="disabled",
            layered=layered,
            metrics=BodyRepairMetrics(),
        )

    polyline_output = is_polyline_output_enabled()
    phase = "6B_polyline_output" if polyline_output else "6A_validation"

    metrics = BodyRepairMetrics()
    primitives: List[ReconstructedPrimitive] = []
    accepted_primitives: List[ReconstructedPrimitive] = []

    body_entities = layered.body
    mm_per_px = layered.mm_per_px

    if not body_entities or mm_per_px <= 0:
        return BodyRepairResult(
            applied=True,
            phase=phase,
            layered=layered,
            metrics=metrics,
        )

    metrics.contour_count = len(body_entities)

    all_polyline_runs: List[PolylineRun] = []
    all_arc_candidates: List[ArcCandidate] = []
    conversion_failures = 0

    for idx, entity in enumerate(body_entities):
        contour = entity.contour
        metrics.total_points += contour.shape[0]
        metrics.line_segments_original += max(0, contour.shape[0] - 1)

        # Validate round-trip conversion
        if not validate_roundtrip(contour, mm_per_px):
            conversion_failures += 1
            continue

        # Convert to chain (mm space)
        chain = contour_to_chain(contour, mm_per_px)

        # Detect polyline runs
        runs = detect_polyline_runs(chain)
        for run in runs:
            # Phase 6B: Evaluate acceptance
            run = evaluate_polyline_acceptance(run, mean_tol_mm, max_tol_mm)
            all_polyline_runs.append(run)

            # Create candidate primitive
            primitive = ReconstructedPrimitive(
                kind="polyline",
                layer="BODY",
                points=run.points,
                source_contour_id=idx,
                mean_error_mm=run.mean_deviation_mm,
                max_error_mm=run.max_deviation_mm,
            )
            primitives.append(primitive)

            # Phase 6B: Track accepted primitives
            if run.accepted:
                accepted_primitives.append(primitive)

        # Detect arc candidates (if enabled)
        if is_arc_fitting_enabled():
            candidates = detect_arc_candidates(chain)
            for candidate in candidates:
                all_arc_candidates.append(candidate)

                if candidate.valid:
                    primitives.append(ReconstructedPrimitive(
                        kind="arc",
                        layer="BODY",
                        center=candidate.center,
                        radius=candidate.radius,
                        start_angle=candidate.start_angle,
                        end_angle=candidate.end_angle,
                        source_contour_id=idx,
                        mean_error_mm=candidate.mean_error_mm,
                        max_error_mm=candidate.max_error_mm,
                    ))

    # Compute metrics
    metrics.chain_conversion_ok = conversion_failures == 0

    # Polyline metrics
    metrics.polyline_runs_detected = len(all_polyline_runs)
    metrics.polyline_total_points = sum(r.point_count for r in all_polyline_runs)
    if all_polyline_runs:
        metrics.avg_run_length = metrics.polyline_total_points / len(all_polyline_runs)

    # Phase 6B: Acceptance metrics
    accepted_runs = [r for r in all_polyline_runs if r.accepted]
    rejected_runs = [r for r in all_polyline_runs if not r.accepted]
    metrics.polyline_runs_accepted = len(accepted_runs)
    metrics.polyline_runs_rejected = len(rejected_runs)
    metrics.accepted_points_total = sum(r.point_count for r in accepted_runs)

    if accepted_runs:
        metrics.mean_deviation_accepted_mm = float(np.mean([r.mean_deviation_mm for r in accepted_runs]))
        metrics.max_deviation_accepted_mm = float(np.max([r.max_deviation_mm for r in accepted_runs]))

    # Arc metrics
    metrics.arc_candidates_detected = len(all_arc_candidates)
    metrics.arc_candidates_valid = sum(1 for c in all_arc_candidates if c.valid)

    valid_arcs = [c for c in all_arc_candidates if c.valid]
    if valid_arcs:
        metrics.mean_arc_error_mm = float(np.mean([c.mean_error_mm for c in valid_arcs]))
        metrics.max_arc_error_mm = float(np.max([c.max_error_mm for c in valid_arcs]))

    # Potential reduction: if we emitted ALL polylines instead of lines
    if metrics.line_segments_original > 0:
        potential_entities = metrics.polyline_runs_detected
        reduction = metrics.line_segments_original - potential_entities
        metrics.potential_reduction_pct = (reduction / metrics.line_segments_original) * 100

        # Actual reduction: only ACCEPTED polylines count
        # Rejected runs remain as line segments
        rejected_segments = sum(r.segment_count for r in rejected_runs)
        actual_entities = metrics.polyline_runs_accepted + rejected_segments
        actual_reduction = metrics.line_segments_original - actual_entities
        metrics.actual_reduction_pct = (actual_reduction / metrics.line_segments_original) * 100

    logger.info(
        f"BODY_GEOMETRY_REPAIR | phase={phase} contours={metrics.contour_count} "
        f"polyline_runs={metrics.polyline_runs_detected} "
        f"accepted={metrics.polyline_runs_accepted} rejected={metrics.polyline_runs_rejected} "
        f"actual_reduction={metrics.actual_reduction_pct:.1f}%"
    )

    return BodyRepairResult(
        applied=True,
        phase=phase,
        layered=layered,
        primitives=primitives,
        accepted_primitives=accepted_primitives,
        metrics=metrics,
    )
