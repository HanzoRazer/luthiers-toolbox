"""
Decision Intel Advisory Helper

Provides a simple function to get the latest approved tuning delta for a (tool_id, material_id) pair.
Used by batch_router.py to attach advisory to plan responses.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def get_latest_approved_delta_advisory(
    *,
    tool_id: str,
    material_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Returns an advisory dict if a previously approved tuning decision exists for (tool_id, material_id).
    
    Returns None if:
      - No approved decision found
      - Store unavailable
      - Any error (never raises)
    
    The returned dict shape:
    {
        "decision_artifact_id": str,
        "effective_delta": {"rpm_mul": float, "feed_mul": float, "doc_mul": float},
        "note": str,
    }
    """
    try:
        from app.saw_lab.decision_intel_apply_service import (
            ArtifactStorePorts,
            find_latest_approved_tuning_decision,
        )
        from app.rmos.runs_v2 import store as runs_store
        
        store = ArtifactStorePorts(
            list_runs_filtered=getattr(runs_store, "list_runs_filtered", lambda **kw: []),
            persist_run_artifact=getattr(runs_store, "persist_run_artifact", lambda **kw: {}),
        )
        
        decision_id, delta = find_latest_approved_tuning_decision(
            store,
            tool_id=tool_id,
            material_id=material_id,
        )
        
        if decision_id and delta:
            return {
                "decision_artifact_id": decision_id,
                "effective_delta": delta.model_dump(),
                "note": "Found approved tuning delta. Use /stamp-plan-link to apply.",
            }
        return None
    except Exception:
        return None
