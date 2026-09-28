"""Pure helpers for containing the Rosette manufacturing emitters.

Covers the ``/export-cnc`` single-ring route and the ``/design`` multi-ring
route. Extracted from ``rosette_cam_router.py`` under the CF2 order's file-size
governance allowance (keep utilities local unless the file-size ratchet requires
a narrow extraction). Nothing here persists, calls the evaluator, builds a
response, or calls a generator.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from fastapi import Response

from ..cam.rosette.cnc import MaterialType
from ..cam.rosette.models import RosetteRingConfig
from .manufacturing_output_authority import ManufacturingAuthorityContext

# Capability key for the rosette manufacturing-output authority. The tool_id is
# passed as a string literal at the route call site (``rosette:export_cnc``) so
# the static inventory classifier can render it as the row's authority_key. It
# carries the ``rosette:`` prefix because the feasibility dispatcher resolves the
# substantive rosette evaluator by that prefix (mirroring the profiling route's
# ``profiling:gcode``); a bare ``rosette`` resolves to mode "unknown" and could
# never reach compute_rosette_feasibility.
ROSETTE_MODE = "rosette"

_ROSETTE_MATERIALS = {
    "hardwood": MaterialType.HARDWOOD,
    "softwood": MaterialType.SOFTWOOD,
    "composite": MaterialType.COMPOSITE,
}


def _canonical_rosette_material(value: Any) -> tuple[str, MaterialType]:
    """Return the material id and enum that Rosette generation will use.

    Preserve the routes' established fallback: missing, blank, or unsupported
    material values generate as hardwood. Returning both representations from
    one function keeps authority summaries and CNC generation identical.
    """
    requested = str(value or "hardwood").strip().lower()
    canonical = requested if requested in _ROSETTE_MATERIALS else "hardwood"
    return canonical, _ROSETTE_MATERIALS[canonical]


def _rosette_ring_feasibility_summary(
    ring: RosetteRingConfig, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Derive the single-ring feasibility summary from normalized ring geometry.

    Pure: no persistence, evaluator call, response, or generator call. Returns a
    JSON-safe mapping accepted by ``require_manufacturing_output_authority``.
    ``pattern_type`` is deliberately omitted (the export request carries no
    pattern and the generator uses none); ``tool_id`` is omitted because the
    shared authority service adds it. Raises ``ValueError`` for impossible
    geometry so the evaluator's silent defaults cannot substitute plausible
    values.
    """
    outer_radius_mm = ring.radius_mm + ring.width_mm / 2.0
    inner_radius_mm = ring.radius_mm - ring.width_mm / 2.0
    outer_diameter_mm = 2.0 * outer_radius_mm
    inner_diameter_mm = 2.0 * inner_radius_mm

    if ring.width_mm <= 0:
        raise ValueError(f"ring width must be positive, got {ring.width_mm}")
    if inner_radius_mm <= 0:
        raise ValueError(
            f"inner radius must be positive, got {inner_radius_mm} "
            f"(radius {ring.radius_mm}, width {ring.width_mm})"
        )
    if outer_diameter_mm <= inner_diameter_mm:
        raise ValueError(
            f"outer diameter {outer_diameter_mm} must exceed inner diameter {inner_diameter_mm}"
        )

    return {
        "outer_diameter_mm": outer_diameter_mm,
        "inner_diameter_mm": inner_diameter_mm,
        "ring_count": 1,
        "material_id": _canonical_rosette_material(payload.get("material"))[0],
        "rpm": int(payload.get("spindle_rpm", 12000)),
    }


def _rosette_design_feasibility_summary(
    ring_dicts: List[Dict[str, Any]], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Derive one complete-design feasibility summary from normalized rings.

    Pure: no persistence, evaluator call, response, or generator call. Aggregates
    every ring so the single authority request represents the whole design, not
    ring 1. ``outer_diameter_mm`` is the outermost outer edge and
    ``inner_diameter_mm`` the innermost inner edge across all rings; taking the
    max outer and min inner is conservative for the scorer (it maximizes the
    modeled channel width and perimeter, so it cannot under-report risk).

    ``material_id`` and ``rpm`` are the route-level values generation actually
    uses (the generator applies one material and one post RPM to every ring).

    ``pattern_type`` is truthful: the single normalized pattern when uniform,
    else ``"mixed"``; ``pattern_types`` lists the sorted unique normalized
    patterns as diagnostics. NOTE: pattern affects the emitted program only via
    tile-count parity; the manufacturing-output evaluator does not currently
    consume ``pattern_type`` for its risk decision (authority is based on
    geometry, ring count, material, and RPM). Closing evaluator pattern-awareness
    is separate future work.

    Raises ``ValueError`` for invalid geometry so the evaluator's silent defaults
    cannot substitute plausible values.
    """
    if not ring_dicts:
        raise ValueError("design has no rings")

    outer_diameters: List[float] = []
    inner_diameters: List[float] = []
    patterns: List[str] = []
    for r in ring_dicts:
        radius_mm = float(r["radius_mm"])
        width_mm = float(r["width_mm"])
        if not (math.isfinite(radius_mm) and math.isfinite(width_mm)):
            raise ValueError(
                f"non-finite ring geometry: radius={radius_mm}, width={width_mm}"
            )
        if width_mm <= 0:
            raise ValueError(f"ring width must be positive, got {width_mm}")
        inner_radius_mm = radius_mm - width_mm / 2.0
        if inner_radius_mm <= 0:
            raise ValueError(
                f"inner radius must be positive, got {inner_radius_mm} "
                f"(radius {radius_mm}, width {width_mm})"
            )
        outer_diameters.append(2.0 * (radius_mm + width_mm / 2.0))
        inner_diameters.append(2.0 * inner_radius_mm)
        patterns.append(str(r.get("pattern", "checkerboard")).lower())

    outer_diameter_mm = max(outer_diameters)
    inner_diameter_mm = min(inner_diameters)
    if not (math.isfinite(outer_diameter_mm) and math.isfinite(inner_diameter_mm)):
        raise ValueError("non-finite derived diameters")
    if outer_diameter_mm <= inner_diameter_mm:
        raise ValueError(
            f"outer diameter {outer_diameter_mm} must exceed inner diameter {inner_diameter_mm}"
        )

    unique_patterns = sorted(set(patterns))
    pattern_type = unique_patterns[0] if len(unique_patterns) == 1 else "mixed"

    return {
        "outer_diameter_mm": outer_diameter_mm,
        "inner_diameter_mm": inner_diameter_mm,
        "ring_count": len(ring_dicts),
        "material_id": _canonical_rosette_material(payload.get("material"))[0],
        "rpm": int(payload.get("spindle_rpm", 12000)),
        "pattern_type": pattern_type,
        "pattern_types": unique_patterns,
    }


def _set_governed_output_headers(
    response: Response, authority: ManufacturingAuthorityContext, gcode_hash: str
) -> None:
    """Stamp the governed success headers onto the FastAPI response.

    Requires ``gcode_hash`` (returned by ``persist_authorized_manufacturing_output``)
    so it cannot be used before the program is persisted.
    """
    response.headers["X-Run-ID"] = authority.run_id
    response.headers["X-ToolBox-Lane"] = "governed"
    response.headers["X-GCode-SHA256"] = gcode_hash
