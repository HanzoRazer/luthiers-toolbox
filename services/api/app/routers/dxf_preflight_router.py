"""DXF Preflight Validator Router - validates DXF files before CAM import."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Optional
import tempfile
from pathlib import Path
import base64
import binascii
import math
import re

try:
    import ezdxf
    from ezdxf.document import Drawing
    from app.util.dxf_compat import create_document
    from app.util.dxf_lifecycle_guard import (
        DxfLifecycleContext,
        assert_dxf_lifecycle_context,
    )
    from app.cam.r12_convert import (
        FidelityError,
        UnconvertibleEntity,
        convert_document,
        publish_converted_document,
    )
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from ..schemas.dxf_preflight_schemas import (
    ValidationIssue, GeometrySummary, LayerInfo, ValidationReport,
    ValidateBase64Request, AutoFixRequest, CurvePoint, CurveBiarcEntity,
    CurvePreflightRequest, PolylineMetrics, BiarcMetrics, CurvePreflightResponse,
)

router = APIRouter(prefix="/dxf/preflight", tags=["DXF Preflight", "Validation"])

from ..dxf.preflight_service import (
    validate_dxf_file, EZDXF_AVAILABLE,
    _distance, _bounding_box, _polyline_length, _duplicate_indices,
    _mm_diag, _validate_layer_name, _biarc_metrics,
)

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
    except (ValueError, binascii.Error) as e:  # WP-1: base64 decode
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
    except (ValueError, binascii.Error) as e:  # WP-1: base64 decode
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
        
        # convert_to_r12 appends its message AFTER the saved file has been verified
        # (below). It used to be announced here, before the conversion ran, so the
        # response said "Converted to R12 format" even when the output came back empty.
        conversion_report = None

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
            # R12 conversion is explicit, verified against the SAVED file, and fails
            # closed. The previous implementation copied entities with
            # add_foreign_entity, which accepts an LWPOLYLINE into an R12 document and
            # then loses it at write time: a consolidated body outline (R2000, one
            # LWPOLYLINE per contour) came back EMPTY while this endpoint reported
            # "Converted to R12 format". See app/cam/r12_convert.py.
            try:
                r12_doc, conversion = convert_document(doc, "R12")
            except UnconvertibleEntity as exc:
                raise HTTPException(status_code=422, detail=str(exc))

            assert_dxf_lifecycle_context(
                DxfLifecycleContext(
                    source_module=__name__,
                    export_type="dxf-create-save",
                    dxf_version="R12",
                    lifecycle_status="COMPAT_ONLY",
                    runtime_callable="router_endpoint",
                    authority_context="user_request",
                    provenance_status="NO",
                )
            )
            # Save, verify the SAVED bytes, then publish -- one shared implementation
            # with convert_file, so the two publish paths cannot drift apart. The
            # document in memory is not evidence: the loss happened at write time.
            # source_doc makes this source-vs-saved, not saved-vs-its-own-prediction.
            #
            # `doc` is passed, not tmp_in_path: the fixes above (close_open_polylines,
            # units) were applied to this document in memory. Re-reading the source
            # from disk would silently discard them.
            try:
                publish_converted_document(
                    r12_doc, conversion, tmp_out_path, doc, encoding='cp1252'
                )
            except FidelityError as exc:
                raise HTTPException(status_code=500, detail=str(exc))

            conversion_report = conversion
            verified = sum(conversion["verification"]["saved_entity_types"].values())
            fixes_applied.append(
                f"Converted to R12 format: {conversion['conversions'] or 'no entity conversions needed'}; "
                f"{verified} entities verified in the saved file "
                f"(note: R12 doesn't store units)"
            )
        else:
            doc.saveas(tmp_out_path)
        
        # Read back and encode
        with open(tmp_out_path, 'rb') as f:
            fixed_bytes = f.read()
        
        fixed_base64 = base64.b64encode(fixed_bytes).decode('utf-8')
        
        # Generate new validation report
        new_report = validate_dxf_file(tmp_out_path)
        
        response = {
            "fixed_dxf_base64": fixed_base64,
            "fixes_applied": fixes_applied,
            "validation_report": new_report
        }
        if conversion_report is not None:
            # What the conversion did and what it cost, so a caller can check rather
            # than trust a sentence: entity conversions, layer/style tables carried,
            # the saved-file verification, and losses R12's format forces.
            response["conversion_report"] = conversion_report
        return response
    
    finally:
        tmp_in_path.unlink()
        if tmp_out_path and tmp_out_path.exists():
            tmp_out_path.unlink()
