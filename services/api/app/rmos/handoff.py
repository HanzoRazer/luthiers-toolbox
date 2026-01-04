"""
RMOS Handoff Interface

This module exposes the ONLY RMOS operations that AI sandbox code
may import. All other rmos.* imports remain forbidden.

Architectural decision:
- AI sandbox creates advisories
- AI sandbox may call these handoff functions to link to runs
- This is the narrow, explicit trust boundary

See docs/AI_SANDBOX_GOVERNANCE.md for details.
"""
from __future__ import annotations

from typing import Optional, Any, List, Dict

# Import from the actual implementation
from .runs_v2.store import (
    get_run as _get_run,
    attach_advisory as _attach_advisory,
    RunStoreV2,
)


def get_run(run_id: str) -> Optional[Any]:
    """
    Get a run by ID (read-only access).
    
    AI sandbox may use this to verify a run exists before attaching.
    """
    return _get_run(run_id)


def attach_advisory(
    run_id: str,
    advisory_id: str,
    kind: str = "advisory",
    engine_id: Optional[str] = None,
    engine_version: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Optional[Any]:
    """
    Attach an advisory asset to an existing run.
    
    This is the handoff point where AI-generated content becomes
    linked to RMOS authority. The advisory must already be reviewed
    and approved.
    
    Returns the AdvisoryRef if successful, None otherwise.
    """
    return _attach_advisory(
        run_id=run_id,
        advisory_id=advisory_id,
        kind=kind,
        engine_id=engine_id,
        engine_version=engine_version,
        request_id=request_id,
    )


def find_runs_with_advisory(advisory_id: str, limit: int = 500) -> List[Dict[str, Any]]:
    """
    Find all runs that have a specific advisory attached.
    
    This is a read-only query to find which runs reference a given advisory.
    Used for reverse-lookup from advisory asset to runs.
    
    Returns a list of dicts with run info and advisory attachment details.
    """
    run_store = RunStoreV2()
    all_runs = run_store.list_runs(limit=limit)
    
    matching_runs = []
    for run in all_runs:
        if run.advisory_inputs:
            for ref in run.advisory_inputs:
                if ref.advisory_id == advisory_id:
                    matching_runs.append({
                        "run_id": run.run_id,
                        "created_at_utc": run.created_at_utc.isoformat(),
                        "mode": run.mode,
                        "status": run.status,
                        "event_type": run.event_type,
                        "advisory_kind": ref.kind,
                        "attached_at_utc": ref.created_at_utc.isoformat(),
                    })
                    break
    
    return matching_runs


__all__ = ["get_run", "attach_advisory", "find_runs_with_advisory"]
