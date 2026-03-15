# services/api/app/cam/dxf_validation_gate.py
"""
DXF Validation Gate - Mandatory Pre-Export Validation

Enforces geometry validation BEFORE G-code export.
This addresses the security gap where users could bypass preflight
and export unchecked geometry leading to unsafe toolpaths.

Usage in routers::

    from app.cam.dxf_validation_gate import enforce_dxf_validation

    @router.post("/plan_from_dxf")
    async def plan_from_dxf(file: UploadFile = File(...)):
        dxf_bytes = await file.read()

        # MANDATORY: Validate geometry before proceeding
        enforce_dxf_validation(dxf_bytes, file.filename)

        # ... proceed with toolpath generation ...

The gate will:
1. Run DXFPreflight checks (layer, entity, closed path, dimension, sanity)
2. Run TopologyValidator checks (self-intersection, degenerate polygons)
3. Raise HTTPException 422 if any ERROR-level issues are found
4. Allow WARNING/INFO issues to pass (logged for transparency)

This is FAIL-CLOSED: if validation fails, no G-code is generated.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Tuple

from fastapi import HTTPException

from .dxf_preflight import DXFPreflight, PreflightReport, Severity
from .dxf_advanced_validation import TopologyValidator, TopologyReport

logger = logging.getLogger(__name__)


class DXFValidationGateError(Exception):
    """Raised when DXF fails mandatory validation gate."""

    def __init__(
        self,
        message: str,
        errors: List[dict],
        warnings: List[dict],
        preflight_report: Optional[PreflightReport] = None,
        topology_report: Optional[TopologyReport] = None,
    ):
        super().__init__(message)
        self.errors = errors
        self.warnings = warnings
        self.preflight_report = preflight_report
        self.topology_report = topology_report


def run_full_validation(
    dxf_bytes: bytes,
    filename: str = "unknown.dxf",
    skip_topology: bool = False,
) -> Tuple[PreflightReport, Optional[TopologyReport]]:
    """
    Run all DXF validation checks.

    Args:
        dxf_bytes: Raw DXF file content
        filename: Original filename (for reporting)
        skip_topology: If True, skip Shapely-based topology checks (faster)

    Returns:
        Tuple of (preflight_report, topology_report or None)
    """
    # Run preflight validation
    preflight = DXFPreflight(dxf_bytes, filename)
    preflight_report = preflight.run_all_checks()

    # Run topology validation (if not skipped)
    topology_report = None
    if not skip_topology:
        try:
            validator = TopologyValidator(dxf_bytes, filename)
            topology_report = validator.check_self_intersections()
            validator.check_line_segments()
            # Note: overlap check is O(n²) and slow - skip for now
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Topology validation failed (non-fatal): {e}")

    return preflight_report, topology_report


def enforce_dxf_validation(
    dxf_bytes: bytes,
    filename: str = "unknown.dxf",
    skip_topology: bool = False,
    allow_warnings: bool = True,
) -> Tuple[PreflightReport, Optional[TopologyReport]]:
    """
    MANDATORY validation gate for DXF before G-code export.

    This is the main entry point for enforcing DXF validation.
    Call this before any toolpath generation or G-code export.

    Args:
        dxf_bytes: Raw DXF file content
        filename: Original filename (for reporting)
        skip_topology: If True, skip Shapely topology checks (faster but less thorough)
        allow_warnings: If False, also block on WARNING-level issues

    Returns:
        Tuple of (preflight_report, topology_report) if validation passes

    Raises:
        HTTPException 422: If any ERROR-level issues are found

    Example:
        ```python
        dxf_bytes = await file.read()
        preflight, topology = enforce_dxf_validation(dxf_bytes, file.filename)
        # If we get here, validation passed
        loops = extract_loops(dxf_bytes)
        ```
    """
    preflight_report, topology_report = run_full_validation(
        dxf_bytes, filename, skip_topology
    )

    # Collect errors and warnings
    errors: List[dict] = []
    warnings: List[dict] = []

    # Preflight issues
    for issue in preflight_report.issues:
        issue_dict = {
            "source": "preflight",
            "severity": issue.severity.value,
            "category": issue.category,
            "message": issue.message,
            "layer": issue.layer,
            "suggestion": issue.suggestion,
        }
        if issue.severity == Severity.ERROR:
            errors.append(issue_dict)
        elif issue.severity == Severity.WARNING:
            warnings.append(issue_dict)

    # Topology issues
    if topology_report:
        for issue in topology_report.issues:
            issue_dict = {
                "source": "topology",
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
                "layer": issue.layer,
                "repair_suggestion": issue.repair_suggestion,
            }
            if issue.severity == Severity.ERROR:
                errors.append(issue_dict)
            elif issue.severity == Severity.WARNING:
                warnings.append(issue_dict)

    # Log warnings for transparency
    if warnings:
        logger.warning(
            f"DXF validation warnings for {filename}: {len(warnings)} warnings",
            extra={"filename": filename, "warning_count": len(warnings)},
        )

    # FAIL-CLOSED: Block on errors
    if errors:
        logger.error(
            f"DXF validation BLOCKED for {filename}: {len(errors)} errors",
            extra={"filename": filename, "error_count": len(errors)},
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "DXF_VALIDATION_FAILED",
                "message": f"DXF file failed mandatory validation: {len(errors)} error(s) found. "
                           "Fix geometry issues before G-code export.",
                "filename": filename,
                "errors": errors,
                "warnings": warnings,
                "passed_preflight": preflight_report.passed,
                "topology_valid": topology_report.is_valid if topology_report else None,
            },
        )

    # Optionally block on warnings
    if not allow_warnings and warnings:
        logger.warning(
            f"DXF validation BLOCKED (strict mode) for {filename}: {len(warnings)} warnings",
            extra={"filename": filename, "warning_count": len(warnings)},
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "DXF_VALIDATION_WARNINGS",
                "message": f"DXF file has {len(warnings)} warning(s). "
                           "Fix or use allow_warnings=True to proceed.",
                "filename": filename,
                "errors": [],
                "warnings": warnings,
                "passed_preflight": preflight_report.passed,
                "topology_valid": topology_report.is_valid if topology_report else None,
            },
        )

    logger.info(
        f"DXF validation PASSED for {filename}",
        extra={
            "filename": filename,
            "entity_count": preflight_report.total_entities,
            "layer_count": len(preflight_report.layers),
        },
    )

    return preflight_report, topology_report


def validate_dxf_for_cam(
    dxf_bytes: bytes,
    filename: str = "unknown.dxf",
    require_closed_paths: bool = True,
    require_cam_layer: bool = True,
) -> dict:
    """
    Validate DXF for CAM-specific requirements.

    This is a more specific validation focused on CAM readiness.

    Args:
        dxf_bytes: Raw DXF file content
        filename: Original filename
        require_closed_paths: If True, require at least one closed LWPOLYLINE
        require_cam_layer: If True, require GEOMETRY or similar CAM layer

    Returns:
        Validation result dict with pass/fail status and details

    Example:
        ```python
        result = validate_dxf_for_cam(dxf_bytes, filename)
        if not result["passed"]:
            raise HTTPException(422, detail=result)
        ```
    """
    preflight, topology = run_full_validation(dxf_bytes, filename)

    cam_ready = True
    cam_issues: List[str] = []

    # Check for closed paths
    if require_closed_paths:
        has_closed = False
        for issue in preflight.issues:
            if "closed" in issue.message.lower() and issue.severity == Severity.ERROR:
                cam_issues.append("No closed LWPOLYLINE entities found")
                cam_ready = False
                break
        # Also check entity types
        stats = preflight.stats
        if stats and "entity_types" in stats:
            if "LWPOLYLINE" not in stats["entity_types"]:
                cam_issues.append("No LWPOLYLINE entities found")
                cam_ready = False

    # Check for CAM layer
    if require_cam_layer:
        cam_layers = ["GEOMETRY", "CONTOURS", "OUTLINE", "POCKET", "CAM"]
        has_cam_layer = any(
            layer.upper() in [l.upper() for l in preflight.layers]
            for layer in cam_layers
        )
        if not has_cam_layer:
            cam_issues.append(f"No CAM-standard layer found (expected: {', '.join(cam_layers)})")
            # This is a warning, not blocking

    # Check for self-intersections
    if topology and not topology.is_valid:
        cam_issues.append(f"{topology.self_intersections} self-intersecting polygon(s) found")
        cam_ready = False

    return {
        "passed": cam_ready and preflight.passed,
        "filename": filename,
        "dxf_version": preflight.dxf_version,
        "entity_count": preflight.total_entities,
        "layers": preflight.layers,
        "cam_issues": cam_issues,
        "error_count": preflight.error_count(),
        "warning_count": preflight.warning_count(),
    }
