"""
Deprecation Headers Middleware.

Adds RFC-style deprecation headers and warning logs for legacy endpoint lanes.
Does NOT block requests - purely observational.

Headers added for deprecated endpoints:
    Deprecation: true
    Sunset: <date>
    X-Deprecated-Lane: <lane_key>
    Link: <successor>; rel="successor-version"

Server log:
    DEPRECATED_ENDPOINT_HIT lane=... method=... path=... successor=...
"""
from __future__ import annotations

import logging
import os
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


def _deprecated_lane(path: str) -> Optional[str]:
    """
    Returns the lane key if the request is hitting a deprecated endpoint prefix.
    """
    if path.startswith("/api/art-studio"):
        return "legacy_art_studio_lane"
    if path.startswith("/rosette"):
        return "transitional_no_api_prefix_lane"
    return None


def _successor_link(path: str) -> Optional[str]:
    """
    Provide a best-effort successor mapping.
    Keep it intentionally conservative: we only map by prefix.
    """
    if path.startswith("/api/art-studio"):
        # redirect conceptually to /api/art/*
        # example: /api/art-studio/rosette/preview -> /api/art/rosette/preview/svg (not 1:1)
        return "/api/art"
    if path.startswith("/rosette"):
        return "/api/art"
    return None


class DeprecationHeadersMiddleware(BaseHTTPMiddleware):
    """
    Minimal deprecation guardrail:
    - Adds Deprecation/Sunset/Link headers for deprecated lanes
    - Emits a warning log so legacy hits are loud (not silent)

    This does NOT block requests.
    """

    def __init__(self, app, sunset_date: Optional[str] = None):
        super().__init__(app)
        self.sunset_date = sunset_date or os.getenv("DEPRECATION_SUNSET_DATE", "2026-06-30")

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        lane = _deprecated_lane(path)

        response: Response = await call_next(request)

        if lane:
            successor = _successor_link(path)

            # Standard-ish headers
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = self.sunset_date
            response.headers["X-Deprecated-Lane"] = lane

            if successor:
                # RFC-style Link header (simple)
                response.headers["Link"] = f'<{successor}>; rel="successor-version"'

            logger.warning(
                "DEPRECATED_ENDPOINT_HIT lane=%s method=%s path=%s successor=%s",
                lane,
                request.method,
                path,
                successor,
            )

        return response
