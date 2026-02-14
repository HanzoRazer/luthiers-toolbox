"""
Miscellaneous Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors.

Endpoints covered:
- /ai/advisories/* - AI advisory requests
- /ai/context/* - AI context building
- /blueprint/* - Blueprint analysis and conversion
- /art/rosette/* - Art rosette operations
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
def request_advisory(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Request an AI advisory for design decisions."""
    return {
        "ok": True,
        "advisory_id": None,
        "status": "not_implemented",
        "message": "Stub: AI advisory not yet implemented",
    }


# =============================================================================
# AI Context Stubs
# =============================================================================

@router.post("/ai/context/build")
def build_ai_context(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Build AI context packet for design assistance."""
    return {
        "ok": True,
        "context_id": None,
        "packet": {},
        "message": "Stub: AI context building not yet implemented",
    }


# =============================================================================
# Blueprint Stubs
# =============================================================================

@router.post("/blueprint/analyze")
def analyze_blueprint(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Analyze a blueprint image or PDF."""
    return {
        "ok": True,
        "analysis": {},
        "features": [],
        "message": "Stub: blueprint analysis not yet implemented",
    }


@router.post("/blueprint/to-svg")
def blueprint_to_svg(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Convert blueprint to SVG."""
    return {
        "ok": True,
        "svg": None,
        "message": "Stub: blueprint-to-SVG not yet implemented",
    }


@router.post("/blueprint/vectorize-geometry")
def vectorize_geometry(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Vectorize geometry from blueprint."""
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

@router.get("/art/rosette/jobs")
def list_rosette_jobs(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """List rosette design jobs."""
    return {"jobs": [], "total": 0}


@router.get("/art/rosette/presets")
def list_rosette_presets() -> Dict[str, Any]:
    """List rosette design presets."""
    return {"presets": [], "total": 0}


@router.post("/art/rosette/preview")
def preview_rosette(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Generate rosette preview."""
    return {
        "ok": True,
        "preview_url": None,
        "message": "Stub: rosette preview not yet implemented",
    }


@router.post("/art/rosette/save")
def save_rosette(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Save rosette design."""
    return {
        "ok": True,
        "rosette_id": None,
        "message": "Stub: rosette save not yet implemented",
    }


@router.post("/art/rosette/compare")
def compare_rosettes(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Compare two rosette designs."""
    return {
        "ok": True,
        "diffs": [],
        "message": "Stub: rosette comparison not yet implemented",
    }


@router.get("/art/rosette/compare/snapshot")
def get_rosette_compare_snapshot() -> Dict[str, Any]:
    """Get rosette comparison snapshot."""
    return {"snapshot": None}


@router.get("/art/rosette/compare/snapshots")
def list_rosette_compare_snapshots() -> Dict[str, Any]:
    """List rosette comparison snapshots."""
    return {"snapshots": [], "total": 0}
