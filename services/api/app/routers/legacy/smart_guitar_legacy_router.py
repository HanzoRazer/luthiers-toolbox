"""
Legacy Smart Guitar Temperament Router Aliases
==============================================

Backward compatibility for old /api/smart-guitar/temperaments/* routes.
Forwards to new /api/music/temperament/* routes.

Deprecation Notice:
  These routes will be removed in the next major release.
  Update your client code to use the new canonical routes.

Old Routes → New Routes:
  /api/smart-guitar/temperaments/systems → /api/music/temperament/systems
  /api/smart-guitar/temperaments/compare → /api/music/temperament/compare
  /api/smart-guitar/temperaments/keys → /api/music/temperament/keys
  /api/smart-guitar/temperaments/tunings → /api/music/temperament/tunings

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/smart-guitar", tags=["Legacy", "Smart Guitar", "Temperaments", "Deprecated"])


# =============================================================================
# DEPRECATION MIDDLEWARE HELPER
# =============================================================================

def add_deprecation_headers(response: Response, old_route: str, new_route: str):
    """Add deprecation headers to response."""
    response.headers["X-Deprecated-Route"] = "true"
    response.headers["X-New-Route"] = new_route
    response.headers["X-Deprecation-Notice"] = f"Route {old_route} is deprecated. Use {new_route} instead."


# =============================================================================
# TEMPERAMENT LEGACY ROUTES
# =============================================================================

@router.get("/temperaments/status")
async def legacy_temperament_status(response: Response) -> Dict[str, Any]:
    """Legacy route - returns deprecation notice with new route info."""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/status",
        "/api/music/temperament/health"
    )
    return {
        "deprecated": True,
        "message": "This route is deprecated. Please use /api/music/temperament/health",
        "redirect": "/api/music/temperament/health",
        "migration_guide": {
            "/api/smart-guitar/temperaments/systems": "/api/music/temperament/systems",
            "/api/smart-guitar/temperaments/compare": "/api/music/temperament/compare",
            "/api/smart-guitar/temperaments/keys": "/api/music/temperament/keys",
            "/api/smart-guitar/temperaments/tunings": "/api/music/temperament/tunings",
            "/api/smart-guitar/temperaments/compare-all": "/api/music/temperament/compare-all",
            "/api/smart-guitar/temperaments/equal-temperament": "/api/music/temperament/equal-temperament"
        }
    }


@router.get("/temperaments/systems")
async def legacy_temperament_systems(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/systems"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/systems",
        "/api/music/temperament/systems"
    )
    return RedirectResponse(
        url="/api/music/temperament/systems",
        status_code=308
    )


@router.get("/temperaments/keys")
async def legacy_temperament_keys(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/keys"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/keys",
        "/api/music/temperament/keys"
    )
    return RedirectResponse(
        url="/api/music/temperament/keys",
        status_code=308
    )


@router.get("/temperaments/tunings")
async def legacy_temperament_tunings(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/tunings"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/tunings",
        "/api/music/temperament/tunings"
    )
    return RedirectResponse(
        url="/api/music/temperament/tunings",
        status_code=308
    )


@router.post("/temperaments/compare")
async def legacy_temperament_compare(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/compare"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/compare",
        "/api/music/temperament/compare"
    )
    return RedirectResponse(
        url="/api/music/temperament/compare",
        status_code=308
    )


@router.get("/temperaments/compare-all")
async def legacy_temperament_compare_all(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/compare-all"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/compare-all",
        "/api/music/temperament/compare-all"
    )
    return RedirectResponse(
        url="/api/music/temperament/compare-all",
        status_code=308
    )


@router.get("/temperaments/equal-temperament")
async def legacy_temperament_equal(request: Request, response: Response):
    """Legacy route - redirects to /api/music/temperament/equal-temperament"""
    add_deprecation_headers(
        response,
        "/api/smart-guitar/temperaments/equal-temperament",
        "/api/music/temperament/equal-temperament"
    )
    return RedirectResponse(
        url="/api/music/temperament/equal-temperament",
        status_code=308
    )
