"""
Pocketing Feasibility Check

Feasibility validation for pocketing operations.
Part of the OPERATION lane requirements (8J).

This implements the four geometric validity checks required by 8J:
1. Boundary is a valid simple polygon (non-self-intersecting)
2. Each island is a valid simple polygon
3. Each island lies fully within the boundary
4. Islands do not overlap each other

All four are BLOCKING issues, not warnings.

Additional checks:
- Tool diameter sanity
- Stepover in L.1 range
- Safe/retract Z above material
- Deep pocket/tool ratio warnings
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from shapely.geometry import Polygon
from shapely.validation import explain_validity


@dataclass
class PocketFeasibilityResult:
    """Result of pocketing feasibility check."""

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


def _points_to_coords(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Convert point list to coordinate tuples for Shapely."""
    return [(p[0], p[1]) for p in points]


def _validate_polygon_geometry(
    coords: List[Tuple[float, float]],
    name: str,
) -> Tuple[bool, str]:
    """
    Validate that coordinates form a valid simple polygon.

    Uses Shapely's is_valid which checks:
    - Non-self-intersecting
    - Properly closed
    - No duplicate consecutive points
    - No ring self-touches

    Args:
        coords: List of (x, y) coordinate tuples
        name: Name for error messages (e.g., "boundary", "island 0")

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(coords) < 3:
        return False, f"{name} must have at least 3 points"

    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            reason = explain_validity(poly)
            return False, f"{name} is not a valid polygon: {reason}"
        if poly.is_empty:
            return False, f"{name} is empty"
        return True, ""
    except Exception as e:
        return False, f"{name} geometry error: {str(e)}"


def _validate_island_within_boundary(
    boundary_coords: List[Tuple[float, float]],
    island_coords: List[Tuple[float, float]],
    island_index: int,
) -> Tuple[bool, str]:
    """
    Validate that an island lies fully within the boundary.

    Args:
        boundary_coords: Boundary polygon coordinates
        island_coords: Island polygon coordinates
        island_index: Index for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        boundary_poly = Polygon(boundary_coords)
        island_poly = Polygon(island_coords)

        if not boundary_poly.contains(island_poly):
            if boundary_poly.intersects(island_poly) and not boundary_poly.contains(island_poly):
                return False, f"island {island_index} extends outside boundary"
            else:
                return False, f"island {island_index} is not within boundary"
        return True, ""
    except Exception as e:
        return False, f"island {island_index} containment check failed: {str(e)}"


