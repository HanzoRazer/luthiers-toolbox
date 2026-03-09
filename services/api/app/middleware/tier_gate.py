"""
Tier Gate Middleware - Enforce feature access based on subscription tier.

Provides dependency factories for tier-gated and feature-gated endpoints.

Usage:
    @router.get("/ai-vision")
    async def ai_vision(
        principal: Principal = Depends(require_feature("ai_vision"))
    ):
        ...

    @router.get("/pro-dashboard")
    async def pro_dash(
        principal: Principal = Depends(require_tier("pro"))
    ):
        ...
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.auth.principal import Principal
from app.db.session import get_db


# Tier hierarchy: pro > free
TIER_LEVELS = {"free": 0, "pro": 1}


async def _get_user_tier(user_id: str, db: Session) -> str:
    """Fetch user's subscription tier from database."""
    result = db.execute(
        text("SELECT tier FROM user_profiles WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    return result.tier if result else "free"


async def _check_feature_access(tier: str, feature_key: str, db: Session) -> bool:
    """Check if a tier has access to a feature."""
    result = db.execute(
        text("""
            SELECT enabled, min_tier
            FROM feature_flags
            WHERE feature_key = :feature_key
        """),
        {"feature_key": feature_key}
    ).fetchone()

    if not result:
        return False

    enabled, min_tier = result.enabled, result.min_tier
    if not enabled:
        return False

    user_level = TIER_LEVELS.get(tier, 0)
    required_level = TIER_LEVELS.get(min_tier, 0)

    return user_level >= required_level


def require_feature(feature_key: str) -> Callable[..., Principal]:
    """
    Dependency factory for feature-gated endpoints.

    Usage:
        @router.post("/batch-process")
        async def batch(
            principal: Principal = Depends(require_feature("batch_processing"))
        ):
            ...

    Raises:
        401 if not authenticated
        403 if user's tier doesn't have access to the feature
    """

    async def _gate(
        principal: Principal = Depends(get_current_principal),
        db: Session = Depends(get_db),
    ) -> Principal:
        tier = await _get_user_tier(principal.user_id, db)

        if not await _check_feature_access(tier, feature_key, db):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "feature_not_available",
                    "feature": feature_key,
                    "current_tier": tier,
                    "required_tier": "pro",
                    "upgrade_url": "/upgrade",
                    "message": f"Feature '{feature_key}' requires Pro tier",
                },
            )

        return principal

    return _gate


def require_tier(min_tier: str) -> Callable[..., Principal]:
    """
    Dependency factory for tier-gated endpoints.

    Usage:
        @router.get("/pro-dashboard")
        async def pro_dash(
            principal: Principal = Depends(require_tier("pro"))
        ):
            ...

    Raises:
        401 if not authenticated
        403 if user's tier is insufficient
    """
    required_level = TIER_LEVELS.get(min_tier, 0)

    async def _gate(
        principal: Principal = Depends(get_current_principal),
        db: Session = Depends(get_db),
    ) -> Principal:
        tier = await _get_user_tier(principal.user_id, db)
        user_level = TIER_LEVELS.get(tier, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "tier_required",
                    "current_tier": tier,
                    "required_tier": min_tier,
                    "upgrade_url": "/upgrade",
                    "message": f"This feature requires {min_tier.title()} tier",
                },
            )

        return principal

    return _gate


# Convenience decorators for common tiers
require_pro = require_tier("pro")
