"""
Profile Feasibility Check

Minimal feasibility validation for profile operations.
Part of the OPERATION lane requirements (8H).

This is not a full physics model - it validates basic parameter
coherence and safety constraints.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProfileFeasibilityResult:
    """Result of profile feasibility check."""

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


def compute_profile_feasibility(
    *,
    tool_diameter_mm: float,
    cut_depth_mm: float,
    stepdown_mm: float,
    feed_rate_mm_min: float,
    plunge_rate_mm_min: float,
    safe_z_mm: float,
    retract_z_mm: float,
    contour_point_count: int,
    tab_count: int,
    tab_height_mm: float,
    use_tabs: bool,
    finishing_pass: bool,
    finishing_allowance_mm: float,
) -> ProfileFeasibilityResult:
    """
    Compute feasibility for a profile operation.

    Validates:
    - Tool diameter bounds
    - Cut depth vs stepdown coherence
    - Feed/plunge rate bounds
    - Safe/retract Z above material
    - Tab configuration coherence
    - Estimated pass count reasonableness

    Args:
        tool_diameter_mm: Tool diameter
        cut_depth_mm: Total cut depth
        stepdown_mm: Depth per pass
        feed_rate_mm_min: XY feed rate
        plunge_rate_mm_min: Z plunge rate
        safe_z_mm: Safe Z height
        retract_z_mm: Retract Z height
        contour_point_count: Number of points in contour
        tab_count: Number of tabs
        tab_height_mm: Tab height
        use_tabs: Whether tabs are enabled
        finishing_pass: Whether finishing pass is enabled
        finishing_allowance_mm: Finishing allowance

    Returns:
        ProfileFeasibilityResult with feasibility status and issues
    """
    issues: List[str] = []
    warnings: List[str] = []

    # Tool diameter validation
    if tool_diameter_mm <= 0:
        issues.append("tool_diameter_mm must be > 0")
    elif tool_diameter_mm < 1.0:
        warnings.append(f"tool_diameter_mm={tool_diameter_mm}mm is very small")
    elif tool_diameter_mm > 25.0:
        warnings.append(f"tool_diameter_mm={tool_diameter_mm}mm is unusually large for profiling")

    # Cut depth validation
    if cut_depth_mm <= 0:
        issues.append("cut_depth_mm must be > 0")
    elif cut_depth_mm > 50.0:
        warnings.append(f"cut_depth_mm={cut_depth_mm}mm is deep - verify tool flute length")

    # Stepdown validation
    if stepdown_mm <= 0:
        issues.append("stepdown_mm must be > 0")
    elif stepdown_mm > cut_depth_mm:
        warnings.append("stepdown_mm > cut_depth_mm; will use single pass")
    elif stepdown_mm > tool_diameter_mm:
        warnings.append(f"stepdown_mm={stepdown_mm}mm exceeds tool diameter - aggressive cut")

    # Feed rate validation
    if feed_rate_mm_min <= 0:
        issues.append("feed_rate_mm_min must be > 0")
    elif feed_rate_mm_min < 100:
        warnings.append("feed_rate_mm_min < 100 is very slow")
    elif feed_rate_mm_min > 5000:
        warnings.append(f"feed_rate_mm_min={feed_rate_mm_min} is aggressive for profiling")

    # Plunge rate validation
    if plunge_rate_mm_min <= 0:
        issues.append("plunge_rate_mm_min must be > 0")
    elif plunge_rate_mm_min > feed_rate_mm_min:
        warnings.append("plunge_rate exceeds feed_rate - unusual configuration")

    # Z heights validation
    if safe_z_mm <= 0:
        issues.append("safe_z_mm must be > 0")
    if retract_z_mm <= 0:
        issues.append("retract_z_mm must be > 0")
    if retract_z_mm > safe_z_mm:
        warnings.append("retract_z_mm > safe_z_mm - will use safe_z for both")

    # Contour validation
    if contour_point_count < 3:
        issues.append("contour must have at least 3 points")

    # Tab validation
    if use_tabs:
        if tab_count < 1:
            issues.append("tab_count must be >= 1 when use_tabs is True")
        if tab_height_mm <= 0:
            issues.append("tab_height_mm must be > 0 when use_tabs is True")
        if tab_height_mm >= cut_depth_mm:
            issues.append("tab_height_mm must be < cut_depth_mm")

    # Finishing validation
    if finishing_pass:
        if finishing_allowance_mm < 0:
            issues.append("finishing_allowance_mm must be >= 0")
        elif finishing_allowance_mm > tool_diameter_mm / 2:
            warnings.append("finishing_allowance exceeds tool radius")

    # Calculate estimated pass count
    if stepdown_mm > 0:
        effective_depth = cut_depth_mm - (tab_height_mm if use_tabs else 0)
        pass_count = max(1, int((effective_depth + stepdown_mm - 0.001) / stepdown_mm))
        if finishing_pass:
            pass_count += 1
    else:
        pass_count = 1

    if pass_count > 50:
        warnings.append(f"Estimated {pass_count} passes - consider larger stepdown")

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
        "estimated_pass_count": pass_count,
        "effective_depth_mm": cut_depth_mm - (tab_height_mm if use_tabs else 0),
        "tool_diameter_mm": tool_diameter_mm,
        "tab_count": tab_count if use_tabs else 0,
    }

    return ProfileFeasibilityResult(
        feasible=feasible,
        risk_level=risk_level,
        issues=issues,
        warnings=warnings,
        summary=summary,
    )


def hash_feasibility_result(result: ProfileFeasibilityResult) -> str:
    """Generate SHA256 hash of feasibility result for provenance."""
    data = json.dumps(result.to_dict(), sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()
