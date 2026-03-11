"""
DXF Geometry Correction Pipeline
=================================

Pipeline module for correcting DXF dimension mismatches and centerline offsets.

Resolves: SG-GAP-01, SG-GAP-02
- SG-GAP-01: DXF dimension mismatch vs spec (scale correction)
- SG-GAP-02: DXF centerline asymmetry (translation correction)

Usage:
    result = correct_dxf_geometry(
        dxf_bytes=bytes,
        spec_width_mm=368.3,
        spec_length_mm=444.5,
        center_on_x=True,
    )
"""

from __future__ import annotations

import io
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import ezdxf
from ezdxf.math import Vec2


@dataclass
class GeometryAnalysis:
    """Analysis of DXF geometry vs spec."""
    # Measured dimensions
    actual_width_mm: float = 0.0
    actual_length_mm: float = 0.0
    bounds_min: Tuple[float, float] = (0.0, 0.0)
    bounds_max: Tuple[float, float] = (0.0, 0.0)

    # Centerline analysis
    geometric_center_x: float = 0.0
    geometric_center_y: float = 0.0
    centerline_offset_mm: float = 0.0  # How far center is from X=0

    # Spec comparison
    spec_width_mm: float = 0.0
    spec_length_mm: float = 0.0
    width_deviation_pct: float = 0.0
    length_deviation_pct: float = 0.0

    # Point counts
    total_points: int = 0
    entity_count: int = 0


