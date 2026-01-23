"""
Legacy Temperament Router
=========================

Backward compatibility for old /api/smart-guitar/temperaments/* routes.
Forwards to new /api/music/temperament/* routes.

Deprecation Notice:
  These routes will be removed in the next major release.
  Update your client code to use the new canonical routes.

Old Routes → New Routes:
  /api/smart-guitar/temperaments/systems → /api/music/temperament/systems
  /api/smart-guitar/temperaments/keys → /api/music/temperament/keys
  /api/smart-guitar/temperaments/tunings → /api/music/temperament/tunings
  /api/smart-guitar/temperaments/compare → /api/music/temperament/compare
  /api/smart-guitar/temperaments/compare-all → /api/music/temperament/compare-all
  /api/smart-guitar/temperaments/equal-temperament → /api/music/temperament/equal-temperament

Wave 15: Option C API Restructuring
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/smart-guitar/temperaments", tags=["Legacy", "Temperaments", "Deprecated"])


# =============================================================================
# LEGACY TEMPERAMENT ROUTES → /api/music/temperament/*
# =============================================================================

@router.get("/systems")
async def legacy_temperament_systems(request: Request):
    """Legacy route - redirects to /api/music/temperament/systems"""
    return RedirectResponse(
        url="/api/music/temperament/systems",
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/systems"
        }
    )


@router.get("/keys")
async def legacy_temperament_keys(request: Request):
    """Legacy route - redirects to /api/music/temperament/keys"""
    return RedirectResponse(
        url="/api/music/temperament/keys",
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/keys"
        }
    )


@router.get("/tunings")
async def legacy_temperament_tunings(request: Request):
    """Legacy route - redirects to /api/music/temperament/tunings"""
    return RedirectResponse(
        url="/api/music/temperament/tunings",
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/tunings"
        }
    )


@router.post("/compare")
async def legacy_temperament_compare(request: Request):
    """Legacy route - redirects to /api/music/temperament/compare"""
    return RedirectResponse(
        url="/api/music/temperament/compare",
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/compare"
        }
    )


@router.get("/compare-all")
async def legacy_temperament_compare_all(request: Request):
    """Legacy route - redirects to /api/music/temperament/compare-all"""
    query = str(request.query_params)
    url = "/api/music/temperament/compare-all"
    if query:
        url += f"?{query}"
    return RedirectResponse(
        url=url,
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/compare-all"
        }
    )


@router.get("/equal-temperament")
async def legacy_temperament_equal(request: Request):
    """Legacy route - redirects to /api/music/temperament/equal-temperament"""
    query = str(request.query_params)
    url = "/api/music/temperament/equal-temperament"
    if query:
        url += f"?{query}"
    return RedirectResponse(
        url=url,
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/equal-temperament"
        }
    )


@router.get("/status")
async def legacy_temperament_status(request: Request):
    """Legacy route - redirects to /api/music/temperament/health"""
    return RedirectResponse(
        url="/api/music/temperament/health",
        status_code=308,
        headers={
            "X-Deprecated-Route": "true",
            "X-New-Route": "/api/music/temperament/health"
        }
    )
