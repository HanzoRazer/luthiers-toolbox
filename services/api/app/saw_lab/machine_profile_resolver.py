from __future__ import annotations

from typing import Any, Dict, Optional


def resolve_machine_profile_constraints(
    *,
    machine_profile_artifact_id: str,
) -> Dict[str, Any]:
    """
    Reads a machine profile artifact and returns validation constraints:
      - safe_z_mm
      - bounds_mm {min_x,max_x,min_y,max_y,min_z,max_z}

    Expected artifact payload shape (best-effort):
      payload.safe_z_mm: float
      payload.bounds_mm: dict

    Returns {} if not found or malformed.
    """
    if not machine_profile_artifact_id:
        return {}

    from app.rmos.runs_v2 import store as runs_store

    art = runs_store.get_run(machine_profile_artifact_id)
    if not isinstance(art, dict):
        return {}

    payload = art.get("payload") or art.get("data") or {}
    if not isinstance(payload, dict):
        return {}

    out: Dict[str, Any] = {}
    safe = payload.get("safe_z_mm")
    if isinstance(safe, (int, float)):
        out["safe_z_mm"] = float(safe)

    b = payload.get("bounds_mm")
    if isinstance(b, dict):
        bounds: Dict[str, float] = {}
        for k in ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z"):
            v = b.get(k)
            if isinstance(v, (int, float)):
                bounds[k] = float(v)
        if bounds:
            out["bounds_mm"] = bounds

    return out
