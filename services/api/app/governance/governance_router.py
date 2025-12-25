from __future__ import annotations

from fastapi import APIRouter

from .endpoint_stats import snapshot, reset


router = APIRouter(prefix="/governance/endpoints", tags=["Governance"])


@router.get("/stats")
def get_endpoint_stats():
    """
    Return endpoint governance hit counters + recent hit log.
    Used to measure legacy/shadow usage before deletions.
    """
    return snapshot()


@router.post("/stats/reset")
def reset_endpoint_stats():
    """
    Reset in-memory counters (does NOT truncate JSONL log file).
    Useful between test runs or during manual verification.
    """
    reset()
    return {"ok": True}
