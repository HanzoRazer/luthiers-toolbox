# services/api/app/util/dxf_preflight.py
"""
DXF Preflight wrapper for pipeline_operations.py compatibility.

This module provides the interface expected by pipeline_operations.py,
wrapping the actual implementation in cam/dxf_preflight.py.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Exception types expected by pipeline_operations.py
# =============================================================================
class PreflightEngineMissingError(Exception):
    """Raised when the DXF parsing engine is unavailable."""
    pass


class PreflightParseError(Exception):
    """Raised when DXF parsing fails."""
    pass


class PreflightGeometryError(Exception):
    """Raised when geometry validation fails critically."""
    pass


# =============================================================================
# Result type expected by pipeline_operations.py
# =============================================================================
@dataclass
class PreflightResult:
    """Result type matching pipeline_operations.py expectations."""
    ok: bool
    units: str = "mm"
    layers: List[str] = field(default_factory=list)
    candidate_layers: List[str] = field(default_factory=list)
    issues: List[Any] = field(default_factory=list)
    debug: Optional[Dict[str, Any]] = None


@dataclass
class PreflightIssue:
    """Issue type matching pipeline_operations.py expectations."""
    level: str  # "error", "warning", "info"
    code: str
    message: str
    entity_id: Optional[str] = None
    layer: Optional[str] = None


# =============================================================================
# Main preflight function
# =============================================================================
def preflight_dxf_bytes(
    dxf_bytes: bytes,
    *,
    cam_layer_prefix: Optional[str] = None,
    profile: Optional[str] = None,
    debug: bool = False,
) -> PreflightResult:
    """
    Run DXF preflight validation on raw bytes.

    Args:
        dxf_bytes: Raw DXF file content
        cam_layer_prefix: Optional layer prefix filter for CAM layers
        profile: Optional profile name for validation rules
        debug: Whether to include debug information

    Returns:
        PreflightResult with validation results

    Raises:
        PreflightParseError: If DXF parsing fails
        PreflightGeometryError: If critical geometry issues found
    """
    try:
        from ..cam.dxf_preflight import DXFPreflight, Severity
    except ImportError as e:
        raise PreflightEngineMissingError(f"DXF preflight engine not available: {e}")

    try:
        preflight = DXFPreflight(dxf_bytes)
        report = preflight.run_all_checks()
    except Exception as e:
        logger.warning("DXF preflight parse error: %s", e)
        raise PreflightParseError(f"Failed to parse DXF: {e}")

    # Convert issues to expected format
    issues = []
    for issue in report.issues:
        level = issue.severity.value.lower()  # ERROR -> error
        issues.append(PreflightIssue(
            level=level,
            code=issue.category,
            message=issue.message,
            entity_id=issue.entity_handle,
            layer=issue.layer,
        ))

    # Filter candidate layers by prefix if specified
    candidate_layers = report.layers
    if cam_layer_prefix:
        candidate_layers = [
            layer for layer in report.layers
            if layer.upper().startswith(cam_layer_prefix.upper())
        ]

    # Determine overall ok status
    ok = report.passed

    # Build debug info if requested
    debug_info = None
    if debug:
        debug_info = {
            "dxf_version": report.dxf_version,
            "total_entities": report.total_entities,
            "stats": report.stats,
            "error_count": report.error_count(),
            "warning_count": report.warning_count(),
        }

    return PreflightResult(
        ok=ok,
        units="mm",  # DXF preflight doesn't track units yet
        layers=report.layers,
        candidate_layers=candidate_layers,
        issues=issues,
        debug=debug_info,
    )
