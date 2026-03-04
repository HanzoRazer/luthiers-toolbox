"""
Authentication middleware for Site Generator API
Validates API keys and enforces rate limiting
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings


# Simple in-memory rate limiter (use Redis in production)
class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> tuple[bool, Optional[str]]:
        """Check if client has exceeded rate limit. Returns (allowed, error_message)"""
        if not settings.rate_limit_enabled:
            return True, None

        now = time.time()
        hour_ago = now - 3600

        # Clean old requests
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > hour_ago
        ]

        # Check limit
        if len(self._requests[client_id]) >= settings.rate_limit_per_hour:
            reset_time = datetime.fromtimestamp(
                self._requests[client_id][0] + 3600
            ).strftime("%H:%M:%S")
            return False, f"Rate limit exceeded. Resets at {reset_time}"

        # Record this request
        self._requests[client_id].append(now)
        return True, None

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client"""
        if not settings.rate_limit_enabled:
            return 999999
        return max(0, settings.rate_limit_per_hour - len(self._requests[client_id]))


rate_limiter = RateLimiter()
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[HTTPAuthorizationCredentials] = None
) -> str:
    """
    Verify API key from either X-API-Key header or Bearer token
    Returns the client identifier for rate limiting
    """
    api_key = None

    # Check X-API-Key header
    if x_api_key:
        api_key = x_api_key

    # Check Authorization: Bearer token
    elif authorization:
        api_key = authorization.credentials

    # Fail if no key provided
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via X-API-Key header or Authorization: Bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validate key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    # Rate limiting
    client_id = f"{api_key[:8]}_{request.client.host}"
    allowed, error_msg = rate_limiter.is_allowed(client_id)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=error_msg,
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_per_hour),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "3600"
            }
        )

    # Add rate limit headers to response (via middleware)
    request.state.rate_limit_remaining = rate_limiter.get_remaining(client_id)

    return client_id


async def optional_api_key(
    x_api_key: Optional[str] = Header(None)
) -> Optional[str]:
    """Optional API key for public endpoints like status checks"""
    return x_api_key
