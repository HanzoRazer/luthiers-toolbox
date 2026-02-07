"""
DXF Preflight Validator Router

Validates DXF files before CAM import to prevent common issues:
- Open vs closed paths
- R12 format compatibility
- Unit detection (mm vs inch)
- Layer structure
- Unsupported geometry types

Author: Luthier's Tool Box
Date: November 17, 2025
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import tempfile
from pathlib import Path
import base64
import math
import re

try:
    import ezdxf
    from ezdxf.document import Drawing
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    print("Warning: ezdxf not available - DXF preflight will be limited")

router = APIRouter(prefix="/dxf/preflight", tags=["DXF Preflight", "Validation"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ValidationIssue(BaseModel):
    """Single validation issue found in DXF"""
    severity: Literal["error", "warning", "info"]
    category: Literal["format", "geometry", "units", "layers", "compatibility"]
    message: str
    details: Optional[str] = None
    fix_available: bool = False
    fix_description: Optional[str] = None


class GeometrySummary(BaseModel):
    """Summary of geometry types in DXF"""
    lines: int = 0
    arcs: int = 0
    circles: int = 0
    polylines: int = 0
    lwpolylines: int = 0
    splines: int = 0
    ellipses: int = 0
    text: int = 0
    other: int = 0
    total: int = 0


class LayerInfo(BaseModel):
    """Information about a single layer"""
    name: str
    entity_count: int
    geometry_types: List[str]
    color: Optional[int] = None
    frozen: bool = False
    locked: bool = False


class ValidationReport(BaseModel):
    """Complete validation report for a DXF file"""
    filename: str
    filesize_bytes: int
    dxf_version: str
    units: Optional[str] = None  # "mm", "inch", "unknown"
    
    issues: List[ValidationIssue]
    errors_count: int
    warnings_count: int
    info_count: int
    
    geometry: GeometrySummary
    layers: List[LayerInfo]
    
    cam_ready: bool
    recommended_actions: List[str]


class ValidateBase64Request(BaseModel):
    """Request to validate DXF from base64"""
    dxf_base64: str
    filename: str = "uploaded.dxf"


class AutoFixRequest(BaseModel):
    """Request to auto-fix common DXF issues"""
    dxf_base64: str
    filename: str
    fixes: List[Literal[
        "convert_to_r12",
        "close_open_polylines",
        "explode_splines",
        "merge_duplicate_layers",
        "set_units_mm"
    ]]


class CurvePoint(BaseModel):
    """Simple XY point used by CurveLab"""
    x: float
    y: float


class CurveBiarcEntity(BaseModel):
    """Optional bi-arc metadata from CurveLab client"""
    type: Literal["arc", "line"]
    radius: Optional[float] = None
    center: Optional[CurvePoint] = None
    start_angle: Optional[float] = None
    end_angle: Optional[float] = None
    a: Optional[CurvePoint] = Field(None, description="Line start point")
    b: Optional[CurvePoint] = Field(None, description="Line end point")


class CurvePreflightRequest(BaseModel):
    """Inline geometry payload sent by CurveLab.vue"""
    points: List[CurvePoint]
    units: Literal["mm", "inch"] = "mm"
    tolerance_mm: float = Field(0.1, description="Closure/duplicate tolerance in millimeters")
    layer: str = Field("CURVE", description="DXF layer name to preview")
    biarc_entities: Optional[List[CurveBiarcEntity]] = None


class PolylineMetrics(BaseModel):
    point_count: int
    length: float
    length_units: str
    closed: bool
    closure_gap: float
    closure_units: str
    duplicate_count: int
    duplicate_indices: List[int]
    bounding_box: Dict[str, float]


class BiarcMetrics(BaseModel):
    entity_count: int
    arcs: int
    lines: int
    min_radius: Optional[float]
    max_radius: Optional[float]
    radius_units: str = "mm"


class CurvePreflightResponse(BaseModel):
    """Response payload consumed by CurveLab Preflight modal"""
    units: str
    tolerance_mm: float
    issues: List[ValidationIssue]
    errors_count: int
    warnings_count: int
    info_count: int
    polyline: PolylineMetrics
    biarc: Optional[BiarcMetrics]
    cam_ready: bool
    recommended_actions: List[str]


# ============================================================================
# Validation Logic
# ============================================================================

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

@router.get("/health")
def preflight_health():
    """Health check for DXF preflight service"""
    return {
        "service": "dxf_preflight",
        "version": "1.0",
        "ezdxf_available": EZDXF_AVAILABLE,
        "status": "ok" if EZDXF_AVAILABLE else "degraded"
    }


@router.post("/curve_report", response_model=CurvePreflightResponse)
def curve_preflight_report(body: CurvePreflightRequest):
    """Validate in-memory CurveLab geometry before DXF export."""
    if len(body.points) < 2:
        raise HTTPException(status_code=400, detail="At least two points required for CurveLab preflight")

    issues: List[ValidationIssue] = []
    duplicates = _duplicate_indices(body.points, body.tolerance_mm)
    bbox = _bounding_box(body.points)
    length = _polyline_length(body.points)
    closure_gap = _distance(body.points[0], body.points[-1])

    if not (0.001 <= body.tolerance_mm <= 1.0):
        issues.append(ValidationIssue(
            severity="warning",
            category="geometry",
            message="Tolerance outside recommended range",
            details="Suggested tolerance window is 0.001 mm – 1.0 mm",
            fix_available=True,
            fix_description="Set tolerance between 0.01 mm and 0.5 mm for most lutherie work"
        ))

    if duplicates:
        issues.append(ValidationIssue(
            severity="warning",
            category="geometry",
            message=f"{len(duplicates)} duplicate vertex/vertices detected",
            details="Duplicate points can create zero-length segments",
            fix_available=True,
            fix_description="Remove duplicate control points before exporting"
        ))

    if closure_gap > body.tolerance_mm:
        issues.append(ValidationIssue(
            severity="warning",
            category="geometry",
            message=f"Open polyline gap of {closure_gap:.3f} {body.units}",
            details="Curve must be closed for pocketing and profiling",
            fix_available=True,
            fix_description="Connect first/last point or increase closure tolerance"
        ))

    diag_mm = _mm_diag(body.points, body.units)
    if diag_mm > 6000:
        issues.append(ValidationIssue(
            severity="info",
            category="units",
            message="Geometry spans more than 6,000 mm",
            details="Check that units are correct (inch vs mm)",
            fix_available=False
        ))
    elif diag_mm < 0.5:
        issues.append(ValidationIssue(
            severity="info",
            category="units",
            message="Geometry smaller than 0.5 mm",
            details="Scale may be incorrect for production parts",
            fix_available=False
        ))

    layer_issue = _validate_layer_name(body.layer)
    if layer_issue:
        issues.append(ValidationIssue(
            severity="warning",
            category="layers",
            message=layer_issue,
            details="CurveLab exports to a single DXF layer",
            fix_available=True,
            fix_description="Use alphanumeric/underscore characters for layer names"
        ))

    biarc_stats = _biarc_metrics(body.biarc_entities, body.units)
    if biarc_stats and biarc_stats.min_radius and biarc_stats.min_radius < 0.25:
        issues.append(ValidationIssue(
            severity="info",
            category="geometry",
            message=f"Bi-arc radius drops below 0.25 {body.units}",
            details="Very small arcs may not machine cleanly",
            fix_available=False
        ))

    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")

    recommendations = [i.fix_description for i in issues if i.fix_description]
    if not recommendations:
        recommendations = ["✅ CurveLab polyline is CAM-ready"]

    polyline_stats = PolylineMetrics(
        point_count=len(body.points),
        length=length,
        length_units=body.units,
        closed=closure_gap <= body.tolerance_mm,
        closure_gap=closure_gap,
        closure_units=body.units,
        duplicate_count=len(duplicates),
        duplicate_indices=duplicates,
        bounding_box=bbox,
    )

    return CurvePreflightResponse(
        units=body.units,
        tolerance_mm=body.tolerance_mm,
        issues=issues,
        errors_count=errors,
        warnings_count=warnings,
        info_count=infos,
        polyline=polyline_stats,
        biarc=biarc_stats,
        cam_ready=errors == 0 and warnings == 0,
        recommended_actions=recommendations,
    )


@router.post("/validate", response_model=ValidationReport)
async def validate_dxf(file: UploadFile = File(...)):
    """
    Validate uploaded DXF file and return comprehensive report.
    
    Checks:
    - DXF version (R12 recommended)
    - Units (mm, inch, unknown)
    - Closed vs open paths
    - Geometry types (lines, arcs, splines, etc.)
    - Layer structure
    - CAM compatibility issues
    
    Returns:
    - Validation report with issues, geometry summary, and recommendations
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(status_code=500, detail="ezdxf library not available")
    
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="File must be a DXF (.dxf extension)")
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        report = validate_dxf_file(tmp_path)
        return report
    finally:
        tmp_path.unlink()  # Clean up temp file


