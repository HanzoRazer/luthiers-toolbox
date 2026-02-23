"""
Miscellaneous Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors.

Endpoints covered:
- /ai/advisories/* - AI advisory requests
- /blueprint/* - Blueprint analysis and conversion
- /art/rosette/compare/snapshot - Single snapshot endpoint (snapshots list is real)

Note: Many /art/rosette/* and /ai/context/* endpoints now have real implementations.
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
# AI Context Stubs
# =============================================================================

# =============================================================================
# Blueprint Stubs
# =============================================================================

@router.post("/blueprint/analyze")
def analyze_blueprint(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze a blueprint image or PDF."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "analysis": {},
        "features": [],
        "message": "Stub: blueprint analysis not yet implemented",
    }


@router.post("/blueprint/to-svg")
def blueprint_to_svg(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert blueprint to SVG."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "svg": None,
        "message": "Stub: blueprint-to-SVG not yet implemented",
    }


@router.post("/blueprint/vectorize-geometry")
def vectorize_geometry(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Vectorize geometry from blueprint."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "vectors": [],
        "message": "Stub: vectorization not yet implemented",
    }


@router.get("/blueprint/static/{asset_path:path}")
def get_blueprint_static(asset_path: str) -> Dict[str, Any]:
    """Get static blueprint asset."""
    return {
        "ok": False,
        "message": f"Static asset not found: {asset_path}",
    }


# =============================================================================
# Art Rosette Stubs
# =============================================================================

@router.get("/art/rosette/compare/snapshot")
def get_rosette_compare_snapshot() -> Dict[str, Any]:
    """Get rosette comparison snapshot."""
    return {"snapshot": None}


