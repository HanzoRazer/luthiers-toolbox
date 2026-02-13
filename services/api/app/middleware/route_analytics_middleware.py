# route_analytics_middleware.py
"""
Lightweight route analytics middleware for FastAPI.
Works on Railway (logs to stdout, captured by Railway logs).

Usage in main.py:
    from route_analytics_middleware import RouteAnalyticsMiddleware, analytics_router
    app.add_middleware(RouteAnalyticsMiddleware)
    app.include_router(analytics_router, prefix="/api/_analytics", tags=["internal"])
"""
from fastapi import Request, APIRouter
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from collections import defaultdict
import threading
import json
import os

# In-memory stats (persists until redeploy)
_stats: dict = defaultdict(lambda: {
    "call_count": 0,
    "total_ms": 0.0,
    "avg_ms": 0.0,
    "last_used": None,
    "status_codes": defaultdict(int)
})
_lock = threading.Lock()
_start_time = datetime.utcnow().isoformat()


class RouteAnalyticsMiddleware(BaseHTTPMiddleware):
    """Captures route usage metrics."""

    # Routes to skip (health checks, static, analytics itself)
    SKIP_PREFIXES = ("/health", "/docs", "/openapi", "/api/_analytics", "/favicon")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip noise
        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        start = datetime.utcnow()
        response = await call_next(request)
        elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000

        # Normalize path (replace IDs with placeholder)
        normalized = self._normalize_path(path)
        key = f"{request.method}:{normalized}"

        with _lock:
            _stats[key]["call_count"] += 1
            _stats[key]["total_ms"] += elapsed_ms
            _stats[key]["avg_ms"] = _stats[key]["total_ms"] / _stats[key]["call_count"]
            _stats[key]["last_used"] = datetime.utcnow().isoformat()
            _stats[key]["status_codes"][str(response.status_code)] += 1

        # Also log to stdout for Railway log capture
        if os.getenv("ANALYTICS_VERBOSE"):
            print(f"[ROUTE] {key} | {response.status_code} | {elapsed_ms:.1f}ms")

        return response

    def _normalize_path(self, path: str) -> str:
        """Replace UUIDs and numeric IDs with placeholders."""
        import re
        # UUID pattern
        path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path, flags=re.I)
        # Numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
        # Hash-like strings (32+ hex chars)
        path = re.sub(r'/[0-9a-f]{32,}(?=/|$)', '/{hash}', path, flags=re.I)
        return path


# === Analytics API Endpoints ===

analytics_router = APIRouter()


@analytics_router.get("/summary")
def get_analytics_summary():
    """Get route usage summary."""
    with _lock:
        total_calls = sum(s["call_count"] for s in _stats.values())
        routes_by_usage = sorted(
            [(k, v["call_count"]) for k, v in _stats.items()],
            key=lambda x: -x[1]
        )
        return {
            "collection_started": _start_time,
            "total_routes_hit": len(_stats),
            "total_calls": total_calls,
            "top_20": routes_by_usage[:20],
            "bottom_20_nonzero": [r for r in routes_by_usage if r[1] > 0][-20:]
        }


@analytics_router.get("/export")
def export_analytics():
    """Export full analytics for router harness."""
    with _lock:
        # Convert to harness-compatible format
        export = {}
        for key, data in _stats.items():
            method, path = key.split(":", 1)
            # Extract function name hint from path
            func_hint = path.strip("/").replace("/", "_").replace("{", "").replace("}", "") or "root"

            total_calls = sum(s["call_count"] for s in _stats.values())
            frequency = data["call_count"] / total_calls if total_calls > 0 else 0

            export[func_hint] = {
                "path": path,
                "method": method,
                "call_count": data["call_count"],
                "frequency": round(frequency, 6),
                "avg_response_ms": round(data["avg_ms"], 2),
                "last_used": data["last_used"],
                "status_codes": dict(data["status_codes"])
            }

        return {
            "collection_started": _start_time,
            "exported_at": datetime.utcnow().isoformat(),
            "routes": export
        }


@analytics_router.get("/zero-usage")
def get_zero_usage_routes():
    """Routes that were NEVER called (potential cull candidates)."""
    # This only works if you've hit all routes at least once during collection
    # For now, return routes with 0 calls from our stats
    with _lock:
        zero = [k for k, v in _stats.items() if v["call_count"] == 0]
        return {"zero_usage_routes": zero, "count": len(zero)}


@analytics_router.post("/reset")
def reset_analytics():
    """Reset all collected analytics."""
    global _start_time
    with _lock:
        _stats.clear()
        _start_time = datetime.utcnow().isoformat()
    return {"status": "reset", "new_start_time": _start_time}
