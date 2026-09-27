"""Pure helpers for containing the Rosette ``/export-cnc`` manufacturing emitter.

Extracted from ``rosette_cam_router.py`` under the CF2 order's file-size
governance allowance (keep utilities local unless the file-size ratchet requires
a narrow extraction). Nothing here persists, calls the evaluator, builds a
response, or calls a generator.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import Response

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
        "material_id": str(payload.get("material", "hardwood")).lower(),
        "rpm": int(payload.get("spindle_rpm", 12000)),
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
