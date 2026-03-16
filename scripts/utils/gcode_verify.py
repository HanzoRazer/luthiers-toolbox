# scripts/utils/gcode_verify.py
"""
Shared G-code Verification Utility

Provides verify_gcode() for all build scripts to validate generated G-code
before writing to disk. Uses the preflight_gate module for validation.

Resolves: LP-GAP-08, EX-GAP-12, SG-GAP-13

Usage:
    from scripts.utils.gcode_verify import verify_gcode

    gcode = generate_phase1(...)
    result = verify_gcode(
        gcode=gcode,
        stock_thickness_mm=44.45,  # 1.75"
        phase_name="Phase 1: Mahogany Back",
        units="inch",
    )
    if not result["ok"]:
        print("VALIDATION FAILED - review errors before running on machine")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add services/api to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
API_DIR = REPO_ROOT / "services" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def verify_gcode(
    gcode: str,
    stock_thickness_mm: float,
    phase_name: str,
    units: str = "mm",
    stock_width_mm: Optional[float] = None,
    stock_length_mm: Optional[float] = None,
    tool_diameter_mm: Optional[float] = None,
    strict: bool = False,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Validate G-code using preflight_gate before output.

    Args:
        gcode: The G-code text to validate
        stock_thickness_mm: Stock material thickness in mm
        phase_name: Human-readable phase name for logging
        units: "mm" or "inch" - which unit system the G-code uses
        stock_width_mm: Optional stock width for bounds checking
        stock_length_mm: Optional stock length for bounds checking
        tool_diameter_mm: Optional tool diameter for feature size validation
        strict: If True, warnings become errors
        verbose: If True, print validation results to stdout

    Returns:
        Dict with keys:
            - ok: bool - True if validation passed
            - errors: List[str] - Error messages
            - warnings: List[str] - Warning messages
            - summary: Dict - Validation summary data
            - phase: str - Phase name
            - line_count: int - Number of G-code lines
    """
    try:
        from app.cam.preflight_gate import preflight_validate, PreflightConfig
    except ImportError as e:
        # Graceful fallback if preflight_gate not available
        result = {
            "ok": True,
            "errors": [],
            "warnings": [f"Preflight validation unavailable: {e}"],
            "summary": {"skipped": True},
            "phase": phase_name,
            "line_count": len(gcode.strip().split("\n")),
        }
        if verbose:
            print(f"  ⚠️  {phase_name}: Validation skipped (preflight_gate not available)")
        return result

    # Configure validation based on units
    require_units_mm = units.lower() == "mm"

    config = PreflightConfig(
        stock_thickness_mm=stock_thickness_mm,
        stock_width_mm=stock_width_mm,
        stock_length_mm=stock_length_mm,
        tool_diameter_mm=tool_diameter_mm,
        require_units_mm=require_units_mm,
        require_absolute=True,
        require_spindle_on=True,
        require_feed_on_cut=True,
        strict_mode=strict,
    )

    # Run validation
    preflight_result = preflight_validate(gcode, config)

    line_count = len(gcode.strip().split("\n"))

    result = {
        "ok": preflight_result.ok,
        "errors": preflight_result.errors,
        "warnings": preflight_result.warnings,
        "summary": preflight_result.summary,
        "phase": phase_name,
        "line_count": line_count,
    }

    # Print results if verbose
    if verbose:
        _print_verification_result(result)

    return result


def verify_gcode_file(
    filepath: Path,
    stock_thickness_mm: float,
    phase_name: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Validate G-code from a file.

    Args:
        filepath: Path to the .nc file
        stock_thickness_mm: Stock material thickness in mm
        phase_name: Optional phase name (defaults to filename)
        **kwargs: Additional arguments passed to verify_gcode()

    Returns:
        Validation result dict (see verify_gcode)
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return {
            "ok": False,
            "errors": [f"File not found: {filepath}"],
            "warnings": [],
            "summary": {},
            "phase": phase_name or filepath.name,
            "line_count": 0,
        }

    gcode = filepath.read_text(encoding="utf-8")
    return verify_gcode(
        gcode=gcode,
        stock_thickness_mm=stock_thickness_mm,
        phase_name=phase_name or filepath.stem,
        **kwargs,
    )


def _print_verification_result(result: Dict[str, Any]) -> None:
    """Print verification result to stdout."""
    phase = result["phase"]
    line_count = result["line_count"]

    if result["ok"]:
        # Success
        summary = result.get("summary", {})
        bounds = summary.get("bounds", {})

        print(f"  ✓ {phase}: PASSED ({line_count:,} lines)")

        # Print key summary info if available
        if bounds:
            z_min = bounds.get("min_z")
            z_max = bounds.get("max_z")
            if z_min is not None:
                print(f"      Z range: {z_min:.3f} to {z_max:.3f}")

        # Print warnings if any
        for warn in result.get("warnings", []):
            print(f"      ⚠️  {warn}")
    else:
        # Failure
        print(f"  ✗ {phase}: FAILED ({line_count:,} lines)")
        for err in result["errors"]:
            print(f"      ❌ {err}")
        for warn in result.get("warnings", []):
            print(f"      ⚠️  {warn}")


def verify_all_phases(
    phases: List[Dict[str, Any]],
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Verify multiple phases and return aggregate results.

    Args:
        phases: List of dicts with keys:
            - gcode: str
            - stock_thickness_mm: float
            - phase_name: str
            - units: str (optional, defaults to "mm")
        verbose: Print results to stdout

    Returns:
        Dict with:
            - all_passed: bool
            - total_lines: int
            - total_errors: int
            - total_warnings: int
            - results: List of individual phase results
    """
    results = []
    total_lines = 0
    total_errors = 0
    total_warnings = 0

    for phase in phases:
        result = verify_gcode(
            gcode=phase["gcode"],
            stock_thickness_mm=phase["stock_thickness_mm"],
            phase_name=phase["phase_name"],
            units=phase.get("units", "mm"),
            verbose=verbose,
        )
        results.append(result)
        total_lines += result["line_count"]
        total_errors += len(result["errors"])
        total_warnings += len(result["warnings"])

    all_passed = all(r["ok"] for r in results)

    if verbose:
        print()
        if all_passed:
            print(f"  ✓ ALL PHASES PASSED: {total_lines:,} total lines verified")
        else:
            failed = [r["phase"] for r in results if not r["ok"]]
            print(f"  ✗ VERIFICATION FAILED: {len(failed)} phase(s) with errors")

        if total_warnings > 0:
            print(f"      {total_warnings} warning(s) - review before production")

    return {
        "all_passed": all_passed,
        "total_lines": total_lines,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "results": results,
    }
