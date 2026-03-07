"""
Miscellaneous Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors.

Endpoints covered:
- /ai/advisories/* - AI advisory requests (real service exists but needs router wiring)
- /art/rosette/compare/snapshot - Single snapshot GET (list endpoint is real)

REMOVED (real implementations exist):
- /blueprint/* - See app.routers.blueprint (phase1_router, phase2_router)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel


router = APIRouter(tags=["stubs"])


# =============================================================================
# AI Advisory Stubs
# =============================================================================

@router.post("/ai/advisories/request")
def request_advisory(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Request an AI advisory for design decisions."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "advisory_id": None,
        "status": "not_implemented",
        "message": "Stub: AI advisory not yet implemented",
    }


# =============================================================================
# Art Rosette Stubs
# =============================================================================

@router.get("/art/rosette/compare/snapshot")
def get_rosette_compare_snapshot() -> Dict[str, Any]:
    """Get rosette comparison snapshot."""
    return {"snapshot": None}


