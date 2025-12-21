"""
Legacy Guitar Router Aliases
============================

Backward compatibility for old /api/guitar/{model}/* routes.
Forwards to new /api/instruments/guitar/{model}/* and /api/cam/guitar/{model}/* routes.

Deprecation Notice:
  These routes will be removed in the next major release.
  Update your client code to use the new canonical routes.

Old Routes → New Routes:
  /api/guitar/archtop/cam/archtop/* → /api/cam/guitar/archtop/*
  /api/guitar/stratocaster/cam/stratocaster/* → /api/cam/guitar/stratocaster/*
  /api/guitar/om/cam/om/* → /api/cam/guitar/om/*
  /api/guitar/smart/cam/smart-guitar/* → /api/cam/guitar/smart/*

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Legacy", "Guitar", "Deprecated"])


# =============================================================================
# DEPRECATION MIDDLEWARE HELPER
# =============================================================================

def add_deprecation_headers(response: Response, old_route: str, new_route: str):
    """Add deprecation headers to response."""
    response.headers["X-Deprecated-Route"] = "true"
    response.headers["X-New-Route"] = new_route
    response.headers["X-Deprecation-Notice"] = f"Route {old_route} is deprecated. Use {new_route} instead."


# =============================================================================
# ARCHTOP LEGACY ROUTES
# =============================================================================

@router.get("/guitar/archtop/cam/archtop/contours/csv")
async def legacy_archtop_contours_csv(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/archtop/contours/csv"""
    add_deprecation_headers(
        response, 
        "/api/guitar/archtop/cam/archtop/contours/csv",
        "/api/cam/guitar/archtop/contours/csv"
    )
    return RedirectResponse(
        url="/api/cam/guitar/archtop/contours/csv",
        status_code=308  # Permanent redirect, preserve method
    )


@router.post("/guitar/archtop/cam/archtop/contours/csv")
async def legacy_archtop_contours_csv_post(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/archtop/contours/csv"""
    return RedirectResponse(
        url="/api/cam/guitar/archtop/contours/csv",
        status_code=308
    )


@router.post("/guitar/archtop/cam/archtop/contours/outline")
async def legacy_archtop_contours_outline(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/archtop/contours/outline"""
    return RedirectResponse(
        url="/api/cam/guitar/archtop/contours/outline",
        status_code=308
    )


@router.post("/guitar/archtop/cam/archtop/fit")
async def legacy_archtop_fit(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/archtop/fit"""
    return RedirectResponse(
        url="/api/cam/guitar/archtop/fit",
        status_code=308
    )


@router.get("/guitar/archtop/info")
async def legacy_archtop_info(response: Response) -> Dict[str, Any]:
    """Legacy route - returns deprecation notice with new route."""
    add_deprecation_headers(
        response,
        "/api/guitar/archtop/info",
        "/api/instruments/guitar/archtop/info"
    )
    return {
        "deprecated": True,
        "message": "This route is deprecated. Please use /api/instruments/guitar/archtop/info",
        "redirect": "/api/instruments/guitar/archtop/info"
    }


# =============================================================================
# STRATOCASTER LEGACY ROUTES
# =============================================================================

@router.get("/guitar/stratocaster/cam/stratocaster/templates")
async def legacy_stratocaster_templates(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/stratocaster/templates"""
    return RedirectResponse(
        url="/api/cam/guitar/stratocaster/templates",
        status_code=308
    )


@router.get("/guitar/stratocaster/cam/stratocaster/bom")
async def legacy_stratocaster_bom(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/stratocaster/bom"""
    return RedirectResponse(
        url="/api/cam/guitar/stratocaster/bom",
        status_code=308
    )


@router.get("/guitar/stratocaster/info")
async def legacy_stratocaster_info(response: Response) -> Dict[str, Any]:
    """Legacy route - returns deprecation notice with new route."""
    add_deprecation_headers(
        response,
        "/api/guitar/stratocaster/info",
        "/api/instruments/guitar/stratocaster/info"
    )
    return {
        "deprecated": True,
        "message": "This route is deprecated. Please use /api/instruments/guitar/stratocaster/info",
        "redirect": "/api/instruments/guitar/stratocaster/info"
    }


# =============================================================================
# OM LEGACY ROUTES
# =============================================================================

@router.get("/guitar/om/cam/om/templates")
async def legacy_om_templates(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/om/templates"""
    return RedirectResponse(
        url="/api/cam/guitar/om/templates",
        status_code=308
    )


@router.get("/guitar/om/cam/om/graduation")
async def legacy_om_graduation(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/om/graduation"""
    return RedirectResponse(
        url="/api/cam/guitar/om/graduation",
        status_code=308
    )


@router.get("/guitar/om/cam/om/kits")
async def legacy_om_kits(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/om/kits"""
    return RedirectResponse(
        url="/api/cam/guitar/om/kits",
        status_code=308
    )


@router.get("/guitar/om/info")
async def legacy_om_info(response: Response) -> Dict[str, Any]:
    """Legacy route - returns deprecation notice with new route."""
    add_deprecation_headers(
        response,
        "/api/guitar/om/info",
        "/api/instruments/guitar/om/info"
    )
    return {
        "deprecated": True,
        "message": "This route is deprecated. Please use /api/instruments/guitar/om/info",
        "redirect": "/api/instruments/guitar/om/info"
    }


# =============================================================================
# SMART GUITAR LEGACY ROUTES (CAM)
# =============================================================================

@router.get("/guitar/smart/cam/smart-guitar/info")
async def legacy_smart_guitar_cam_info(request: Request, response: Response):
    """Legacy route - redirects to /api/cam/guitar/smart/health"""
    return RedirectResponse(
        url="/api/cam/guitar/smart/health",
        status_code=308
    )


@router.get("/guitar/smart/info")
async def legacy_smart_guitar_info(response: Response) -> Dict[str, Any]:
    """Legacy route - returns deprecation notice with new route."""
    add_deprecation_headers(
        response,
        "/api/guitar/smart/info",
        "/api/instruments/guitar/smart/info"
    )
    return {
        "deprecated": True,
        "message": "This route is deprecated. Please use /api/instruments/guitar/smart/info",
        "redirect": "/api/instruments/guitar/smart/info"
    }
