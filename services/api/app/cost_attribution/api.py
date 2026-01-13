from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Any, Dict, Optional
from pathlib import Path

from .store import summarize_by_batch, summarize_by_instrument

router = APIRouter(prefix="/api/cost", tags=["Cost Attribution"])


def _repo_root() -> Path:
    """Get repository root path."""
    # services/api/app/cost_attribution/api.py -> repo root
    return Path(__file__).resolve().parents[4]


@router.get("/summary")
def get_cost_summary(
    manufacturing_batch_id: Optional[str] = Query(default=None),
    instrument_id: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """
    Get cost attribution summary.

    Query by either:
    - manufacturing_batch_id: Get costs for an entire manufacturing batch
    - instrument_id: Get costs for a specific instrument

    Returns:
        Cost summary with breakdown by cost dimension
    """
    if manufacturing_batch_id:
        return summarize_by_batch(_repo_root(), manufacturing_batch_id)
    if instrument_id:
        return summarize_by_instrument(_repo_root(), instrument_id)
    return {
        "detail": "Provide manufacturing_batch_id or instrument_id"
    }


@router.get("/health")
def cost_health() -> Dict[str, str]:
    """Health check for cost attribution module."""
    return {"status": "ok", "module": "cost_attribution"}
