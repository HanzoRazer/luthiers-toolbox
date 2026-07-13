# services/api/app/cam/project_adapter.py
"""
Project Spine -> CAM request translation (SPINE-003).

Translates validated canonical project state (`InstrumentProjectData`, ADR-002) into
the EXISTING adaptive-clearing CAM request model (`PlanIn`). This is the single,
canonical Project -> CAM translation point.

Boundary (ADR-002 + the SPINE-003 Dev Order):
    - CAM keeps its computational authority; RMOS keeps its manufacturing authority.
      This module performs NO CAM execution, NO feasibility evaluation, and NO
      persistence. It only builds a request object.
    - The Project Spine owns canonical geometry/spec. The only geometry consumed here
      is the project's canonical body outline (`blueprint_geometry.body_outline_mm`),
      mapped onto `PlanIn.loops`. No geometry is generated or invented.
    - Machining parameters (tool diameter, feeds, stepover, ...) are NOT design state;
      they are supplied by the caller and passed through unchanged. `PlanIn`'s own field
      defaults remain the single source of truth for any parameter the caller omits.

Translation happens exactly once, in `build_cam_request_from_project`. Duplicate
translation logic is prohibited (SPINE-003 "Canonical Translation").
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from ..schemas.adaptive_schemas import Loop, PlanIn
from ..schemas.instrument_project import InstrumentProjectData

# Machining parameters a caller may override; all are existing PlanIn fields. Anything
# omitted keeps its PlanIn default (single source of truth — no default duplication here).
ALLOWED_MACHINING_OVERRIDES = frozenset(
    {
        "units",
        "stepover",
        "stepdown",
        "margin",
        "strategy",
        "smoothing",
        "climb",
        "feed_xy",
        "safe_z",
        "z_rough",
    }
)


def validate_project_cam_inputs(project_data: InstrumentProjectData) -> None:
    """
    Validate that the project carries the geometry this CAM operation requires.

    CAM-operation-specific precondition only (project-level readiness is checked upstream
    by ``projects.service.load_project_for_cam``). Raises ``ValueError`` on a missing or
    malformed precondition — never fabricates geometry.

    Requires ``blueprint_geometry.body_outline_mm`` to be a closed boundary of at least
    three finite (x, y) points.
    """
    if project_data is None:
        raise ValueError("No project design state to build a CAM request from.")

    geometry = project_data.blueprint_geometry
    if geometry is None or not geometry.body_outline_mm:
        raise ValueError(
            "Project has no body_outline_mm geometry; import a blueprint before CAM execution."
        )

    outline = geometry.body_outline_mm
    if len(outline) < 3:
        raise ValueError(
            "body_outline_mm must have at least 3 points to form a closed boundary."
        )

    for point in outline:
        if len(point) != 2:
            raise ValueError("Each body_outline_mm point must be an (x, y) pair.")
        x, y = point
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("body_outline_mm contains non-finite coordinates.")


def build_cam_request_from_project(
    project_data: InstrumentProjectData,
    *,
    tool_d: float,
    overrides: Optional[Dict[str, Any]] = None,
) -> PlanIn:
    """
    Build the existing adaptive-clearing ``PlanIn`` request from canonical project state.

    The outer boundary loop is the project's canonical body outline
    (``blueprint_geometry.body_outline_mm``). ``tool_d`` and any ``overrides`` are
    caller-supplied machining parameters (not design state); overrides are restricted to
    known ``PlanIn`` machining fields and any omitted field keeps its ``PlanIn`` default.

    Read-only against project state; performs no execution or persistence.
    """
    validate_project_cam_inputs(project_data)

    applied = dict(overrides or {})
    unknown = set(applied) - ALLOWED_MACHINING_OVERRIDES
    if unknown:
        raise ValueError(
            f"Unsupported machining override(s): {sorted(unknown)}. "
            f"Allowed: {sorted(ALLOWED_MACHINING_OVERRIDES)}."
        )

    outline = project_data.blueprint_geometry.body_outline_mm
    boundary = Loop(pts=[(float(x), float(y)) for (x, y) in outline])

    return PlanIn(loops=[boundary], tool_d=tool_d, **applied)
