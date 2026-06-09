"""
Pocketing Feasibility Check

Geometric + parameter feasibility for adaptive pocket-clearing (Dev Order 8J).
Uses shapely for polygon validity, island containment, and overlap checks.
Observational: warns or blocks; never mutates intent.

Reconstructed from preserved bytecode.
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
    return [(float(x), float(y)) for x, y in points]


def _validate_polygon_geometry(coords: List[Tuple[float, float]], name: str) -> Tuple[bool, str]:
    """Validate a coordinate ring forms a valid, non-empty polygon."""
    if len(coords) < 3:
        return False, f"{name} must have at least 3 points"
    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            return False, f"{name} is not a valid polygon: {explain_validity(poly)}"
        if poly.is_empty:
            return False, f"{name} is empty"
    except Exception as e:  # pragma: no cover - shapely defensive
        return False, f"{name} geometry error: {e}"
    return True, ""


def _validate_island_within_boundary(
    boundary_coords: List[Tuple[float, float]],
    island_coords: List[Tuple[float, float]],
    island_index: int,
) -> Tuple[bool, str]:
    """Validate an island lies within the pocket boundary."""
    try:
        boundary = Polygon(boundary_coords)
        island = Polygon(island_coords)
        if not boundary.contains(island):
            if boundary.intersects(island):
                return False, f"island {island_index} extends outside boundary"
            return False, f"island {island_index} is not within boundary"
    except Exception as e:  # pragma: no cover
        return False, f"island {island_index} containment check failed: {e}"
    return True, ""


def _validate_islands_non_overlapping(
    islands_coords: List[List[Tuple[float, float]]],
) -> Tuple[bool, str]:
    """Validate islands do not overlap each other."""
    try:
        polys = [Polygon(c) for c in islands_coords]
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                if polys[i].intersects(polys[j]) and polys[i].intersection(polys[j]).area > 0:
                    return False, f"islands {i} and {j} overlap"
    except Exception as e:  # pragma: no cover
        return False, f"island overlap check failed: {e}"
    return True, ""


def compute_pocket_area(
    boundary: List[Tuple[float, float]],
    islands: List[List[Tuple[float, float]]],
) -> float:
    """Net pocket area = boundary area minus island areas."""
    return Polygon(boundary).area - sum(Polygon(c).area for c in islands)


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
    """Compute feasibility for an adaptive pocket-clearing operation."""
    issues: List[str] = []
    warnings: List[str] = []

    # Boundary geometry
    ok, msg = _validate_polygon_geometry(boundary, "boundary")
    if not ok:
        issues.append(msg)

    # Island geometry, containment, overlap
    for i, isl in enumerate(islands):
        ok, msg = _validate_polygon_geometry(isl, f"island {i}")
        if not ok:
            issues.append(msg)
        else:
            ok, msg = _validate_island_within_boundary(boundary, isl, i)
            if not ok:
                issues.append(msg)
    if len(islands) > 1:
        ok, msg = _validate_islands_non_overlapping(islands)
        if not ok:
            issues.append(msg)

    # Tool diameter (L.1 bounds)
    if tool_diameter_mm <= 0:
        issues.append("tool_diameter_mm must be > 0")
    elif tool_diameter_mm < 0.5:
        issues.append(f"tool_diameter_mm={tool_diameter_mm}mm below L.1 minimum (0.5mm)")
    elif tool_diameter_mm > 50.0:
        issues.append(f"tool_diameter_mm={tool_diameter_mm}mm above L.1 maximum (50mm)")

    # Stepover (L.1 bounds)
    if stepover_percent < 30.0:
        issues.append(f"stepover_percent={stepover_percent}% below L.1 minimum (30%)")
    elif stepover_percent > 70.0:
        issues.append(f"stepover_percent={stepover_percent}% above L.1 maximum (70%)")
    elif stepover_percent > 60.0:
        warnings.append(f"stepover_percent={stepover_percent}% is aggressive - may leave scallops")

    # Pocket depth
    if pocket_depth_mm <= 0:
        issues.append("pocket_depth_mm must be > 0")
    elif pocket_depth_mm > 50.0:
        warnings.append(f"pocket_depth_mm={pocket_depth_mm}mm is very deep")

    # Stepdown
    if stepdown_mm <= 0:
        issues.append("stepdown_mm must be > 0")
    elif stepdown_mm > tool_diameter_mm:
        warnings.append(f"stepdown_mm={stepdown_mm}mm exceeds tool diameter - aggressive")

    # Feed / plunge
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

    # Finishing
    if finish_allowance_mm < 0:
        issues.append("finish_allowance_mm must be >= 0")
    elif finish_allowance_mm > tool_diameter_mm / 2.0:
        warnings.append("finish_allowance exceeds tool radius")

    # Deep-pocket ratio
    if tool_diameter_mm > 0 and pocket_depth_mm > 0:
        ratio = pocket_depth_mm / tool_diameter_mm
        if ratio > 10:
            warnings.append(
                f"Deep pocket: depth/diameter ratio is {ratio:.1f}. "
                "Verify tool flute length and chip evacuation."
            )

    # Pass count
    if stepdown_mm > 0 and pocket_depth_mm > 0:
        pass_count = max(1, int((pocket_depth_mm + stepdown_mm - 0.001) / stepdown_mm))
    else:
        pass_count = 1
    if pass_count > 50:
        warnings.append(f"Estimated {pass_count} passes - consider larger stepdown")

    # Area (best-effort; only if geometry valid)
    try:
        area = compute_pocket_area(boundary, islands)
    except Exception:  # pragma: no cover
        area = 0.0

    # Risk
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
        "pocket_area_mm2": round(area, 2),
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
