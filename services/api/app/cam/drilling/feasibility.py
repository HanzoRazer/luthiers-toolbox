"""
Drilling Feasibility Check

Minimal feasibility validation for drilling operations.
Part of the OPERATION lane requirements (8I).

This mirrors the validation in peck_cycle.py _validate() but
runs BEFORE toolpath generation to enable early blocking.

Key validations:
- Depth/diameter ratio warning (ratio > 10 triggers warning)
- Peck depth coherence
- Feed rate bounds
- Z height safety
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DrillingFeasibilityResult:
    """Result of drilling feasibility check."""

    feasible: bool
    risk_level: str  # "low", "medium", "high", "blocked"
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feasible": self.feasible,
            "risk_level": self.risk_level,
            "issues": self.issues,
            "warnings": self.warnings,
            "summary": self.summary,
        }


def compute_drilling_feasibility(
    *,
    hole_depth_mm: float,
    hole_diameter_mm: float,
    peck_depth_mm: float,
    peck_drilling: bool,
    feed_rate_mm_min: float,
    spindle_rpm: int,
    safe_z_mm: float,
    retract_z_mm: float,
    hole_count: int,
    dwell_ms: int,
) -> DrillingFeasibilityResult:
    """
    Compute feasibility for a drilling operation.

    Validates:
    - Depth/diameter ratio (warn if > 10, matches peck_cycle.py behavior)
    - Peck depth vs hole depth coherence
    - Feed rate bounds
    - Spindle RPM bounds
    - Z height safety
    - Hole count reasonableness

    Args:
        hole_depth_mm: Total hole depth
        hole_diameter_mm: Drill bit diameter
        peck_depth_mm: Depth per peck (Q value)
        peck_drilling: Whether peck drilling is enabled
        feed_rate_mm_min: Plunge feed rate
        spindle_rpm: Spindle speed
        safe_z_mm: Safe travel height
        retract_z_mm: Retract plane height
        hole_count: Number of holes
        dwell_ms: Dwell time at bottom

    Returns:
        DrillingFeasibilityResult with feasibility status and issues
    """
    issues: List[str] = []
    warnings: List[str] = []

    # Hole depth validation
    if hole_depth_mm <= 0:
        issues.append("hole_depth_mm must be > 0")
    elif hole_depth_mm > 100.0:
        warnings.append(f"hole_depth_mm={hole_depth_mm}mm is very deep for CNC drilling")

    # Hole diameter validation
    if hole_diameter_mm <= 0:
        issues.append("hole_diameter_mm must be > 0")
    elif hole_diameter_mm < 0.5:
        warnings.append(f"hole_diameter_mm={hole_diameter_mm}mm is very small")
    elif hole_diameter_mm > 25.0:
        warnings.append(f"hole_diameter_mm={hole_diameter_mm}mm is large for drilling")

    # Depth/diameter ratio check - matches peck_cycle.py _validate()
    if hole_diameter_mm > 0:
        ratio = hole_depth_mm / hole_diameter_mm
        if ratio > 10:
            warnings.append(
                f"Deep hole warning: depth/diameter ratio is {ratio:.1f}. "
                "Consider using smaller peck depth or pilot hole."
            )

    # Peck depth validation
    if peck_drilling:
        if peck_depth_mm <= 0:
            issues.append("peck_depth_mm must be > 0 when peck_drilling is True")
        elif peck_depth_mm > hole_depth_mm:
            warnings.append(
                f"peck_depth_mm ({peck_depth_mm}mm) exceeds hole_depth_mm "
                f"({hole_depth_mm}mm); will use single pass"
            )

    # Feed rate validation
    if feed_rate_mm_min <= 0:
        issues.append("feed_rate_mm_min must be > 0")
    elif feed_rate_mm_min < 10:
        warnings.append("feed_rate_mm_min < 10 is extremely slow")
    elif feed_rate_mm_min > 1000:
        warnings.append(f"feed_rate_mm_min={feed_rate_mm_min} is aggressive for drilling")

    # Spindle RPM validation
    if spindle_rpm <= 0:
        issues.append("spindle_rpm must be > 0")
    elif spindle_rpm < 500:
        warnings.append("spindle_rpm < 500 is very slow for drilling")
    elif spindle_rpm > 20000:
        warnings.append(f"spindle_rpm={spindle_rpm} is very high")

    # Z heights validation
    if safe_z_mm <= 0:
        issues.append("safe_z_mm must be > 0")
    if retract_z_mm <= 0:
        issues.append("retract_z_mm must be > 0")
    if retract_z_mm > safe_z_mm:
        warnings.append("retract_z_mm > safe_z_mm - will use safe_z for both")

    # Hole count validation
    if hole_count < 1:
        issues.append("hole_count must be >= 1")
    elif hole_count > 500:
        warnings.append(f"hole_count={hole_count} is very high - verify pattern")

    # Dwell validation
    if dwell_ms < 0:
        issues.append("dwell_ms must be >= 0")
    elif dwell_ms > 2000:
        warnings.append(f"dwell_ms={dwell_ms} is unusually long")

    # Calculate peck count for summary
    if peck_drilling and peck_depth_mm > 0:
        import math
        peck_count = math.ceil(hole_depth_mm / peck_depth_mm)
    else:
        peck_count = 1

    # Determine risk level
    if issues:
        risk_level = "blocked"
        feasible = False
    elif len(warnings) >= 3:
        risk_level = "high"
        feasible = True
    elif warnings:
        risk_level = "medium"
        feasible = True
    else:
        risk_level = "low"
        feasible = True

    summary = {
        "hole_count": hole_count,
        "hole_depth_mm": hole_depth_mm,
        "hole_diameter_mm": hole_diameter_mm,
        "depth_diameter_ratio": round(hole_depth_mm / hole_diameter_mm, 1) if hole_diameter_mm > 0 else 0,
        "peck_count_per_hole": peck_count,
        "peck_drilling": peck_drilling,
    }

    return DrillingFeasibilityResult(
        feasible=feasible,
        risk_level=risk_level,
        issues=issues,
        warnings=warnings,
        summary=summary,
    )


def hash_feasibility_result(result: DrillingFeasibilityResult) -> str:
    """Generate SHA256 hash of feasibility result for provenance."""
    data = json.dumps(result.to_dict(), sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()
