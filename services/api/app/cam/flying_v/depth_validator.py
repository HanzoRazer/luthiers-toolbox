# services/api/app/cam/flying_v/depth_validator.py
"""
Flying V Depth Validator

Resolves FV-GAP-10: Flying V neck pocket depth validation.

Validates G-code depths against spec JSON before output:
- Neck pocket depth must match tenon_depth_mm (19mm for Flying V)
- Control cavity depth must match control_cavity.depth_mm (35mm)
- Pickup cavity depths must match pickup route_depth_mm (19mm)

Integrates with the shared gcode_verify stack: scripts/utils/gcode_verify.py
calls app.cam.preflight_gate.preflight_validate for general G-code sanity
(units, spindle, feed, depth vs stock). This module adds spec-specific depth
checks. Call validate_flying_v_gcode_with_preflight() to run both, or run
verify_gcode() from gcode_verify then validate_*_depth() for two-step validation.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pocket_generator import FlyingVSpec, load_flying_v_spec

log = logging.getLogger(__name__)


@dataclass
class DepthValidationResult:
    """Result of depth validation."""
    ok: bool
    operation: str
    expected_depth_mm: float
    actual_depths: List[float]
    min_depth: float
    max_depth: float
    tolerance_mm: float
    errors: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "operation": self.operation,
            "expected_depth_mm": self.expected_depth_mm,
            "actual_depths": self.actual_depths,
            "min_depth": self.min_depth,
            "max_depth": self.max_depth,
            "tolerance_mm": self.tolerance_mm,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _extract_z_depths(gcode: str) -> List[float]:
    """
    Extract all Z depth values from G-code.

    Returns list of negative Z values (cutting depths).
    """
    depths = []

    # Match G0/G1 Z moves and G83 Z values
    z_pattern = re.compile(r"[GZ][-+]?\d*\.?\d+", re.IGNORECASE)

    for line in gcode.split("\n"):
        line = line.strip()
        if not line or line.startswith("(") or line.startswith(";"):
            continue

        # Skip G0 Z moves that are retracts (positive Z)
        if "G0" in line.upper() and "Z" in line.upper():
            z_match = re.search(r"Z([-+]?\d*\.?\d+)", line, re.IGNORECASE)
            if z_match:
                z_val = float(z_match.group(1))
                if z_val < 0:
                    depths.append(z_val)
            continue

        # G1 Z moves (plunges)
        if "G1" in line.upper() and "Z" in line.upper():
            z_match = re.search(r"Z([-+]?\d*\.?\d+)", line, re.IGNORECASE)
            if z_match:
                z_val = float(z_match.group(1))
                if z_val < 0:
                    depths.append(z_val)

        # G83 peck drilling Z depth
        if "G83" in line.upper():
            z_match = re.search(r"Z([-+]?\d*\.?\d+)", line, re.IGNORECASE)
            if z_match:
                z_val = float(z_match.group(1))
                if z_val < 0:
                    depths.append(z_val)

    return depths


def validate_neck_pocket_depth(
    gcode: str,
    spec: Optional[FlyingVSpec] = None,
    tolerance_mm: float = 0.5,
) -> DepthValidationResult:
    """
    Validate neck pocket G-code against spec depth.

    Args:
        gcode: G-code text to validate
        spec: Flying V spec (loads default if None)
        tolerance_mm: Acceptable depth deviation (default 0.5mm)

    Returns:
        DepthValidationResult with pass/fail status.
    """
    if spec is None:
        spec = load_flying_v_spec()

    expected_depth = spec.neck_pocket.depth_mm
    depths = _extract_z_depths(gcode)

    errors = []
    warnings = []

    if not depths:
        errors.append("No Z depth values found in G-code")
        return DepthValidationResult(
            ok=False,
            operation="neck_pocket",
            expected_depth_mm=expected_depth,
            actual_depths=[],
            min_depth=0.0,
            max_depth=0.0,
            tolerance_mm=tolerance_mm,
            errors=errors,
            warnings=warnings,
        )

    # Convert to positive depths for comparison
    positive_depths = [abs(d) for d in depths]
    max_depth = max(positive_depths)
    min_depth = min(positive_depths)

    # Check if max depth matches expected within tolerance
    depth_error = abs(max_depth - expected_depth)

    if depth_error > tolerance_mm:
        errors.append(
            f"Neck pocket depth mismatch: expected {expected_depth:.2f}mm, "
            f"got {max_depth:.2f}mm (error: {depth_error:.2f}mm)"
        )

    # Warning if depth variance is large (could indicate stepdown issues)
    if max_depth - min_depth > expected_depth * 0.8:
        warnings.append(
            f"Large depth variance detected: {min_depth:.2f}mm to {max_depth:.2f}mm"
        )

    # Warning if cutting deeper than spec
    if max_depth > expected_depth + tolerance_mm:
        warnings.append(
            f"Cutting {max_depth - expected_depth:.2f}mm deeper than spec!"
        )

    ok = len(errors) == 0

    return DepthValidationResult(
        ok=ok,
        operation="neck_pocket",
        expected_depth_mm=expected_depth,
        actual_depths=positive_depths,
        min_depth=min_depth,
        max_depth=max_depth,
        tolerance_mm=tolerance_mm,
        errors=errors,
        warnings=warnings,
    )


def validate_control_cavity_depth(
    gcode: str,
    spec: Optional[FlyingVSpec] = None,
    tolerance_mm: float = 0.5,
) -> DepthValidationResult:
    """
    Validate control cavity G-code against spec depth.

    Args:
        gcode: G-code text to validate
        spec: Flying V spec (loads default if None)
        tolerance_mm: Acceptable depth deviation

    Returns:
        DepthValidationResult with pass/fail status.
    """
    if spec is None:
        spec = load_flying_v_spec()

    expected_depth = spec.control_cavity.depth_mm
    depths = _extract_z_depths(gcode)

    errors = []
    warnings = []

    if not depths:
        errors.append("No Z depth values found in G-code")
        return DepthValidationResult(
            ok=False,
            operation="control_cavity",
            expected_depth_mm=expected_depth,
            actual_depths=[],
            min_depth=0.0,
            max_depth=0.0,
            tolerance_mm=tolerance_mm,
            errors=errors,
            warnings=warnings,
        )

    positive_depths = [abs(d) for d in depths]
    max_depth = max(positive_depths)
    min_depth = min(positive_depths)

    depth_error = abs(max_depth - expected_depth)

    if depth_error > tolerance_mm:
        errors.append(
            f"Control cavity depth mismatch: expected {expected_depth:.2f}mm, "
            f"got {max_depth:.2f}mm (error: {depth_error:.2f}mm)"
        )

    # Check for going through body
    body_thickness = spec.body_thickness_mm
    if max_depth > body_thickness - 5.0:  # Leave at least 5mm
        warnings.append(
            f"Control cavity depth {max_depth:.2f}mm is close to body thickness "
            f"({body_thickness:.2f}mm) - risk of breakthrough!"
        )

    ok = len(errors) == 0

    return DepthValidationResult(
        ok=ok,
        operation="control_cavity",
        expected_depth_mm=expected_depth,
        actual_depths=positive_depths,
        min_depth=min_depth,
        max_depth=max_depth,
        tolerance_mm=tolerance_mm,
        errors=errors,
        warnings=warnings,
    )


def validate_all_depths(
    gcode_dict: Dict[str, str],
    spec: Optional[FlyingVSpec] = None,
    tolerance_mm: float = 0.5,
) -> Dict[str, DepthValidationResult]:
    """
    Validate all cavity depths at once.

    Args:
        gcode_dict: Dict mapping operation name to G-code text
                   Keys: "neck_pocket", "control_cavity", "pickup_neck", "pickup_bridge"
        spec: Flying V spec (loads default if None)
        tolerance_mm: Acceptable depth deviation

    Returns:
        Dict mapping operation name to DepthValidationResult.
    """
    if spec is None:
        spec = load_flying_v_spec()

    results = {}

    if "neck_pocket" in gcode_dict:
        results["neck_pocket"] = validate_neck_pocket_depth(
            gcode_dict["neck_pocket"], spec, tolerance_mm
        )

    if "control_cavity" in gcode_dict:
        results["control_cavity"] = validate_control_cavity_depth(
            gcode_dict["control_cavity"], spec, tolerance_mm
        )

    # Pickup cavities use same depth validation pattern
    for key in ["pickup_neck", "pickup_bridge"]:
        if key in gcode_dict:
            expected_depth = (
                spec.neck_pickup.depth_mm
                if "neck" in key
                else spec.bridge_pickup.depth_mm
            )
            depths = _extract_z_depths(gcode_dict[key])

            errors = []
            warnings = []

            if depths:
                positive_depths = [abs(d) for d in depths]
                max_depth = max(positive_depths)
                min_depth = min(positive_depths)

                if abs(max_depth - expected_depth) > tolerance_mm:
                    errors.append(
                        f"{key} depth mismatch: expected {expected_depth:.2f}mm, "
                        f"got {max_depth:.2f}mm"
                    )
            else:
                positive_depths = []
                max_depth = 0.0
                min_depth = 0.0
                errors.append("No Z depth values found")

            results[key] = DepthValidationResult(
                ok=len(errors) == 0,
                operation=key,
                expected_depth_mm=expected_depth,
                actual_depths=positive_depths,
                min_depth=min_depth,
                max_depth=max_depth,
                tolerance_mm=tolerance_mm,
                errors=errors,
                warnings=warnings,
            )

    return results


def validate_flying_v_gcode_file(
    filepath: Path,
    operation: str,
    spec: Optional[FlyingVSpec] = None,
    tolerance_mm: float = 0.5,
) -> DepthValidationResult:
    """
    Validate a Flying V G-code file.

    Args:
        filepath: Path to .nc file
        operation: Operation type ("neck_pocket", "control_cavity", etc.)
        spec: Flying V spec (loads default if None)
        tolerance_mm: Acceptable depth deviation

    Returns:
        DepthValidationResult.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return DepthValidationResult(
            ok=False,
            operation=operation,
            expected_depth_mm=0.0,
            actual_depths=[],
            min_depth=0.0,
            max_depth=0.0,
            tolerance_mm=tolerance_mm,
            errors=[f"File not found: {filepath}"],
            warnings=[],
        )

    gcode = filepath.read_text(encoding="utf-8")

    if operation == "neck_pocket":
        return validate_neck_pocket_depth(gcode, spec, tolerance_mm)
    elif operation == "control_cavity":
        return validate_control_cavity_depth(gcode, spec, tolerance_mm)
    else:
        # Generic depth validation
        if spec is None:
            spec = load_flying_v_spec()

        depths = _extract_z_depths(gcode)
        errors = []
        warnings = []

        if not depths:
            errors.append("No Z depth values found")

        positive_depths = [abs(d) for d in depths] if depths else []
        max_depth = max(positive_depths) if positive_depths else 0.0
        min_depth = min(positive_depths) if positive_depths else 0.0

        return DepthValidationResult(
            ok=len(errors) == 0,
            operation=operation,
            expected_depth_mm=0.0,  # Unknown for generic
            actual_depths=positive_depths,
            min_depth=min_depth,
            max_depth=max_depth,
            tolerance_mm=tolerance_mm,
            errors=errors,
            warnings=warnings,
        )


