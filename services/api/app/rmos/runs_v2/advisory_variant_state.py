"""
Advisory variant state persistence.

This persists review/reject state in a simple, per-run directory.
It does NOT mint RunArtifacts and does not interfere with validate_and_persist() invariants.

State is stored under:
  {state_root}/rejected/{run_id}/{advisory_id}.json

Configure with RMOS_RUN_VARIANT_STATE_DIR environment variable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .schemas_advisory_reject import (
    AdvisoryVariantRejectionRecord,
    RejectVariantRequest,
    utc_now_iso,
)


STATE_DIR_DEFAULT = "services/api/data/run_variant_state"


def _state_root() -> Path:
    """Get the root directory for variant state files."""
    root = os.getenv("RMOS_RUN_VARIANT_STATE_DIR", STATE_DIR_DEFAULT)
    return Path(root)


def _reject_path(run_id: str, advisory_id: str) -> Path:
    """Get the path to the rejection record file.
    
    One file per variant state (high-signal, easy to debug).
    """
    return _state_root() / "rejected" / run_id / f"{advisory_id}.json"


def write_rejection(
    run_id: str, advisory_id: str, req: RejectVariantRequest
) -> AdvisoryVariantRejectionRecord:
    """
    Write a rejection record for an advisory variant.
    
    Creates the directory structure if needed.
    Overwrites any existing rejection (idempotent).
    """
    rec = AdvisoryVariantRejectionRecord(
        run_id=run_id,
        advisory_id=advisory_id,
        rejected_at_utc=utc_now_iso(),
        reason_code=req.reason_code,
        reason_detail=req.reason_detail,
        operator_note=req.operator_note,
    )
    path = _reject_path(run_id, advisory_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec.model_dump(), indent=2), encoding="utf-8")
    return rec


def read_rejection(
    run_id: str, advisory_id: str
) -> Optional[AdvisoryVariantRejectionRecord]:
    """
    Read a rejection record for an advisory variant.
    
    Returns None if no rejection exists.
    """
    path = _reject_path(run_id, advisory_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return AdvisoryVariantRejectionRecord(**data)


def clear_rejection(run_id: str, advisory_id: str) -> bool:
    """
    Clear/undo a rejection for an advisory variant.
    
    Returns True if a rejection was cleared, False if none existed.
    """
    path = _reject_path(run_id, advisory_id)
    if path.exists():
        path.unlink()
        return True
    return False


def is_rejected(run_id: str, advisory_id: str) -> bool:
    """Check if an advisory variant is rejected."""
    return _reject_path(run_id, advisory_id).exists()
