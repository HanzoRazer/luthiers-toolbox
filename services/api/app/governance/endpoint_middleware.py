from __future__ import annotations

import logging
from typing import Optional, Set, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .endpoint_registry import EndpointStatus, lookup_endpoint

logger = logging.getLogger(__name__)

# one warning per (method, path_pattern, status) per process
_WARNED: Set[Tuple[str, str, str]] = set()


class EndpointGovernanceMiddleware(BaseHTTPMiddleware):
    """
    Runtime visibility for legacy/shadow endpoints.

    Behavior:
      - If endpoint has @endpoint_meta, we honor it
      - Otherwise, we fall back to ENDPOINT_REGISTRY lookup using the FastAPI
        path pattern (e.g. "/api/rmos/runs/{run_id}") when available.
      - For LEGACY/SHADOW: log a warning once per process.

    This is intentionally non-blocking (no HTTP behavior changes).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        try:
            scope = request.scope
            endpoint = scope.get("endpoint")
            method = (scope.get("method") or "GET").upper()

            # FastAPI provides the templated route path via scope["route"].path
            route = scope.get("route")
            path_pattern = getattr(route, "path", None)  # e.g. "/api/rmos/runs/{run_id}"

            status = _get_status(endpoint=endpoint, method=method, path_pattern=path_pattern)
            if status in {EndpointStatus.LEGACY, EndpointStatus.SHADOW}:
                replacement = _get_replacement(endpoint=endpoint, method=method, path_pattern=path_pattern)
                _warn_once(method=method, path_pattern=path_pattern or (request.url.path or ""), status=status, replacement=replacement)
        except Exception:
            # Never interfere with request lifecycle
            logger.debug("Endpoint governance middleware failed (non-fatal).", exc_info=True)

        return response


def _get_status(*, endpoint, method: str, path_pattern: Optional[str]) -> Optional[EndpointStatus]:
    # 1) From decorator annotation
    raw = getattr(endpoint, "__endpoint_status__", None) if endpoint else None
    if raw:
        try:
            return EndpointStatus(raw)
        except Exception:
            return None

    # 2) From registry fallback
    if path_pattern:
        info = lookup_endpoint(method, path_pattern)
        if info:
            return info.status

    return None


def _get_replacement(*, endpoint, method: str, path_pattern: Optional[str]) -> Optional[str]:
    # 1) From decorator annotation
    replacement = getattr(endpoint, "__endpoint_replacement__", None) if endpoint else None
    if replacement:
        return replacement

    # 2) From registry fallback
    if path_pattern:
        info = lookup_endpoint(method, path_pattern)
        if info:
            return info.replacement

    return None


def _warn_once(*, method: str, path_pattern: str, status: EndpointStatus, replacement: Optional[str]) -> None:
    key = (method, path_pattern, status.value)
    if key in _WARNED:
        return
    _WARNED.add(key)

    msg = f"[endpoint_governance] {status.value.upper()} endpoint hit: {method} {path_pattern}"
    if replacement:
        msg += f" | replacement: {replacement}"

    logger.warning(msg)