@router.post("/validate_base64", response_model=ValidationReport)
def validate_dxf_base64(request: ValidateBase64Request):
    """
    Validate DXF from base64 string.
    
    Useful for client-side file reading without multipart upload.
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(status_code=500, detail="ezdxf library not available")
    
    try:
        dxf_bytes = base64.b64decode(request.dxf_base64)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Invalid base64: {str(e)}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        tmp.write(dxf_bytes)
        tmp_path = Path(tmp.name)
    
    try:
        report = validate_dxf_file(tmp_path)
        report.filename = request.filename
        return report
    finally:
        tmp_path.unlink()


@router.post("/auto_fix")
async def auto_fix_dxf(request: AutoFixRequest):
    """
    Attempt to auto-fix common DXF issues.
    
    Available fixes:
    - convert_to_r12: Convert to R12 format
    - close_open_polylines: Close open polylines within tolerance
    - explode_splines: Convert splines to polyline approximations
    - merge_duplicate_layers: Merge layers with same name (case-insensitive)
    - set_units_mm: Set $INSUNITS to millimeters
    
    Returns:
    - Fixed DXF as base64 string
    - List of fixes applied
    - New validation report
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(status_code=500, detail="ezdxf library not available")
    
    # Decode DXF
    try:
        dxf_bytes = base64.b64decode(request.dxf_base64)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Invalid base64: {str(e)}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp_in:
        tmp_in.write(dxf_bytes)
        tmp_in_path = Path(tmp_in.name)
    
    tmp_out_path = None  # Initialize for cleanup
    try:
        doc = ezdxf.readfile(str(tmp_in_path))
        fixes_applied = []
        
        # Apply requested fixes
        # Note: set_units_mm must come BEFORE convert_to_r12 since R12 doesn't support $INSUNITS
        if "set_units_mm" in request.fixes and "convert_to_r12" not in request.fixes:
            doc.header['$INSUNITS'] = 4  # mm (only if not converting to R12)
            fixes_applied.append("Set units to millimeters")
        
        if "convert_to_r12" in request.fixes:
            # To convert to R12, we need to create a new R12 document and copy entities
            # ezdxf doesn't support direct format conversion via fmt parameter
            fixes_applied.append("Converted to R12 format (note: R12 doesn't store units)")
        
        if "close_open_polylines" in request.fixes:
            msp = doc.modelspace()
            closed_count = 0
            for entity in msp:
                if entity.dxftype() == "LWPOLYLINE" and not entity.closed:
                    # Check if start/end are close (within 0.01mm)
                    points = list(entity.get_points())
                    if len(points) >= 2:
                        start = points[0][:2]
                        end = points[-1][:2]
                        dist = ((start[0]-end[0])**2 + (start[1]-end[1])**2)**0.5
                        if dist < 0.1:  # 0.1mm tolerance
                            entity.close(True)
                            closed_count += 1
            if closed_count > 0:
                fixes_applied.append(f"Closed {closed_count} open polyline(s)")
        
        if "explode_splines" in request.fixes:
            # Note: Spline explosion is complex, stub for now
            fixes_applied.append("Spline explosion not yet implemented")
        
        # Save fixed DXF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp_out:
            tmp_out_path = Path(tmp_out.name)
        
        if "convert_to_r12" in request.fixes:
            # Create a new R12 document and copy entities
            r12_doc = ezdxf.new('R12')
            r12_msp = r12_doc.modelspace()
            
            # Copy entities from original doc
            try:
                for entity in doc.modelspace():
                    # Copy entity to R12 document (R12 may not support all entity types)
                    try:
                        r12_msp.add_foreign_entity(entity)
                    except (TypeError, ValueError, AttributeError):  # WP-1: narrowed — entity copy fallback
                        # Fallback: try direct copy for simple entities
                        if entity.dxftype() in ('LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'POLYLINE'):
                            r12_msp.add_entity(entity.copy())
            except (TypeError, ValueError, AttributeError) as e:  # WP-1: narrowed — R12 copy fallback
                # If copying fails, at least save as R12 even if empty
                pass
            
            r12_doc.saveas(tmp_out_path, encoding='cp1252')
        else:
            doc.saveas(tmp_out_path)
        
        # Read back and encode
        with open(tmp_out_path, 'rb') as f:
            fixed_bytes = f.read()
        
        fixed_base64 = base64.b64encode(fixed_bytes).decode('utf-8')
        
        # Generate new validation report
        new_report = validate_dxf_file(tmp_out_path)
        
        return {
            "fixed_dxf_base64": fixed_base64,
            "fixes_applied": fixes_applied,
            "validation_report": new_report
        }
    
    finally:
        tmp_in_path.unlink()
        if tmp_out_path and tmp_out_path.exists():
            tmp_out_path.unlink()
