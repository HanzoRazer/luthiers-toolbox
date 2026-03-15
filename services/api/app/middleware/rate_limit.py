# services/api/app/middleware/rate_limit.py
"""
API Rate Limiting Middleware

Provides configurable rate limiting for the Production Shop API using slowapi.

Rate Limit Tiers:
- Public/unauthenticated: 30 requests/minute (strict)
- Authenticated (free tier): 60 requests/minute
- Authenticated (pro tier): 300 requests/minute
- AI endpoints: 10 requests/minute (expensive operations)
- CNC/CAM export: 20 requests/minute (computational)
- Health/status: No limit (monitoring)

Environment Variables:
- RATE_LIMIT_ENABLED: Set to "0" or "false" to disable (default: enabled)
- RATE_LIMIT_STORAGE: "memory" (default) or "redis://host:port/db"
- RATE_LIMIT_DEFAULT: Override default limit (e.g., "100/minute")

Usage in routers:
    from app.middleware.rate_limit import limiter, rate_limit_tier

    @router.post("/generate-gcode")
    @limiter.limit(rate_limit_tier("cam"))
    async def generate_gcode(request: Request, ...):
        ...

    # Or use dynamic limit based on auth:
    @router.post("/ai/vision")
    @limiter.limit(rate_limit_tier("ai"))
    async def ai_vision(request: Request, ...):
        ...
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Callable

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Environment-based configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1").lower() not in ("0", "false", "no", "off")
RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE", "memory://")
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")

# Rate limit tiers (requests per minute)
RATE_LIMITS = {
    # Endpoint categories
    "default": RATE_LIMIT_DEFAULT,
    "public": "30/minute",        # Unauthenticated requests
    "authenticated": "60/minute", # Free tier users
    "pro": "300/minute",          # Pro tier users
    "ai": "10/minute",            # AI/vision endpoints (expensive)
    "cam": "20/minute",           # CNC/CAM export (computational)
    "upload": "10/minute",        # File uploads
    "export": "30/minute",        # Data exports
    "health": "1000/minute",      # Health checks (effectively unlimited)

    # Specific endpoint overrides
    "dxf_upload": "15/minute",
    "gcode_export": "20/minute",
    "ai_vision": "5/minute",
    "ai_explain": "10/minute",
}


# =============================================================================
# KEY FUNCTIONS
# =============================================================================

def get_client_key(request: Request) -> str:
    """
    Generate rate limit key based on client identity.

    Priority:
    1. Authenticated user ID (from JWT)
    2. API key (X-API-Key header)
    3. IP address (fallback)

    This ensures authenticated users get their own quota,
    while anonymous users share IP-based limits.
    """
    # Check for authenticated user (set by auth middleware)
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"

    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Hash the API key for privacy (first 8 chars of key as identifier)
        return f"apikey:{api_key[:8]}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


def get_tier_key(request: Request) -> str:
    """
    Get rate limit key with tier awareness.

    Pro users get higher limits, free users get standard limits.
    """
    base_key = get_client_key(request)

    # Check user tier (set by auth middleware)
    tier = getattr(request.state, "tier", "free")

    return f"{base_key}:tier:{tier}"


# =============================================================================
# LIMITER INSTANCE
# =============================================================================

# Create limiter with appropriate storage
if RATE_LIMIT_STORAGE.startswith("redis://"):
    # Production: Use Redis for distributed rate limiting
    try:
        from slowapi.util import get_remote_address
        limiter = Limiter(
            key_func=get_client_key,
            default_limits=[RATE_LIMIT_DEFAULT],
            storage_uri=RATE_LIMIT_STORAGE,
            enabled=RATE_LIMIT_ENABLED,
        )
        logger.info(f"Rate limiter initialized with Redis storage: {RATE_LIMIT_STORAGE}")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis, falling back to memory: {e}")
        limiter = Limiter(
            key_func=get_client_key,
            default_limits=[RATE_LIMIT_DEFAULT],
            enabled=RATE_LIMIT_ENABLED,
        )
else:
    # Development: Use in-memory storage
    limiter = Limiter(
        key_func=get_client_key,
        default_limits=[RATE_LIMIT_DEFAULT],
        enabled=RATE_LIMIT_ENABLED,
    )
    if RATE_LIMIT_ENABLED:
        logger.info("Rate limiter initialized with in-memory storage")
    else:
        logger.info("Rate limiter DISABLED (RATE_LIMIT_ENABLED=0)")


# =============================================================================
# HELPERS
# =============================================================================

def rate_limit_tier(tier: str) -> str:
    """
    Get rate limit string for a tier/category.

    Usage:
        @limiter.limit(rate_limit_tier("ai"))
        async def ai_endpoint(request: Request):
            ...

    Args:
        tier: One of: default, public, authenticated, pro, ai, cam, upload, export, health

    Returns:
        Rate limit string like "60/minute"
    """
    return RATE_LIMITS.get(tier, RATE_LIMIT_DEFAULT)


def dynamic_rate_limit(request: Request) -> str:
    """
    Dynamic rate limit based on user authentication and tier.

    Usage:
        @limiter.limit(dynamic_rate_limit)
        async def endpoint(request: Request):
            ...
    """
    # Check if authenticated
    if hasattr(request.state, "user_id") and request.state.user_id:
        # Check tier
        tier = getattr(request.state, "tier", "free")
        if tier == "pro":
            return RATE_LIMITS["pro"]
        return RATE_LIMITS["authenticated"]

    # Unauthenticated
    return RATE_LIMITS["public"]


# =============================================================================
# ERROR HANDLER
# =============================================================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with:
    - 429 status code
    - Retry-After header
    - Structured error details
    """
    # Parse the limit info
    limit_string = str(exc.detail) if exc.detail else "Rate limit exceeded"

    # Get retry-after from the exception if available
    retry_after = 60  # Default to 60 seconds

    response = JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. {limit_string}",
            "retry_after_seconds": retry_after,
            "documentation": "https://docs.theproductionshop.com/api/rate-limits",
        },
    )
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = limit_string

    # Log rate limit hit
    client_key = get_client_key(request)
    logger.warning(
        f"Rate limit exceeded: {client_key} on {request.url.path}",
        extra={
            "client_key": client_key,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return response


# =============================================================================
# EXEMPT PATHS
# =============================================================================

# Paths that should not be rate limited
EXEMPT_PATHS = {
    "/health",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/_starlette_static",
}


def should_exempt(request: Request) -> bool:
    """Check if request path should be exempt from rate limiting."""
    path = request.url.path

    # Exact matches
    if path in EXEMPT_PATHS:
        return True

    # Prefix matches (static files, docs)
    exempt_prefixes = ("/docs/", "/redoc/", "/_starlette_static/")
    if any(path.startswith(prefix) for prefix in exempt_prefixes):
        return True

    return False


# =============================================================================
# DECORATORS FOR COMMON PATTERNS
# =============================================================================

def limit_ai(func: Callable) -> Callable:
    """Decorator for AI endpoints (10/minute)."""
    return limiter.limit(rate_limit_tier("ai"))(func)


def limit_cam(func: Callable) -> Callable:
    """Decorator for CAM/CNC endpoints (20/minute)."""
    return limiter.limit(rate_limit_tier("cam"))(func)


def limit_upload(func: Callable) -> Callable:
    """Decorator for upload endpoints (10/minute)."""
    return limiter.limit(rate_limit_tier("upload"))(func)


def limit_export(func: Callable) -> Callable:
    """Decorator for export endpoints (30/minute)."""
    return limiter.limit(rate_limit_tier("export"))(func)
