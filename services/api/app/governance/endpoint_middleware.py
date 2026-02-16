from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Optional, Set, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .endpoint_registry import EndpointStatus, lookup_endpoint
from .endpoint_stats import record_hit

logger = logging.getLogger(__name__)

# one warning per (method, path_pattern, status) per process
_WARNED: Set[Tuple[str, str, str]] = set()


# =============================================================================
# Per-Request Sampling (H5.2)
# =============================================================================

def _get_sample_rate() -> float:
    """Get sampling rate from env (0.0 = off, 1.0 = all requests)."""
    try:
        return float(os.getenv("ENDPOINT_SAMPLE_RATE", "0.0"))
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return 0.0


def _get_sample_log_path() -> Optional[str]:
    """Get optional JSONL log path for sampled requests."""
    return os.getenv("ENDPOINT_SAMPLE_LOG_PATH") or None


def _maybe_sample() -> bool:
    """Decide whether to sample this request based on configured rate."""
    rate = _get_sample_rate()
    if rate <= 0:
        return False
    if rate >= 1:
        return True
    return random.random() < rate


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
        start = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start) * 1000.0

        try:
            scope = request.scope
            endpoint = scope.get("endpoint")
            method = (scope.get("method") or "GET").upper()

            # FastAPI provides the templated route path via scope["route"].path
            route = scope.get("route")
            path_pattern = getattr(route, "path", None)  # e.g. "/api/rmos/runs/{run_id}"

            status = _get_status(endpoint=endpoint, method=method, path_pattern=path_pattern, route=route)
            if status:
                # Always record governed hits if status known (canonical/legacy/shadow/internal)
                replacement = _get_replacement(endpoint=endpoint, method=method, path_pattern=path_pattern)
                record_hit(
                    status=status.value,
                    method=method,
                    path_pattern=path_pattern or (request.url.path or ""),
                    path_actual=request.url.path,
                    replacement=replacement,
                )

                # Per-request sampling (structured) for incident review & low-noise telemetry.
                # Enabled via ENDPOINT_SAMPLE_RATE and ENDPOINT_SAMPLE_LOG_PATH.
                if _maybe_sample():
                    rid = getattr(getattr(request, "state", None), "request_id", None)
                    payload = {
                        "ts_utc": time.time(),
                        "request_id": rid,
                        "status": status.value,
                        "method": method,
                        "path_pattern": path_pattern or (request.url.path or ""),
                        "path_actual": request.url.path,
                        "replacement": replacement,
                        "latency_ms": round(latency_ms, 3),
                        "http_status": getattr(response, "status_code", None),
                    }

                    # Always emit to structured logs (cheap)
                    try:
                        logger.info("endpoint_sample=%s", json.dumps(payload, separators=(",", ":")))
                    except (TypeError, ValueError, OSError):  # WP-1: serialization/IO errors - middleware must not crash
                        pass

                    # Optional JSONL file append (best-effort)
                    log_path = _get_sample_log_path()
                    if log_path:
                        try:
                            from .endpoint_stats import _append_jsonl
                            _append_jsonl(log_path, payload)
                        except (OSError, ImportError):  # WP-1: narrowed from except Exception
                            pass

            if status in {EndpointStatus.LEGACY, EndpointStatus.SHADOW}:
                replacement = _get_replacement(endpoint=endpoint, method=method, path_pattern=path_pattern)
                _warn_once(method=method, path_pattern=path_pattern or (request.url.path or ""), status=status, replacement=replacement)
        except Exception:  # WP-1: keep broad — middleware must never interfere with request lifecycle
            logger.debug("Endpoint governance middleware failed (non-fatal).", exc_info=True)

        return response


def _get_status(*, endpoint, method: str, path_pattern: Optional[str], route=None) -> Optional[EndpointStatus]:
    # 1) From decorator annotation
    raw = getattr(endpoint, "__endpoint_status__", None) if endpoint else None
    if raw:
        try:
            return EndpointStatus(raw)
        except ValueError:  # WP-1: narrowed from except Exception
            return None

    # 2) From registry fallback
    if path_pattern:
        info = lookup_endpoint(method, path_pattern)
        if info:
            return info.status

    # 3) From FastAPI route tags (check for "Legacy" tag)
    # This allows tagging routes in main.py without modifying individual routers
    if route:
        tags = getattr(route, "tags", None) or []
        if "Legacy" in tags:
            return EndpointStatus.LEGACY

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
