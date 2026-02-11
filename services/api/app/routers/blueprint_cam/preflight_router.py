"""
Blueprint CAM Preflight Router
==============================

DXF validation before CAM processing.

Endpoints:
- POST /preflight: Validate DXF for CAM readiness
"""

from typing import Any, Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from ...cam.dxf_preflight import DXFPreflight, generate_html_report

router = APIRouter(tags=["blueprint-cam-bridge"])


@router.post("/preflight")
async def dxf_preflight(
    file: UploadFile = File(..., description="DXF file to validate"),
    format: str = Form(default="json")  # "json" or "html"
) -> Dict[str, Any]:
    """
    Phase 3.2: DXF Preflight Validation

    Validates DXF files before CAM processing to catch issues early.

    Checks:
        - Layer validation (required layers present)
        - Closed path validation (all LWPOLYLINE closed)
        - Entity type validation (CAM-compatible entities)
        - Dimension validation (reasonable sizes for guitar lutherie)
        - Geometry sanity (no zero-length segments, degenerate paths)

    Severity Levels:
        - ERROR: Must fix (blocks CAM processing)
        - WARNING: Should fix (may cause issues)
        - INFO: Nice to know (optimization suggestions)

    Args:
        file: DXF file to validate
        format: Output format - "json" or "html"

    Returns:
        JSON: PreflightReport with issues array
        HTML: Visual report with color-coded issues

    Raises:
        HTTPException 500: Preflight validation failed
    """
    # Security patch: Validate file size and extension before reading
    from app.cam.dxf_upload_guard import read_dxf_with_validation

    dxf_bytes = await read_dxf_with_validation(file)

    # Run preflight checks
    try:
        preflight = DXFPreflight(dxf_bytes, filename=file.filename)
        report = preflight.run_all_checks()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preflight validation failed: {str(e)}"
        )

    # Return in requested format
    if format.lower() == "html":
        html = generate_html_report(report)
        return HTMLResponse(content=html, status_code=200)
    else:
        # JSON format
        return {
            "filename": report.filename,
            "dxf_version": report.dxf_version,
            "passed": report.passed,
            "total_entities": report.total_entities,
            "layers": report.layers,
            "issues": [
                {
                    "severity": issue.severity,
                    "message": issue.message,
                    "category": issue.category,
                    "layer": issue.layer,
                    "entity_handle": issue.entity_handle,
                    "entity_type": issue.entity_type,
                    "suggestion": issue.suggestion
                }
                for issue in report.issues
            ],
            "stats": report.stats,
            "summary": {
                "errors": report.error_count(),
                "warnings": report.warning_count(),
                "info": report.info_count()
            },
            "timestamp": report.timestamp
        }
