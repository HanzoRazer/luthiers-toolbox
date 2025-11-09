"""CAM Simulation Bridge

Normalizes outputs from different CAM simulation engines into a unified format.
Part of Art Studio v16.1 integration.
"""

from typing import Dict, Any, List

from app.schemas.cam_sim import SimIssue, SimIssuesSummary


def _extract_issues_from_raw(raw: Dict[str, Any]) -> List[SimIssue]:
    """
    Try to interpret whatever the sim engine gave us into a list[SimIssue].
    This keeps the pipeline + UI decoupled from engine-specific formats.
    """
    issues: List[SimIssue] = []

    # Preferred: raw["issues"] is already close to the schema
    raw_issues = raw.get("issues")
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, dict):
                continue
            try:
                issues.append(SimIssue(**item))
            except Exception:
                continue

    # Alternate: raw["collisions"]
    collisions = raw.get("collisions")
    if isinstance(collisions, list):
        for c in collisions:
            if not isinstance(c, dict):
                continue
            try:
                issues.append(
                    SimIssue(
                        type=c.get("type", "collision"),
                        x=float(c.get("x", 0.0)),
                        y=float(c.get("y", 0.0)),
                        z=c.get("z"),
                        severity=c.get("severity", "high"),
                        note=c.get("note", "Collision detected"),
                    )
                )
            except Exception:
                continue

    # Alternate: raw["gouges"]
    gouges = raw.get("gouges")
    if isinstance(gouges, list):
        for g in gouges:
            if not isinstance(g, dict):
                continue
            try:
                issues.append(
                    SimIssue(
                        type=g.get("type", "gouge"),
                        x=float(g.get("x", 0.0)),
                        y=float(g.get("y", 0.0)),
                        z=g.get("z"),
                        severity=g.get("severity", "medium"),
                        note=g.get("note", "Gouge detected"),
                    )
                )
            except Exception:
                continue

    return issues


def simulate_gcode_inline(
    gcode: str,
    stock_thickness: float | None = None,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Inline sim call used by the pipeline.

    Always returns a dict matching SimIssuesSummary, plus the raw engine payload.
    
    NOTE: This is a stub implementation. Wire to your actual sim engine.
    """
    # Stub implementation - replace with actual sim engine call
    raw_out = {
        "ok": True,
        "issues": [],
        "stats": {
            "time_s": len(gcode) * 0.0001,  # Trivial estimate
            "move_count": len([l for l in gcode.split('\n') if l.strip()])
        }
    }

    issues = _extract_issues_from_raw(raw_out)

    summary = SimIssuesSummary(
        ok=bool(raw_out.get("ok", True)),
        gcode_bytes=len(gcode.encode("utf-8")),
        stock_thickness=stock_thickness,
        issues=issues,
        stats=raw_out.get("stats") or {},
        meta={
            k: v
            for k, v in raw_out.items()
            if k not in ("issues", "collisions", "gouges", "stats")
        },
    )

    out: Dict[str, Any] = summary.model_dump()
    out["raw"] = raw_out
    return out
