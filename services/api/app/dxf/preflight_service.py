"""DXF Preflight validation service - extracted from dxf_preflight_router.py."""
from pathlib import Path
from typing import List, Dict, Optional
import math

from fastapi import HTTPException

try:
    import ezdxf
    from ezdxf.document import Drawing
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from ..schemas.dxf_preflight_schemas import (
    ValidationIssue, GeometrySummary, LayerInfo, ValidationReport,
    CurvePoint, CurveBiarcEntity, PolylineMetrics, BiarcMetrics,
)

def validate_dxf_file(dxf_path: Path) -> ValidationReport:
    """
    Validate a DXF file and return comprehensive report.
    
    Args:
        dxf_path: Path to DXF file
        
    Returns:
        ValidationReport with issues, geometry summary, and recommendations
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(status_code=500, detail="ezdxf library not available")
    
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Failed to read DXF: {str(e)}")
    
    issues: List[ValidationIssue] = []
    geometry = GeometrySummary()
    layers_info: List[LayerInfo] = []
    
    # Get file stats
    filename = dxf_path.name
    filesize = dxf_path.stat().st_size
    dxf_version = doc.dxfversion
    
    # Check 1: DXF Version (R12 recommended for CAM)
    if dxf_version != "AC1009":  # R12
        issues.append(ValidationIssue(
            severity="warning",
            category="format",
            message=f"DXF version is {dxf_version}, not R12 (AC1009)",
            details="Many CAM software prefer R12 format for maximum compatibility",
            fix_available=True,
            fix_description="Convert to R12 format (may lose some features)"
        ))
    
    # Check 2: Units detection
    try:
        units_code = doc.header.get('$INSUNITS', 0)
        units_map = {0: "unknown", 1: "inch", 4: "mm", 5: "cm"}
        units = units_map.get(units_code, "unknown")
        
        if units == "unknown":
            issues.append(ValidationIssue(
                severity="warning",
                category="units",
                message="Units not specified in DXF header ($INSUNITS)",
                details="CAM software may interpret dimensions incorrectly",
                fix_available=True,
                fix_description="Set units to mm (most common for lutherie)"
            ))
    except (KeyError, AttributeError):  # WP-1: narrowed — header access fallback
        units = "unknown"
    
    # Check 3: Analyze geometry and layers
    msp = doc.modelspace()
    layer_entities: Dict[str, List[str]] = {}
    
    for entity in msp:
        entity_type = entity.dxftype()
        layer_name = entity.dxf.layer
        
        # Count by type
        if entity_type == "LINE":
            geometry.lines += 1
        elif entity_type == "ARC":
            geometry.arcs += 1
        elif entity_type == "CIRCLE":
            geometry.circles += 1
        elif entity_type == "POLYLINE":
            geometry.polylines += 1
            # Check if closed
            if hasattr(entity.dxf, 'flags') and not (entity.dxf.flags & 1):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="geometry",
                    message=f"Open POLYLINE found on layer {layer_name}",
                    details="CNC toolpaths require closed paths for pocketing/profiling",
                    fix_available=True,
                    fix_description="Close polyline by connecting start/end points"
                ))
        elif entity_type == "LWPOLYLINE":
            geometry.lwpolylines += 1
            if not entity.closed:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="geometry",
                    message=f"Open LWPOLYLINE found on layer {layer_name}",
                    details="CNC toolpaths require closed paths for pocketing/profiling",
                    fix_available=True,
                    fix_description="Close lwpolyline by setting closed flag"
                ))
        elif entity_type == "SPLINE":
            geometry.splines += 1
            issues.append(ValidationIssue(
                severity="info",
                category="geometry",
                message=f"SPLINE found on layer {layer_name}",
                details="Some CAM software require splines to be exploded to line/arc segments",
                fix_available=True,
                fix_description="Explode spline to polyline approximation"
            ))
        elif entity_type == "ELLIPSE":
            geometry.ellipses += 1
            issues.append(ValidationIssue(
                severity="warning",
                category="geometry",
                message=f"ELLIPSE found on layer {layer_name}",
                details="Not all CAM software support ellipses directly",
                fix_available=True,
                fix_description="Convert ellipse to polyline approximation"
            ))
        elif entity_type == "TEXT" or entity_type == "MTEXT":
            geometry.text += 1
        else:
            geometry.other += 1
        
        # Track layer entities
        if layer_name not in layer_entities:
            layer_entities[layer_name] = []
        if entity_type not in layer_entities[layer_name]:
            layer_entities[layer_name].append(entity_type)
    
    geometry.total = (geometry.lines + geometry.arcs + geometry.circles + 
                      geometry.polylines + geometry.lwpolylines + geometry.splines +
                      geometry.ellipses + geometry.text + geometry.other)
    
    # Check 4: Layer analysis
    for layer in doc.layers:
        layer_name = layer.dxf.name
        entity_count = sum(1 for e in msp if e.dxf.layer == layer_name)
        
        layers_info.append(LayerInfo(
            name=layer_name,
            entity_count=entity_count,
            geometry_types=layer_entities.get(layer_name, []),
            color=layer.dxf.color if hasattr(layer.dxf, 'color') else None,
            frozen=layer.is_frozen(),
            locked=layer.is_locked()
        ))
    
    # Check 5: Empty layers
    empty_layers = [l for l in layers_info if l.entity_count == 0]
    if empty_layers:
        issues.append(ValidationIssue(
            severity="info",
            category="layers",
            message=f"{len(empty_layers)} empty layer(s) found",
            details=f"Layers: {', '.join([l.name for l in empty_layers[:5]])}",
            fix_available=True,
            fix_description="Remove empty layers to clean up file"
        ))
    
    # Check 6: Frozen/locked layers with geometry
    frozen_with_geom = [l for l in layers_info if l.frozen and l.entity_count > 0]
    if frozen_with_geom:
        issues.append(ValidationIssue(
            severity="warning",
            category="layers",
            message=f"{len(frozen_with_geom)} frozen layer(s) contain geometry",
            details="Frozen layers may not be visible or selectable in CAM software",
            fix_available=False
        ))
    
    # Check 7: No geometry at all
    if geometry.total == 0:
        issues.append(ValidationIssue(
            severity="error",
            category="geometry",
            message="No geometry found in DXF file",
            details="File may be empty or geometry is on frozen/off layers",
            fix_available=False
        ))
    
    # Generate recommendations
    recommendations = []
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    
    cam_ready = errors == 0 and warnings <= 2
    
    if not cam_ready:
        if errors > 0:
            recommendations.append(f"Fix {errors} critical error(s) before importing to CAM")
        if warnings > 5:
            recommendations.append(f"Consider addressing {warnings} warning(s) for best results")
    
    if dxf_version != "AC1009":
        recommendations.append("Convert to R12 format for maximum CAM compatibility")
    
    if units == "unknown":
        recommendations.append("Set units to mm or inch to avoid scale mismatches")
    
    open_path_count = sum(1 for i in issues if "Open" in i.message)
    if open_path_count > 0:
        recommendations.append(f"Close {open_path_count} open path(s) for CNC operations")
    
    if geometry.splines > 0 or geometry.ellipses > 0:
        recommendations.append("Explode splines/ellipses to line/arc segments if CAM import fails")
    
    if not recommendations:
        recommendations.append("✅ DXF is CAM-ready! No major issues found.")
    
    return ValidationReport(
        filename=filename,
        filesize_bytes=filesize,
        dxf_version=dxf_version,
        units=units,
        issues=issues,
        errors_count=errors,
        warnings_count=warnings,
        info_count=sum(1 for i in issues if i.severity == "info"),
        geometry=geometry,
        layers=layers_info,
        cam_ready=cam_ready,
        recommended_actions=recommendations
    )


# ============================================================================
# Inline CurveLab Geometry Validation
# ============================================================================

def _distance(a: CurvePoint, b: CurvePoint) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _bounding_box(points: List[CurvePoint]) -> Dict[str, float]:
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x,
        "height": max_y - min_y,
    }


def _polyline_length(points: List[CurvePoint]) -> float:
    return sum(_distance(points[i], points[i + 1]) for i in range(len(points) - 1))


def _duplicate_indices(points: List[CurvePoint], tolerance: float) -> List[int]:
    """Return indices of duplicate vertices, ignoring explicit closing vertex."""
    precision = 4 if tolerance <= 0.01 else 3
    seen: Dict[str, int] = {}
    duplicates: List[int] = []
    closure_idx: Optional[int] = None

    if len(points) > 2 and _distance(points[0], points[-1]) <= tolerance:
        closure_idx = len(points) - 1

    for idx, p in enumerate(points):
        if idx == closure_idx:
            continue  # allow explicit closure without duplication warning

        key = f"{round(p.x, precision)}_{round(p.y, precision)}"
        if key in seen:
            duplicates.append(idx)
        else:
            seen[key] = idx
    return duplicates


def _mm_diag(points: List[CurvePoint], units: str) -> float:
    bbox = _bounding_box(points)
    diag = math.hypot(bbox["width"], bbox["height"])
    if units == "inch":
        return diag * 25.4
    return diag


def _validate_layer_name(layer: str) -> Optional[str]:
    if not layer:
        return "Layer name is empty"
    if not re.match(r"^[A-Za-z0-9_\-]+$", layer):
        return "Layer name must be alphanumeric/underscore"
    if len(layer) > 31:
        return "Layer name exceeds 31 characters"
    return None


def _biarc_metrics(entities: Optional[List[CurveBiarcEntity]], units: str) -> Optional[BiarcMetrics]:
    if not entities:
        return None
    arcs = [e for e in entities if e.type == "arc"]
    lines = [e for e in entities if e.type == "line"]
    radii = [e.radius for e in arcs if e.radius is not None]
    return BiarcMetrics(
        entity_count=len(entities),
        arcs=len(arcs),
        lines=len(lines),
        min_radius=min(radii) if radii else None,
        max_radius=max(radii) if radii else None,
        radius_units=units,
    )


# ============================================================================
# API Endpoints
# ============================================================================