def validate_flying_v_gcode_with_preflight(
    gcode: str,
    operation: str,
    spec: Optional[FlyingVSpec] = None,
    tolerance_mm: float = 0.5,
) -> Tuple[Any, DepthValidationResult]:
    """
    Validate Flying V G-code using shared preflight stack then spec depth check (FV-GAP-10).

    Same preflight_gate used by scripts/utils/gcode_verify.verify_gcode().
    Returns (preflight_result_dict, depth_validation_result).
    """
    if spec is None:
        spec = load_flying_v_spec()

    preflight_result: Dict[str, Any] = {"ok": True, "errors": [], "warnings": [], "summary": {}}
    try:
        from app.cam.preflight_gate import (
            preflight_validate,
            PreflightConfig,
            PreflightBlockedError,
        )

        config = PreflightConfig(
            stock_thickness_mm=spec.body_thickness_mm,
            require_units_mm=True,
            require_absolute=True,
            require_spindle_on=True,
            require_feed_on_cut=True,
        )
        result = preflight_validate(gcode, config=config)
        preflight_result = {
            "ok": result.ok,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "summary": result.summary,
        }
    except (ImportError, PreflightBlockedError, ValueError, TypeError, RuntimeError) as e:
        error_id = str(uuid.uuid4())[:8]
        log.error(
            "preflight_setup_failed",
            extra={"error_id": error_id, "error": str(e)},
            exc_info=True,
        )
        preflight_result = {
            "ok": False,
            "errors": [f"[{error_id}] {str(e)}"],
            "warnings": [],
            "summary": {},
        }
        # Safety-critical fail-closed behavior: do not continue depth checks
        depth_result = DepthValidationResult(
            ok=False,
            operation=operation,
            expected_depth_mm=0.0,
            actual_depths=[],
            min_depth=0.0,
            max_depth=0.0,
            tolerance_mm=tolerance_mm,
            errors=["Preflight failed; depth validation skipped."],
            warnings=[],
        )
        return preflight_result, depth_result

    if operation == "neck_pocket":
        depth_result = validate_neck_pocket_depth(gcode, spec, tolerance_mm)
    elif operation == "control_cavity":
        depth_result = validate_control_cavity_depth(gcode, spec, tolerance_mm)
    elif operation in ("pickup_neck", "pickup_bridge"):
        expected = spec.neck_pickup.depth_mm if "neck" in operation else spec.bridge_pickup.depth_mm
        depths = _extract_z_depths(gcode)
        errors = []
        warnings = []
        if not depths:
            errors.append("No Z depth values found")
            positive_depths = []
            max_d, min_d = 0.0, 0.0
        else:
            positive_depths = [abs(d) for d in depths]
            max_d = max(positive_depths)
            min_d = min(positive_depths)
            if abs(max_d - expected) > tolerance_mm:
                errors.append(f"Depth mismatch: expected {expected:.2f}mm, got {max_d:.2f}mm")
        depth_result = DepthValidationResult(
            ok=len(errors) == 0,
            operation=operation,
            expected_depth_mm=expected,
            actual_depths=positive_depths if depths else [],
            min_depth=min_d,
            max_depth=max_d,
            tolerance_mm=tolerance_mm,
            errors=errors,
            warnings=warnings,
        )
    else:
        depths = _extract_z_depths(gcode)
        errors = [] if depths else ["No Z depth values found"]
        warnings = []
        positive_depths = [abs(d) for d in depths] if depths else []
        max_d = max(positive_depths) if positive_depths else 0.0
        min_d = min(positive_depths) if positive_depths else 0.0
        depth_result = DepthValidationResult(
            ok=len(errors) == 0,
            operation=operation,
            expected_depth_mm=0.0,
            actual_depths=positive_depths,
            min_depth=min_d,
            max_depth=max_d,
            tolerance_mm=tolerance_mm,
            errors=errors,
            warnings=warnings,
        )

    return preflight_result, depth_result
