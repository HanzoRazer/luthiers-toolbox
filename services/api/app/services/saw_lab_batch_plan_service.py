"""
Saw Lab Batch Plan Service

Generates a batch plan from a spec artifact, grouping items into setups
and computing feasibility for each operation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x


def create_batch_plan(*, batch_spec_artifact_id: str) -> Dict[str, Any]:
    """
    Generate a batch plan from a spec artifact.

    Groups items by material/tool into setups and computes feasibility for each op.

    Args:
        batch_spec_artifact_id: The spec artifact to plan from

    Returns:
        Dict with batch_plan_artifact_id, setups, and metadata
    """
    from app.rmos.run_artifacts.store import read_run_artifact, write_run_artifact
    from app.saw_lab import SawLabService

    svc = SawLabService()

    # Read the spec
    spec = read_run_artifact(batch_spec_artifact_id)
    spec_payload = spec.get("payload") or {}
    spec_meta = spec.get("index_meta") or {}

    batch_label = spec_meta.get("batch_label") or spec_payload.get("batch_label")
    session_id = spec_meta.get("session_id") or spec_payload.get("session_id")
    tool_id = spec_payload.get("tool_id") or "saw:thin_140"
    items = spec_payload.get("items") or []

    # Group items by material_id into setups
    setups_by_material: Dict[str, Dict[str, Any]] = {}

    for item in items:
        material_id = item.get("material_id") or "unknown"
        setup_key = f"setup_{material_id}"

        if setup_key not in setups_by_material:
            setups_by_material[setup_key] = {
                "setup_key": setup_key,
                "tool_id": tool_id,
                "material_id": material_id,
                "ops": [],
            }

        # Compute feasibility for this op
        design = {
            "cut_length_mm": item.get("length_mm") or 0.0,
            "cut_depth_mm": item.get("thickness_mm") or 0.0,
            "material": material_id,
            "qty": item.get("qty") or 1,
        }
        context = {
            "tool_id": tool_id,
            "material_id": material_id,
            "stock_thickness_mm": item.get("thickness_mm") or 0.0,
        }

        try:
            feas = svc.check_feasibility(design, context)
            feas_d = _as_dict(feas)
            score = float(feas_d.get("score") or feas_d.get("feasibility_score") or 0.0)
            risk_bucket = str(feas_d.get("risk_bucket") or feas_d.get("risk") or "UNKNOWN").upper()
            warnings = feas_d.get("warnings") or []
        except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
            score = 0.0
            risk_bucket = "ERROR"
            warnings = [f"{type(e).__name__}: {e}"]

        op_id = item.get("op_id") or f"op_{uuid.uuid4().hex[:8]}"

        op = {
            "op_id": op_id,
            "setup_key": setup_key,
            "part_id": item.get("part_id"),
            "material_id": material_id,
            "thickness_mm": item.get("thickness_mm") or 0.0,
            "length_mm": item.get("length_mm") or 0.0,
            "qty": item.get("qty") or 1,
            "feasibility_score": score,
            "risk_bucket": risk_bucket,
            "warnings": warnings if isinstance(warnings, list) else [str(warnings)],
        }

        setups_by_material[setup_key]["ops"].append(op)

    setups = list(setups_by_material.values())

    payload = {
        "created_utc": _utc_now_iso(),
        "batch_spec_artifact_id": batch_spec_artifact_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "setups": setups,
    }

    art = write_run_artifact(
        kind="saw_batch_plan",
        status="OK",
        session_id=session_id,
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": batch_label,
            "session_id": session_id,
            "parent_batch_spec_artifact_id": batch_spec_artifact_id,
            "setup_count": len(setups),
            "op_count": sum(len(s["ops"]) for s in setups),
        },
        payload=payload,
    )

    artifact_id = art.get("artifact_id") if isinstance(art, dict) else getattr(art, "artifact_id", None)

    return {
        "batch_plan_artifact_id": artifact_id,
        "batch_spec_artifact_id": batch_spec_artifact_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "status": "OK",
        "setups": setups,
    }
