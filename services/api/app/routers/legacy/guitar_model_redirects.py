"""
Guitar Model Legacy Redirects
=============================

308 Permanent Redirects from legacy guitar model routes to Wave 20 canonical routes.

Legacy Route Structure (DEPRECATED):
  /api/guitar/{model}/cam/{model}/*  →  /api/cam/guitar/{model}/*

Canonical Route Structure (USE THESE):
  /api/instruments/guitar/{model}/*  - Instrument specs, info
  /api/cam/guitar/{model}/*          - CAM operations, toolpaths

Models with redirects:
  - archtop
  - stratocaster
  - om
  - smart (smart-guitar → smart)

HTTP 308 preserves method and body on redirect.

Wave 20: Option C API Restructuring - Legacy Cleanup
December 2025
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Legacy", "Redirects", "Deprecated"])


# =============================================================================
# ARCHTOP REDIRECTS
# Legacy: /api/guitar/archtop/cam/archtop/* → /api/cam/guitar/archtop/*
# =============================================================================

@router.api_route(
    "/guitar/archtop/cam/archtop/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_archtop_cam(path: str, request: Request):
    """Redirect legacy archtop CAM routes to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/archtop/{path}{query}",
        status_code=308,
    )


@router.api_route(
    "/guitar/archtop/cam/archtop",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_archtop_cam_root(request: Request):
    """Redirect legacy archtop CAM root to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/archtop{query}",
        status_code=308,
    )


# =============================================================================
# STRATOCASTER REDIRECTS
# Legacy: /api/guitar/stratocaster/cam/stratocaster/* → /api/cam/guitar/stratocaster/*
# =============================================================================

@router.api_route(
    "/guitar/stratocaster/cam/stratocaster/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_stratocaster_cam(path: str, request: Request):
    """Redirect legacy stratocaster CAM routes to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/stratocaster/{path}{query}",
        status_code=308,
    )


@router.api_route(
    "/guitar/stratocaster/cam/stratocaster",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_stratocaster_cam_root(request: Request):
    """Redirect legacy stratocaster CAM root to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/stratocaster{query}",
        status_code=308,
    )


# =============================================================================
# OM REDIRECTS
# Legacy: /api/guitar/om/cam/om/* → /api/cam/guitar/om/*
# =============================================================================

@router.api_route(
    "/guitar/om/cam/om/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_om_cam(path: str, request: Request):
    """Redirect legacy OM CAM routes to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/om/{path}{query}",
        status_code=308,
    )


@router.api_route(
    "/guitar/om/cam/om",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_om_cam_root(request: Request):
    """Redirect legacy OM CAM root to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/om{query}",
        status_code=308,
    )


# =============================================================================
# SMART GUITAR REDIRECTS
# Legacy: /api/guitar/smart/cam/smart-guitar/* → /api/cam/guitar/smart/*
# Also: /api/smart-guitar/* → /api/music/temperament/* (for temperament routes)
# =============================================================================

@router.api_route(
    "/guitar/smart/cam/smart-guitar/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_smart_guitar_cam(path: str, request: Request):
    """Redirect legacy smart guitar CAM routes to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/smart/{path}{query}",
        status_code=308,
    )


@router.api_route(
    "/guitar/smart/cam/smart-guitar",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_smart_guitar_cam_root(request: Request):
    """Redirect legacy smart guitar CAM root to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/cam/guitar/smart{query}",
        status_code=308,
    )


# Legacy /api/smart-guitar/temperaments/* → /api/music/temperament/*
@router.api_route(
    "/smart-guitar/temperaments/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_smart_guitar_temperaments(path: str, request: Request):
    """Redirect legacy temperament routes to canonical music API."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/music/temperament/{path}{query}",
        status_code=308,
    )


@router.api_route(
    "/smart-guitar/temperaments",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def redirect_smart_guitar_temperaments_root(request: Request):
    """Redirect legacy temperament root to canonical."""
    query = f"?{request.query_params}" if request.query_params else ""
    return RedirectResponse(
        url=f"/api/music/temperament{query}",
        status_code=308,
    )


# =============================================================================
# DEPRECATION INFO ENDPOINT
# =============================================================================

@router.get("/guitar/legacy-routes-info")
async def legacy_routes_info():
    """
    Information about deprecated legacy guitar routes.
    
    Returns mapping of old routes to new canonical routes.
    """
    return {
        "status": "deprecated",
        "message": "These legacy routes are deprecated. Please migrate to canonical routes.",
        "migrations": {
            "/api/guitar/archtop/cam/archtop/*": "/api/cam/guitar/archtop/*",
            "/api/guitar/stratocaster/cam/stratocaster/*": "/api/cam/guitar/stratocaster/*",
            "/api/guitar/om/cam/om/*": "/api/cam/guitar/om/*",
            "/api/guitar/smart/cam/smart-guitar/*": "/api/cam/guitar/smart/*",
            "/api/smart-guitar/temperaments/*": "/api/music/temperament/*",
        },
        "canonical_structure": {
            "instruments": "/api/instruments/guitar/{model}/* - Specs, info, geometry",
            "cam": "/api/cam/guitar/{model}/* - Toolpaths, templates, CAM operations",
            "music": "/api/music/temperament/* - Temperament systems",
        },
        "redirect_behavior": "HTTP 308 Permanent Redirect (preserves method and body)",
    }


__all__ = ["router"]