@dataclass
class CorrectionResult:
    """Result of geometry correction."""
    success: bool = False
    dxf_bytes: bytes = b""

    # Before correction
    original_analysis: Optional[GeometryAnalysis] = None

    # After correction
    corrected_analysis: Optional[GeometryAnalysis] = None

    # What was done
    scale_applied: Tuple[float, float] = (1.0, 1.0)  # (scale_x, scale_y)
    translation_applied: Tuple[float, float] = (0.0, 0.0)  # (dx, dy)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def analyze_dxf_geometry(dxf_bytes: bytes) -> GeometryAnalysis:
    """
    Analyze DXF geometry: bounds, dimensions, centerline.

    Returns GeometryAnalysis with measured values.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
    finally:
        import os
        os.unlink(tmp_path)

    msp = doc.modelspace()

    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")
    total_points = 0
    entity_count = 0

    for entity in msp:
        entity_count += 1
        points = _extract_entity_points(entity)
        total_points += len(points)

        for x, y in points:
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

    if min_x == float("inf"):
        return GeometryAnalysis()

    width = max_x - min_x
    length = max_y - min_y
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    return GeometryAnalysis(
        actual_width_mm=width,
        actual_length_mm=length,
        bounds_min=(min_x, min_y),
        bounds_max=(max_x, max_y),
        geometric_center_x=center_x,
        geometric_center_y=center_y,
        centerline_offset_mm=center_x,  # Offset from X=0
        total_points=total_points,
        entity_count=entity_count,
    )


def _extract_entity_points(entity) -> List[Tuple[float, float]]:
    """Extract XY points from a DXF entity."""
    points = []

    if entity.dxftype() == "LWPOLYLINE":
        for x, y, *_ in entity.get_points():
            points.append((x, y))
    elif entity.dxftype() == "POLYLINE":
        for vertex in entity.vertices:
            points.append((vertex.dxf.location.x, vertex.dxf.location.y))
    elif entity.dxftype() == "LINE":
        points.append((entity.dxf.start.x, entity.dxf.start.y))
        points.append((entity.dxf.end.x, entity.dxf.end.y))
    elif entity.dxftype() == "CIRCLE":
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        points.append((cx - r, cy))
        points.append((cx + r, cy))
        points.append((cx, cy - r))
        points.append((cx, cy + r))
    elif entity.dxftype() == "ARC":
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        import math
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        points.append((cx + r * math.cos(start_angle), cy + r * math.sin(start_angle)))
        points.append((cx + r * math.cos(end_angle), cy + r * math.sin(end_angle)))
    elif entity.dxftype() == "SPLINE":
        for pt in entity.control_points:
            points.append((pt.x, pt.y))

    return points


def correct_dxf_geometry(
    dxf_bytes: bytes,
    spec_width_mm: Optional[float] = None,
    spec_length_mm: Optional[float] = None,
    center_on_x: bool = True,
    center_on_y: bool = False,
    uniform_scale: bool = True,
    tolerance_pct: float = 2.0,
) -> CorrectionResult:
    """
    Correct DXF geometry to match spec dimensions and center alignment.

    Args:
        dxf_bytes: Input DXF file bytes
        spec_width_mm: Target width (X-axis extent)
        spec_length_mm: Target length (Y-axis extent)
        center_on_x: Translate so geometric center is at X=0
        center_on_y: Translate so geometric center is at Y=0
        uniform_scale: Use same scale factor for X and Y (preserves aspect ratio)
        tolerance_pct: Skip scaling if deviation is within this tolerance

    Returns:
        CorrectionResult with corrected DXF bytes and analysis
    """
    result = CorrectionResult()

    # Analyze original
    original = analyze_dxf_geometry(dxf_bytes)
    if original.actual_width_mm == 0 or original.actual_length_mm == 0:
        result.errors.append("Could not determine DXF bounds")
        return result

    original.spec_width_mm = spec_width_mm or 0
    original.spec_length_mm = spec_length_mm or 0

    if spec_width_mm:
        original.width_deviation_pct = (
            (original.actual_width_mm - spec_width_mm) / spec_width_mm * 100
        )
    if spec_length_mm:
        original.length_deviation_pct = (
            (original.actual_length_mm - spec_length_mm) / spec_length_mm * 100
        )

    result.original_analysis = original

    # Calculate scale factors
    scale_x, scale_y = 1.0, 1.0

    if spec_width_mm and abs(original.width_deviation_pct) > tolerance_pct:
        scale_x = spec_width_mm / original.actual_width_mm

    if spec_length_mm and abs(original.length_deviation_pct) > tolerance_pct:
        scale_y = spec_length_mm / original.actual_length_mm

    if uniform_scale and (scale_x != 1.0 or scale_y != 1.0):
        # Use average scale to preserve aspect ratio as much as possible
        avg_scale = (scale_x + scale_y) / 2
        scale_x = scale_y = avg_scale
        result.warnings.append(
            f"Using uniform scale {avg_scale:.4f} to preserve aspect ratio"
        )

    # Calculate translation
    translate_x, translate_y = 0.0, 0.0

    if center_on_x:
        # After scaling, center will be at: original_center * scale
        new_center_x = original.geometric_center_x * scale_x
        translate_x = -new_center_x

    if center_on_y:
        new_center_y = original.geometric_center_y * scale_y
        translate_y = -new_center_y

    result.scale_applied = (scale_x, scale_y)
    result.translation_applied = (translate_x, translate_y)

    # Apply transformations
    try:
        corrected_bytes = _apply_transformations(
            dxf_bytes, scale_x, scale_y, translate_x, translate_y
        )
    except Exception as e:
        result.errors.append(f"Transformation failed: {e}")
        return result

    # Analyze corrected
    corrected = analyze_dxf_geometry(corrected_bytes)
    corrected.spec_width_mm = spec_width_mm or 0
    corrected.spec_length_mm = spec_length_mm or 0

    if spec_width_mm:
        corrected.width_deviation_pct = (
            (corrected.actual_width_mm - spec_width_mm) / spec_width_mm * 100
        )
    if spec_length_mm:
        corrected.length_deviation_pct = (
            (corrected.actual_length_mm - spec_length_mm) / spec_length_mm * 100
        )

    result.corrected_analysis = corrected
    result.dxf_bytes = corrected_bytes
    result.success = True

    # Add summary warnings
    if abs(corrected.centerline_offset_mm) > 0.1:
        result.warnings.append(
            f"Centerline still offset by {corrected.centerline_offset_mm:.2f}mm"
        )

    return result


def _apply_transformations(
    dxf_bytes: bytes,
    scale_x: float,
    scale_y: float,
    translate_x: float,
    translate_y: float,
) -> bytes:
    """Apply scale and translation to all entities in DXF."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
    finally:
        import os
        os.unlink(tmp_path)

    msp = doc.modelspace()

    # Transform each entity
    for entity in list(msp):
        _transform_entity(entity, scale_x, scale_y, translate_x, translate_y)

    # Save to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        import os
        os.unlink(tmp_path)


