# services/api/app/auth/deps.py
"""
Authentication dependencies for FastAPI.

Supports:
- JWT Bearer (Authorization: Bearer ...)
- Session cookie (server-side session)
- Legacy header-based auth (x-user-role, x-user-id) for dev/testing

Configure via environment variables:
- AUTH_MODE: "jwt", "session", "header", or "hybrid" (default: "header" for dev)

JWT Configuration (when AUTH_MODE includes jwt):
- JWT_SECRET: shared secret for HS256
- JWT_PUBLIC_KEY_PEM: public key for RS256 (alternative to JWT_SECRET)
- JWT_ALG: algorithm, auto-detected from which key is set (HS256 or RS256)
- JWT_AUDIENCE: optional audience claim to verify
- JWT_ISSUER: optional issuer claim to verify
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .principal import Principal

# Auth mode configuration
AUTH_MODE = os.getenv("AUTH_MODE", "header").lower()

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_PUBLIC_KEY_PEM = os.getenv("JWT_PUBLIC_KEY_PEM", "")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "")
JWT_ISSUER = os.getenv("JWT_ISSUER", "")

# HTTPBearer for JWT extraction (auto_error=False to allow fallback)
bearer = HTTPBearer(auto_error=False)


# =============================================================================
# JWT Decode Implementation
# =============================================================================

def decode_and_verify_jwt(token: str) -> Dict[str, Any]:
    """
    Decode and verify JWT token.

    Supports:
    - HS256 with JWT_SECRET (shared secret)
    - RS256 with JWT_PUBLIC_KEY_PEM (public key)

    Auto-detects algorithm based on which env var is set.
    """
    try:
        import jwt
        from jwt import PyJWTError
    except ImportError:
        raise HTTPException(status_code=500, detail="PyJWT not installed")

    # Determine key and algorithm
    if JWT_PUBLIC_KEY_PEM:
        key = JWT_PUBLIC_KEY_PEM
        algorithm = "RS256"
    elif JWT_SECRET:
        key = JWT_SECRET
        algorithm = os.getenv("JWT_ALG", "HS256")
    else:
        raise HTTPException(status_code=500, detail="JWT not configured (set JWT_SECRET or JWT_PUBLIC_KEY_PEM)")

    try:
        options = {"verify_aud": bool(JWT_AUDIENCE)}
        return jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=JWT_AUDIENCE or None,
            issuer=JWT_ISSUER or None,
            options=options,
        )
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _principal_from_claims(claims: Dict[str, Any]) -> Principal:
    """Extract Principal from JWT claims.

    Supports common claim shapes:
    - sub or user_id for user identity
    - roles: ["admin", "operator"] (list)
    - roles: "operator" (string, coerced to set)
    - role: "operator" (singular form)
    """
    user_id = str(claims.get("sub") or claims.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="JWT missing subject")

    # Normalize roles claim - handle None, string, or list
    roles_raw = claims.get("roles") or claims.get("role")
    if roles_raw is None:
        roles_raw = []
    if isinstance(roles_raw, str):
        roles = {roles_raw.lower()}
    elif isinstance(roles_raw, list):
        roles = {str(r).lower() for r in roles_raw if r}
    else:
        roles = set()

    email = claims.get("email")
    return Principal(user_id=user_id, roles=roles, email=email)


# =============================================================================
# Swap Point B: Session Load
# =============================================================================

def load_user_from_session(request: Request) -> Optional[Principal]:
    """
    Load Principal from server-side session.

    Implement with your session middleware (Starlette SessionMiddleware, etc).
    Returns Principal if session authenticated, None otherwise.

    Example implementation:
        sess = getattr(request, "session", None)
        if not sess:
            return None
        user_id = sess.get("user_id")
        roles = sess.get("roles") or []
        if not user_id:
            return None
        if isinstance(roles, str):
            roles = [roles]
        return Principal(user_id=str(user_id), roles={r.lower() for r in roles})
    """
    # Default: check for Starlette session
    sess = getattr(request, "session", None)
    if not sess:
        return None

    user_id = sess.get("user_id")
    roles = sess.get("roles") or []
    if not user_id:
        return None

    if isinstance(roles, str):
        roles = [roles]
    return Principal(user_id=str(user_id), roles={r.lower() for r in roles})


# =============================================================================
# Legacy Header-Based Auth (for dev/testing)
# =============================================================================

def _principal_from_headers(request: Request) -> Optional[Principal]:
    """
    Extract Principal from legacy headers (x-user-role, x-user-id).

    Used for development and testing when JWT/session not configured.
    """
    role = (request.headers.get("x-user-role") or "").strip().lower()
    user_id = (request.headers.get("x-user-id") or "").strip()

    if not role and not user_id:
        return None

    roles: set[str] = set()
    if role and role not in ("anonymous", ""):
        roles.add(role)

    return Principal(
        user_id=user_id or "anonymous",
        roles=roles,
        email=None,
    )


# =============================================================================
# Main Principal Extractor
# =============================================================================

async def get_current_principal(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> Principal:
    """
    Extract authenticated Principal from request.

    Tries authentication methods in order based on AUTH_MODE:
    - "jwt": JWT Bearer only
    - "session": Session cookie only
    - "header": Legacy headers only (for dev)
    - "hybrid": Try JWT -> session -> headers (default for flexibility)
    """
    mode = AUTH_MODE

    # 1) Try JWT if enabled
    if mode in ("jwt", "hybrid"):
        if creds and creds.scheme.lower() == "bearer" and creds.credentials:
            try:
                claims = decode_and_verify_jwt(creds.credentials)
                return _principal_from_claims(claims)
            except HTTPException:
                if mode == "jwt":
                    raise  # JWT-only mode: fail on invalid token
                # Hybrid mode: continue to fallback
            except Exception:
                if mode == "jwt":
                    raise HTTPException(status_code=401, detail="Invalid token")
                # Hybrid mode: continue to fallback

    # 2) Try session if enabled
    if mode in ("session", "hybrid"):
        principal = load_user_from_session(request)
        if principal:
            return principal

    # 3) Try legacy headers if enabled
    if mode in ("header", "hybrid"):
        principal = _principal_from_headers(request)
        if principal:
            return principal

    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_optional_principal(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> Optional[Principal]:
    """
    Extract Principal if authenticated, None otherwise.

    Does not raise 401 - useful for optional auth endpoints.
    """
    try:
        return await get_current_principal(request, creds)
    except HTTPException:
        return None


# =============================================================================
# RBAC Gate Factory
# =============================================================================

def require_roles(*allowed_roles: str) -> Callable[..., Principal]:
    """
    Dependency factory for role-based access control.

    Usage:
        @router.post("/promote")
        def promote(principal: Principal = Depends(require_roles("admin", "operator", "engineer"))):
            ...

    Returns:
        FastAPI dependency that extracts and validates Principal.
        Raises 401 if not authenticated, 403 if insufficient role.
    """

    async def _gate(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.has_any_role(allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role. Required: {', '.join(allowed_roles)}",
            )
        return principal

    return _gate


def require_admin() -> Callable[..., Principal]:
    """Convenience: require admin role."""
    return require_roles("admin")


def require_operator() -> Callable[..., Principal]:
    """Convenience: require operator or admin role."""
    return require_roles("admin", "operator")


def require_engineer() -> Callable[..., Principal]:
    """Convenience: require engineer, operator, or admin role."""
    return require_roles("admin", "operator", "engineer")