def _validate_islands_non_overlapping(
    islands_coords: List[List[Tuple[float, float]]],
) -> Tuple[bool, str]:
    """
    Validate that no two islands overlap each other.

    Args:
        islands_coords: List of island coordinate lists

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(islands_coords) < 2:
        return True, ""

    try:
        island_polys = [Polygon(coords) for coords in islands_coords]

        for i in range(len(island_polys)):
            for j in range(i + 1, len(island_polys)):
                if island_polys[i].intersects(island_polys[j]):
                    # Check if it's more than just touching at a point
                    intersection = island_polys[i].intersection(island_polys[j])
                    if intersection.area > 0:
                        return False, f"islands {i} and {j} overlap"
        return True, ""
    except Exception as e:
        return False, f"island overlap check failed: {str(e)}"


def compute_pocket_area(
    boundary_coords: List[Tuple[float, float]],
    islands_coords: List[List[Tuple[float, float]]],
) -> float:
    """
    Compute pocket area (boundary area minus island areas).

    MUST only be called after geometric validity passes.
    Invalid polygons produce meaningless area values.

    Args:
        boundary_coords: Validated boundary coordinates
        islands_coords: Validated island coordinate lists

    Returns:
        Pocket area in mm²
    """
    boundary_poly = Polygon(boundary_coords)
    boundary_area = boundary_poly.area

    island_area = sum(Polygon(coords).area for coords in islands_coords)

    return boundary_area - island_area


def compute_pocket_feasibility(
    *,
    boundary: List[Tuple[float, float]],
    islands: List[List[Tuple[float, float]]],
    pocket_depth_mm: float,
    tool_diameter_mm: float,
    stepover_percent: float,
    feed_rate_mm_min: float,
    plunge_rate_mm_min: float,
    safe_z_mm: float,
    retract_z_mm: float,
    stepdown_mm: float,
    finish_allowance_mm: float,
) -> PocketFeasibilityResult:
    """
    Compute feasibility for a pocketing operation.

    Validates (BLOCKING - any failure blocks):
    - Boundary is a valid simple polygon
    - Each island is a valid simple polygon
    - Each island lies within boundary
    - Islands do not overlap

    Validates (parameters):
    - Tool diameter in L.1 range
    - Stepover in L.1 range
    - Safe/retract Z positive
    - Pocket depth > 0
    - Stepdown > 0

    Warns (non-blocking):
    - Deep pocket/tool ratio
    - Aggressive stepover
    - Small internal radii

    Args:
        boundary: Boundary polygon as (x, y) tuples
        islands: List of island polygons
        pocket_depth_mm: Total pocket depth
        tool_diameter_mm: Tool diameter
        stepover_percent: Stepover as percentage
        feed_rate_mm_min: XY feed rate
        plunge_rate_mm_min: Z plunge rate
        safe_z_mm: Safe travel height
        retract_z_mm: Retract height
        stepdown_mm: Depth per pass
        finish_allowance_mm: Material for finishing

    Returns:
        PocketFeasibilityResult with feasibility status and issues
    """
    issues: List[str] = []
    warnings: List[str] = []

    # =========================================================================
    # GEOMETRIC VALIDITY CHECKS (all blocking)
    # =========================================================================

    # Check 1: Boundary is valid simple polygon
    valid, error = _validate_polygon_geometry(boundary, "boundary")
    if not valid:
        issues.append(error)

    # Check 2: Each island is valid simple polygon
    for i, island in enumerate(islands):
        valid, error = _validate_polygon_geometry(island, f"island {i}")
        if not valid:
            issues.append(error)

    # Only proceed with containment/overlap checks if base geometry is valid
    if not issues:
        # Check 3: Each island within boundary
        for i, island in enumerate(islands):
            valid, error = _validate_island_within_boundary(boundary, island, i)
            if not valid:
                issues.append(error)

        # Check 4: Islands non-overlapping
        valid, error = _validate_islands_non_overlapping(islands)
        if not valid:
            issues.append(error)

    # =========================================================================
    # PARAMETER VALIDATION
    # =========================================================================

    # Tool diameter (L.1 range: 0.5-50mm)
    if tool_diameter_mm <= 0:
        issues.append("tool_diameter_mm must be > 0")
    elif tool_diameter_mm < 0.5:
        issues.append(f"tool_diameter_mm={tool_diameter_mm}mm below L.1 minimum (0.5mm)")
    elif tool_diameter_mm > 50.0:
        issues.append(f"tool_diameter_mm={tool_diameter_mm}mm above L.1 maximum (50mm)")

    # Stepover (L.1 range: 30-70%)
    stepover_fraction = stepover_percent / 100.0
    if stepover_fraction < 0.3:
        issues.append(f"stepover_percent={stepover_percent}% below L.1 minimum (30%)")
    elif stepover_fraction > 0.7:
        issues.append(f"stepover_percent={stepover_percent}% above L.1 maximum (70%)")
    elif stepover_fraction > 0.6:
        warnings.append(f"stepover_percent={stepover_percent}% is aggressive - may leave scallops")

    # Pocket depth
    if pocket_depth_mm <= 0:
        issues.append("pocket_depth_mm must be > 0")
    elif pocket_depth_mm > 75.0:
        warnings.append(f"pocket_depth_mm={pocket_depth_mm}mm is very deep")

    # Stepdown
    if stepdown_mm <= 0:
        issues.append("stepdown_mm must be > 0")
    elif stepdown_mm > tool_diameter_mm:
        warnings.append(f"stepdown_mm={stepdown_mm}mm exceeds tool diameter - aggressive")

    # Feed rates
    if feed_rate_mm_min <= 0:
        issues.append("feed_rate_mm_min must be > 0")
    if plunge_rate_mm_min <= 0:
        issues.append("plunge_rate_mm_min must be > 0")
    elif plunge_rate_mm_min > feed_rate_mm_min:
        warnings.append("plunge_rate exceeds feed_rate - unusual")

    # Z heights
    if safe_z_mm <= 0:
        issues.append("safe_z_mm must be > 0")
    if retract_z_mm <= 0:
        issues.append("retract_z_mm must be > 0")
    if retract_z_mm > safe_z_mm:
        warnings.append("retract_z_mm > safe_z_mm - will use safe_z")

    # Finish allowance
    if finish_allowance_mm < 0:
        issues.append("finish_allowance_mm must be >= 0")
    elif finish_allowance_mm > tool_diameter_mm / 2:
        warnings.append("finish_allowance exceeds tool radius")

    # =========================================================================
    # DERIVED WARNINGS
    # =========================================================================

    # Deep pocket ratio
    if tool_diameter_mm > 0 and pocket_depth_mm > 0:
        depth_ratio = pocket_depth_mm / tool_diameter_mm
        if depth_ratio > 3:
            warnings.append(
                f"Deep pocket: depth/diameter ratio is {depth_ratio:.1f}. "
                "Verify tool flute length and chip evacuation."
            )

    # Calculate pass count
    if stepdown_mm > 0:
        pass_count = max(1, int((pocket_depth_mm + stepdown_mm - 0.001) / stepdown_mm))
        if pass_count > 30:
            warnings.append(f"Estimated {pass_count} passes - consider larger stepdown")
    else:
        pass_count = 1

    # =========================================================================
    # COMPUTE SUMMARY (only if geometry valid)
    # =========================================================================

    if not issues:
        pocket_area = compute_pocket_area(boundary, islands)
    else:
        pocket_area = 0.0

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
        "pocket_area_mm2": round(pocket_area, 2),
        "island_count": len(islands),
        "estimated_pass_count": pass_count,
        "tool_diameter_mm": tool_diameter_mm,
        "stepover_percent": stepover_percent,
        "pocket_depth_mm": pocket_depth_mm,
    }

    return PocketFeasibilityResult(
        feasible=feasible,
        risk_level=risk_level,
        issues=issues,
        warnings=warnings,
        summary=summary,
    )


def hash_feasibility_result(result: PocketFeasibilityResult) -> str:
    """Generate SHA256 hash of feasibility result for provenance."""
    data = json.dumps(result.to_dict(), sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()