def _transform_entity(
    entity,
    scale_x: float,
    scale_y: float,
    translate_x: float,
    translate_y: float,
):
    """Transform a single entity in place."""

    def transform_point(x: float, y: float) -> Tuple[float, float]:
        return (x * scale_x + translate_x, y * scale_y + translate_y)

    if entity.dxftype() == "LWPOLYLINE":
        new_points = []
        for x, y, start_width, end_width, bulge in entity.get_points(format="xyseb"):
            nx, ny = transform_point(x, y)
            new_points.append((nx, ny, start_width * scale_x, end_width * scale_x, bulge))
        entity.set_points(new_points, format="xyseb")

    elif entity.dxftype() == "POLYLINE":
        for vertex in entity.vertices:
            x, y = vertex.dxf.location.x, vertex.dxf.location.y
            nx, ny = transform_point(x, y)
            vertex.dxf.location = Vec2(nx, ny)

    elif entity.dxftype() == "LINE":
        sx, sy = entity.dxf.start.x, entity.dxf.start.y
        ex, ey = entity.dxf.end.x, entity.dxf.end.y
        entity.dxf.start = Vec2(*transform_point(sx, sy))
        entity.dxf.end = Vec2(*transform_point(ex, ey))

    elif entity.dxftype() == "CIRCLE":
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        entity.dxf.center = Vec2(*transform_point(cx, cy))
        # Scale radius (use average for non-uniform scale)
        entity.dxf.radius *= (scale_x + scale_y) / 2

    elif entity.dxftype() == "ARC":
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        entity.dxf.center = Vec2(*transform_point(cx, cy))
        entity.dxf.radius *= (scale_x + scale_y) / 2

    elif entity.dxftype() == "SPLINE":
        # Transform control points
        new_control_points = []
        for pt in entity.control_points:
            nx, ny = transform_point(pt.x, pt.y)
            new_control_points.append(Vec2(nx, ny))
        entity.control_points = new_control_points

        # Transform fit points if present
        if entity.fit_points:
            new_fit_points = []
            for pt in entity.fit_points:
                nx, ny = transform_point(pt.x, pt.y)
                new_fit_points.append(Vec2(nx, ny))
            entity.fit_points = new_fit_points


def validate_correction(
    corrected: CorrectionResult,
    max_deviation_pct: float = 1.0,
    max_centerline_offset_mm: float = 0.5,
) -> Tuple[bool, List[str]]:
    """
    Validate that correction meets tolerance requirements.

    Returns (passed, list of issues)
    """
    issues = []

    if not corrected.success:
        return False, corrected.errors

    analysis = corrected.corrected_analysis
    if not analysis:
        return False, ["No corrected analysis available"]

    if abs(analysis.width_deviation_pct) > max_deviation_pct:
        issues.append(
            f"Width deviation {analysis.width_deviation_pct:.1f}% exceeds {max_deviation_pct}%"
        )

    if abs(analysis.length_deviation_pct) > max_deviation_pct:
        issues.append(
            f"Length deviation {analysis.length_deviation_pct:.1f}% exceeds {max_deviation_pct}%"
        )

    if abs(analysis.centerline_offset_mm) > max_centerline_offset_mm:
        issues.append(
            f"Centerline offset {analysis.centerline_offset_mm:.2f}mm exceeds {max_centerline_offset_mm}mm"
        )

    return len(issues) == 0, issues
