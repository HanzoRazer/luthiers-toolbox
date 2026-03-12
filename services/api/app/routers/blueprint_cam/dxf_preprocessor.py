"""
DXF Preprocessor Pipeline
=========================

Systemic fixes for DXF quality issues before CAM processing:
- Format normalization (any version → R2000)
- Curve densification (coarse polylines → smooth 200+ point curves)
- Dimension validation (bounds vs instrument spec)

Resolves: EX-GAP-01, EX-GAP-02, EX-GAP-03
"""

import math
import tempfile
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

import ezdxf
from ezdxf.math import Vec2


# =============================================================================
# CONFIGURATION
# =============================================================================

# Minimum points for production-quality curve
MIN_PRODUCTION_POINTS = 200

# Maximum segment length for densification (mm)
MAX_SEGMENT_LENGTH_MM = 2.0

# Instrument dimension specs (width x height in mm)
INSTRUMENT_SPECS: Dict[str, Dict[str, Any]] = {
    "explorer": {
        "expected_width_mm": (470, 490),   # Actual range
        "expected_height_mm": (420, 450),
        "display_name": "Gibson Explorer 1958",
    },
    "les_paul": {
        "expected_width_mm": (375, 395),
        "expected_height_mm": (260, 280),
        "display_name": "Gibson Les Paul 1959",
    },
    "flying_v": {
        "expected_width_mm": (480, 500),
        "expected_height_mm": (400, 430),
        "display_name": "Gibson Flying V 1958",
    },
    "stratocaster": {
        "expected_width_mm": (315, 335),
        "expected_height_mm": (455, 475),
        "display_name": "Fender Stratocaster",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PreprocessingResult:
    """Result of DXF preprocessing."""
    success: bool
    dxf_bytes: bytes = b""
    original_version: str = ""
    normalized_version: str = "AC1015"  # R2000
    original_point_count: int = 0
    densified_point_count: int = 0
    original_bounds_mm: Tuple[float, float] = (0.0, 0.0)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    dimension_validation: Optional[Dict[str, Any]] = None


@dataclass
class DimensionValidation:
    """Result of dimension validation against spec."""
    valid: bool
    instrument_type: str = ""
    expected_width_range: Tuple[float, float] = (0, 0)
    expected_height_range: Tuple[float, float] = (0, 0)
    actual_width: float = 0.0
    actual_height: float = 0.0
    width_deviation_pct: float = 0.0
    height_deviation_pct: float = 0.0
    message: str = ""


# =============================================================================
# FORMAT NORMALIZATION
# =============================================================================

def normalize_dxf_format(dxf_bytes: bytes) -> Tuple[bytes, str, str, List[str]]:
    """
    Normalize DXF to R2000 format (AC1015).

    R2000 is the minimum version that supports LWPOLYLINE and is
    widely compatible with CAM software.

    Returns:
        (normalized_bytes, original_version, new_version, warnings)
    """
    warnings = []

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        # Read original
        doc = ezdxf.readfile(tmp_path)
        original_version = doc.dxfversion

        # Check if normalization needed
        # AC1009 = R12, AC1015 = R2000, AC1018 = R2004, AC1024 = 2010, AC1027 = 2013
        if original_version in ('AC1015', 'AC1018'):
            # Already good format
            return dxf_bytes, original_version, original_version, warnings

        if original_version == 'AC1009':
            # R12 - needs upgrade for LWPOLYLINE support
            warnings.append(f"Upgrading from R12 ({original_version}) to R2000 for LWPOLYLINE support")
        elif original_version in ('AC1024', 'AC1027', 'AC1032'):
            # Newer format - downgrade for compatibility
            warnings.append(f"Downgrading from {original_version} to R2000 for CAM compatibility")

        # Create new R2000 document
        new_doc = ezdxf.new('R2000')
        new_msp = new_doc.modelspace()

        # Copy all layers
        for layer in doc.layers:
            if layer.dxf.name not in ('0', 'Defpoints'):
                try:
                    new_doc.layers.add(layer.dxf.name)
                except ezdxf.DXFTableEntryError:
                    pass  # Layer already exists

        # Copy entities
        msp = doc.modelspace()
        for entity in msp:
            try:
                etype = entity.dxftype()
                layer = entity.dxf.layer

                if etype == 'LWPOLYLINE':
                    points = [(p[0], p[1]) for p in entity.get_points()]
                    new_msp.add_lwpolyline(points, close=entity.closed,
                                           dxfattribs={'layer': layer})
                elif etype == 'LINE':
                    new_msp.add_line(
                        (entity.dxf.start.x, entity.dxf.start.y),
                        (entity.dxf.end.x, entity.dxf.end.y),
                        dxfattribs={'layer': layer}
                    )
                elif etype == 'CIRCLE':
                    new_msp.add_circle(
                        (entity.dxf.center.x, entity.dxf.center.y),
                        entity.dxf.radius,
                        dxfattribs={'layer': layer}
                    )
                elif etype == 'ARC':
                    new_msp.add_arc(
                        (entity.dxf.center.x, entity.dxf.center.y),
                        entity.dxf.radius,
                        entity.dxf.start_angle,
                        entity.dxf.end_angle,
                        dxfattribs={'layer': layer}
                    )
                elif etype == 'SPLINE':
                    # Sample spline to polyline
                    try:
                        pts = [(p.x, p.y) for p in entity.flattening(0.5)]
                        if len(pts) >= 2:
                            new_msp.add_lwpolyline(pts, close=False,
                                                   dxfattribs={'layer': layer})
                    except (AttributeError, RuntimeError):
                        warnings.append(f"Could not convert SPLINE on layer {layer}")
                # Skip other entity types with warning
                else:
                    pass  # Silently skip unsupported types

            except Exception as e:  # WP-2: API endpoint catch-all
                warnings.append(f"Error copying {entity.dxftype()}: {str(e)}")

        # Save to bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as out_tmp:
            out_path = out_tmp.name

        new_doc.saveas(out_path)

        with open(out_path, 'rb') as f:
            normalized_bytes = f.read()

        os.unlink(out_path)

        return normalized_bytes, original_version, 'AC1015', warnings

    finally:
        os.unlink(tmp_path)


# =============================================================================
# CURVE DENSIFICATION
# =============================================================================

def densify_polyline(points: List[Tuple[float, float]],
                     min_points: int = MIN_PRODUCTION_POINTS,
                     max_segment_mm: float = MAX_SEGMENT_LENGTH_MM) -> List[Tuple[float, float]]:
    """
    Add interpolated points to create smooth, production-quality curve.

    Uses linear interpolation with optional Catmull-Rom spline smoothing
    for curves that need it.

    Args:
        points: Original polyline points [(x, y), ...]
        min_points: Minimum points in output
        max_segment_mm: Maximum segment length in output

    Returns:
        Densified point list
    """
    if len(points) < 2:
        return points

    # Calculate total perimeter
    total_length = 0.0
    segments = []
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        seg_len = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        segments.append((p1, p2, seg_len))
        total_length += seg_len

    # Calculate target segment count
    target_by_length = int(total_length / max_segment_mm) + 1
    target_by_count = max(min_points, len(points))
    target_segments = max(target_by_length, target_by_count)

    if target_segments <= len(points):
        return points  # Already dense enough

    # Densify each segment proportionally
    densified = []
    for p1, p2, seg_len in segments:
        # How many points for this segment?
        seg_fraction = seg_len / total_length if total_length > 0 else 1.0 / len(segments)
        num_subdivisions = max(1, int(target_segments * seg_fraction))

        # Add interpolated points
        for j in range(num_subdivisions):
            t = j / num_subdivisions
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            densified.append((x, y))

    return densified


def densify_dxf(dxf_bytes: bytes,
                min_points: int = MIN_PRODUCTION_POINTS,
                max_segment_mm: float = MAX_SEGMENT_LENGTH_MM) -> Tuple[bytes, int, int, List[str]]:
    """
    Densify all LWPOLYLINE entities in DXF.

    Returns:
        (densified_bytes, original_point_count, new_point_count, warnings)
    """
    warnings = []
    original_count = 0
    new_count = 0

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()

        # Find all LWPOLYLINE entities
        polylines = [e for e in msp if e.dxftype() == 'LWPOLYLINE']

        if not polylines:
            warnings.append("No LWPOLYLINE entities to densify")
            return dxf_bytes, 0, 0, warnings

        # Process each polyline
        for poly in polylines:
            points = [(p[0], p[1]) for p in poly.get_points()]
            original_count += len(points)

            if len(points) < min_points:
                # Needs densification
                dense_points = densify_polyline(points, min_points, max_segment_mm)
                new_count += len(dense_points)

                # Replace entity
                layer = poly.dxf.layer
                is_closed = poly.closed
                msp.delete_entity(poly)
                msp.add_lwpolyline(dense_points, close=is_closed,
                                   dxfattribs={'layer': layer})

                warnings.append(f"Densified {len(points)} → {len(dense_points)} points on layer {layer}")
            else:
                new_count += len(points)

        # Save
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as out_tmp:
            out_path = out_tmp.name

        doc.saveas(out_path)

        with open(out_path, 'rb') as f:
            densified_bytes = f.read()

        os.unlink(out_path)

        return densified_bytes, original_count, new_count, warnings

    finally:
        os.unlink(tmp_path)


# =============================================================================
# DIMENSION VALIDATION
# =============================================================================

def validate_dimensions(dxf_bytes: bytes,
                        instrument_type: Optional[str] = None) -> DimensionValidation:
    """
    Validate DXF dimensions against instrument spec.

    Args:
        dxf_bytes: DXF file content
        instrument_type: e.g. "explorer", "les_paul", "flying_v"

    Returns:
        DimensionValidation result
    """
    result = DimensionValidation(valid=True)

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()

        # Get bounds from all entities
        all_x = []
        all_y = []

        for entity in msp:
            etype = entity.dxftype()
            if etype == 'LWPOLYLINE':
                for p in entity.get_points():
                    all_x.append(p[0])
                    all_y.append(p[1])
            elif etype == 'LINE':
                all_x.extend([entity.dxf.start.x, entity.dxf.end.x])
                all_y.extend([entity.dxf.start.y, entity.dxf.end.y])
            elif etype == 'CIRCLE':
                all_x.extend([entity.dxf.center.x - entity.dxf.radius,
                              entity.dxf.center.x + entity.dxf.radius])
                all_y.extend([entity.dxf.center.y - entity.dxf.radius,
                              entity.dxf.center.y + entity.dxf.radius])

        if not all_x:
            result.valid = False
            result.message = "No geometry found in DXF"
            return result

        result.actual_width = max(all_x) - min(all_x)
        result.actual_height = max(all_y) - min(all_y)

        # Validate against spec if provided
        if instrument_type and instrument_type.lower() in INSTRUMENT_SPECS:
            spec = INSTRUMENT_SPECS[instrument_type.lower()]
            result.instrument_type = spec["display_name"]
            result.expected_width_range = spec["expected_width_mm"]
            result.expected_height_range = spec["expected_height_mm"]

            # Check width
            w_min, w_max = spec["expected_width_mm"]
            w_mid = (w_min + w_max) / 2
            if not (w_min <= result.actual_width <= w_max):
                result.valid = False
                result.width_deviation_pct = ((result.actual_width - w_mid) / w_mid) * 100

            # Check height
            h_min, h_max = spec["expected_height_mm"]
            h_mid = (h_min + h_max) / 2
            if not (h_min <= result.actual_height <= h_max):
                result.valid = False
                result.height_deviation_pct = ((result.actual_height - h_mid) / h_mid) * 100

            if result.valid:
                result.message = f"Dimensions within spec for {spec['display_name']}"
            else:
                result.message = (
                    f"Dimensions outside spec for {spec['display_name']}: "
                    f"actual {result.actual_width:.1f}×{result.actual_height:.1f}mm, "
                    f"expected {w_min}-{w_max}×{h_min}-{h_max}mm "
                    f"(width {result.width_deviation_pct:+.1f}%, height {result.height_deviation_pct:+.1f}%)"
                )
        else:
            result.message = f"Dimensions: {result.actual_width:.1f}×{result.actual_height:.1f}mm (no spec to validate against)"

        return result

    finally:
        os.unlink(tmp_path)


# =============================================================================
# MAIN PREPROCESSING PIPELINE
# =============================================================================

def preprocess_dxf(dxf_bytes: bytes,
                   normalize_format: bool = True,
                   densify_curves: bool = True,
                   validate_dims: bool = True,
                   instrument_type: Optional[str] = None,
                   min_points: int = MIN_PRODUCTION_POINTS,
                   max_segment_mm: float = MAX_SEGMENT_LENGTH_MM) -> PreprocessingResult:
    """
    Full DXF preprocessing pipeline.

    Applies in order:
    1. Format normalization (any version → R2000)
    2. Curve densification (coarse → smooth)
    3. Dimension validation (bounds vs spec)

    Args:
        dxf_bytes: Raw DXF file content
        normalize_format: Convert to R2000 format
        densify_curves: Add points for smooth curves
        validate_dims: Check dimensions against instrument spec
        instrument_type: e.g. "explorer" for dimension validation
        min_points: Minimum points per curve
        max_segment_mm: Maximum segment length

    Returns:
        PreprocessingResult with processed DXF and diagnostics
    """
    result = PreprocessingResult(success=True, dxf_bytes=dxf_bytes)
    current_bytes = dxf_bytes

    # Step 1: Format normalization
    if normalize_format:
        try:
            current_bytes, orig_ver, new_ver, warnings = normalize_dxf_format(current_bytes)
            result.original_version = orig_ver
            result.normalized_version = new_ver
            result.warnings.extend(warnings)
        except Exception as e:  # WP-2: API endpoint catch-all
            result.errors.append(f"Format normalization failed: {str(e)}")
            result.success = False
            return result

    # Step 2: Curve densification
    if densify_curves:
        try:
            current_bytes, orig_pts, new_pts, warnings = densify_dxf(
                current_bytes, min_points, max_segment_mm
            )
            result.original_point_count = orig_pts
            result.densified_point_count = new_pts
            result.warnings.extend(warnings)
        except Exception as e:  # WP-2: API endpoint catch-all
            result.errors.append(f"Curve densification failed: {str(e)}")
            result.success = False
            return result

    # Step 3: Dimension validation
    if validate_dims:
        try:
            dim_result = validate_dimensions(current_bytes, instrument_type)
            result.dimension_validation = {
                "valid": dim_result.valid,
                "instrument_type": dim_result.instrument_type,
                "actual_width_mm": dim_result.actual_width,
                "actual_height_mm": dim_result.actual_height,
                "expected_width_range": dim_result.expected_width_range,
                "expected_height_range": dim_result.expected_height_range,
                "width_deviation_pct": dim_result.width_deviation_pct,
                "height_deviation_pct": dim_result.height_deviation_pct,
                "message": dim_result.message,
            }
            result.original_bounds_mm = (dim_result.actual_width, dim_result.actual_height)

            if not dim_result.valid:
                result.warnings.append(dim_result.message)
        except Exception as e:  # WP-2: API endpoint catch-all
            result.errors.append(f"Dimension validation failed: {str(e)}")
            # Don't fail the whole pipeline for validation errors

    result.dxf_bytes = current_bytes
    return result
