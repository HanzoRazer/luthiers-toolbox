"""
Supabase Authentication Provider.

Validates Supabase JWTs and extracts Principal information.
Integrates with existing Principal model and role system.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import HTTPException

from .principal import Principal


# Supabase configuration (loaded from environment)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def is_supabase_configured() -> bool:
    """Check if Supabase is properly configured."""
    return bool(SUPABASE_URL and SUPABASE_JWT_SECRET)


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decode and verify a Supabase JWT.

    Supabase JWT structure:
    {
        "aud": "authenticated",
        "exp": 1234567890,
        "sub": "user-uuid",
        "email": "user@example.com",
        "role": "authenticated",
        "app_metadata": { "roles": [...] },
        "user_metadata": { ... }
    }

    Returns:
        Dict of JWT claims

    Raises:
        HTTPException: 401 for invalid/expired token, 500 for config issues
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Supabase JWT secret not configured"
        )

    try:
        import jwt
        from jwt import PyJWTError
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PyJWT not installed - run: pip install PyJWT"
        )

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def principal_from_supabase_claims(claims: Dict[str, Any]) -> Principal:
    """
    Extract Principal from Supabase JWT claims.

    Maps Supabase claims to existing Principal model:
    - sub -> user_id
    - app_metadata.roles -> roles (or default to 'user')
    - email -> email

    Returns:
        Principal instance

    Raises:
        HTTPException: 401 if JWT missing required claims
    """
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="JWT missing subject")

    email = claims.get("email")

    # Extract roles from app_metadata (set via Supabase admin API or RLS)
    app_metadata = claims.get("app_metadata", {})
    roles_raw = app_metadata.get("roles", [])

    # Normalize roles to set
    if isinstance(roles_raw, str):
        roles = {roles_raw.lower()}
    elif isinstance(roles_raw, list):
        roles = {str(r).lower() for r in roles_raw if r}
    else:
        roles = set()

    # Default role if none specified
    if not roles:
        roles = {"user"}

    return Principal(
        user_id=user_id,
        roles=roles,
        email=email,
    )


async def get_user_tier(user_id: str, db_session) -> str:
    """
    Fetch user's subscription tier from database.

    Args:
        user_id: UUID of the user
        db_session: SQLAlchemy session

    Returns:
        Tier string: 'free' or 'pro'
    """
    from sqlalchemy import text

    result = db_session.execute(
        text("SELECT tier FROM user_profiles WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    return result[0] if result else "free"


def check_feature_access(tier: str, feature_key: str, db_session) -> bool:
    """
    Check if a tier has access to a feature.

    Args:
        tier: User's current tier ('free' or 'pro')
        feature_key: Feature identifier
        db_session: SQLAlchemy session

    Returns:
        True if user can access the feature
    """
    from sqlalchemy import text

    result = db_session.execute(
        text("""
            SELECT enabled, min_tier
            FROM feature_flags
            WHERE feature_key = :feature_key
        """),
        {"feature_key": feature_key}
    ).fetchone()

    if not result:
        return False

    enabled, min_tier = result
    if not enabled:
        return False

    # Tier hierarchy: pro > free
    tier_levels = {"free": 0, "pro": 1}
    return tier_levels.get(tier, 0) >= tier_levels.get(min_tier, 0)
