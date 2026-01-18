from __future__ import annotations

from typing import Any, Dict, Optional


def write_toolpaths_lint_report_artifact(
    *,
    toolpaths_artifact_id: str,
    session_id: Optional[str],
    batch_label: Optional[str],
    tool_kind: str = "saw",
    machine_profile_artifact_id: Optional[str] = None,
    safe_z_mm: float = 5.0,
    bounds_mm: Optional[Dict[str, float]] = None,
    require_units_mm: bool = True,
    require_absolute: bool = True,
    require_xy_plane: bool = False,
    require_spindle_on: bool = True,
    require_feed_on_cut: bool = True,
) -> Dict[str, Any]:
    """
    Validates toolpaths and persists a governed lint report artifact.

    Returns:
      {
        "lint_artifact_id": str,
        "result": { ok, errors, warnings, summary }
      }
    """
    from .toolpaths_validate_service import validate_toolpaths_artifact_static

    result = validate_toolpaths_artifact_static(
        toolpaths_artifact_id=toolpaths_artifact_id,
        safe_z_mm=safe_z_mm,
        bounds_mm=bounds_mm,
        require_units_mm=require_units_mm,
        require_absolute=require_absolute,
        require_xy_plane=require_xy_plane,
        require_spindle_on=require_spindle_on,
        require_feed_on_cut=require_feed_on_cut,
    )

    payload: Dict[str, Any] = {
        "toolpaths_artifact_id": toolpaths_artifact_id,
        "machine_profile_artifact_id": machine_profile_artifact_id,
        "result": result,
    }

    from app.rmos.runs_v2.store import store_artifact

    lint_id = store_artifact(
        kind="saw_toolpaths_lint_report",
        payload=payload,
        parent_id=toolpaths_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    return {"lint_artifact_id": lint_id, "result": result}
