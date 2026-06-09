"""
Drilling Feasibility Check

Minimal feasibility validation for peck-drilling operations.
Part of the OPERATION lane requirements (Dev Order 8I).

Not a full physics model — validates basic parameter coherence and safety.
Observational: it warns or blocks; it never mutates intent.
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
    peck_drilling: bool,
    peck_depth_mm: float,
    hole_count: int,
    feed_rate_mm_min: float,
    spindle_rpm: float,
    safe_z_mm: float,
    retract_z_mm: float,
) -> DrillingFeasibilityResult:
    """
    Compute feasibility for a peck-drilling operation.

    BLOCKING rules (issues):
    - hole_diameter_mm <= 0
    - hole_depth_mm <= 0
    - hole_count < 1
    - peck_drilling and peck_depth_mm <= 0
    - peck_drilling and peck_depth_mm >= hole_depth_mm   (the mandatory peck rule)
    - safe_z_mm / retract_z_mm <= 0

    Observational warnings:
    - depth:diameter ratio > 10 (deep hole — chip clearing / pilot hole)
    - feed/spindle out of typical bounds
    - retract_z_mm > safe_z_mm
    """
    issues: List[str] = []
    warnings: List[str] = []

    # Drill diameter
    if hole_diameter_mm <= 0:
        issues.append("hole_diameter_mm must be > 0")
    elif hole_diameter_mm < 0.5:
        warnings.append(f"hole_diameter_mm={hole_diameter_mm}mm is very small — fragile drill")

    # Hole depth
    if hole_depth_mm <= 0:
        issues.append("hole_depth_mm must be > 0")

    # Hole count
    if hole_count < 1:
        issues.append("at least 1 hole is required")

    # Peck rule (MANDATORY, blocking)
    if peck_drilling:
        if peck_depth_mm <= 0:
            issues.append("peck_depth_mm must be > 0 when peck_drilling is True")
        elif peck_depth_mm >= hole_depth_mm:
            issues.append(
                f"peck_depth_mm ({peck_depth_mm}mm) must be < hole_depth_mm "
                f"({hole_depth_mm}mm) — a single peck reaching full depth is not a peck cycle"
            )

    # Depth:diameter ratio (deep-hole warning)
    if hole_diameter_mm > 0 and hole_depth_mm > 0:
        ratio = hole_depth_mm / hole_diameter_mm
        if ratio > 10:
            warnings.append(
                f"Deep hole: depth:diameter ratio is {ratio:.1f} — consider smaller "
                "peck depth or a pilot hole."
            )

    # Feed / spindle bounds
    if feed_rate_mm_min <= 0:
        issues.append("feed_rate_mm_min must be > 0")
    elif feed_rate_mm_min > 1000:
        warnings.append(f"feed_rate_mm_min={feed_rate_mm_min} is aggressive for drilling")
    if spindle_rpm <= 0:
        issues.append("spindle_rpm must be > 0")

    # Z heights
    if safe_z_mm <= 0:
        issues.append("safe_z_mm must be > 0")
    if retract_z_mm <= 0:
        issues.append("retract_z_mm must be > 0")
    if retract_z_mm > safe_z_mm:
        warnings.append("retract_z_mm > safe_z_mm — unusual; retract should sit below safe height")

    # Estimated peck count
    if peck_drilling and peck_depth_mm > 0 and hole_depth_mm > 0:
        peck_count = max(1, int((hole_depth_mm + peck_depth_mm - 0.001) / peck_depth_mm))
    else:
        peck_count = 1
    if peck_count > 50:
        warnings.append(f"Estimated {peck_count} pecks per hole — consider larger peck depth")

    # Risk level
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
        "estimated_pecks_per_hole": peck_count,
        "depth_diameter_ratio": round(hole_depth_mm / hole_diameter_mm, 2) if hole_diameter_mm > 0 else None,
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
