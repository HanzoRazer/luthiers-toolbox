"""
Authentication Router - User profile and tier management.

Endpoints:
- GET /api/auth/me - Get current user profile
- PATCH /api/auth/me - Update profile
- GET /api/auth/tier - Get tier info and features
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.auth.principal import Principal
from app.db.session import get_db


router = APIRouter(prefix="/api/auth", tags=["Auth"])


# =============================================================================
# Schemas
# =============================================================================

class UserProfileOut(BaseModel):
    """User profile response."""
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    tier: str
    tier_expires_at: Optional[str] = None
    preferences: dict

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update request."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


class FeatureOut(BaseModel):
    """Feature information."""
    feature_key: str
    display_name: str
    description: Optional[str] = None
    available: bool


class TierInfoOut(BaseModel):
    """Tier and feature information."""
    current_tier: str
    tier_expires_at: Optional[str] = None
    features: List[FeatureOut]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/me", response_model=UserProfileOut)
async def get_current_user(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    """Get current user's profile and tier information."""
    result = db.execute(
        text("""
            SELECT id, tier, tier_expires_at, display_name, avatar_url, preferences
            FROM user_profiles
            WHERE id = :user_id
        """),
        {"user_id": principal.user_id}
    ).fetchone()

    if not result:
        # Auto-create profile for new users
        db.execute(
            text("""
                INSERT INTO user_profiles (id, tier, display_name)
                VALUES (:user_id, 'free', :display_name)
                ON CONFLICT (id) DO NOTHING
            """),
            {"user_id": principal.user_id, "display_name": principal.email}
        )
        db.commit()

        return UserProfileOut(
            id=str(principal.user_id),
            email=principal.email,
            display_name=principal.email,
            avatar_url=None,
            tier="free",
            tier_expires_at=None,
            preferences={},
        )

    return UserProfileOut(
        id=str(result.id),
        email=principal.email,
        display_name=result.display_name,
        avatar_url=result.avatar_url,
        tier=result.tier,
        tier_expires_at=result.tier_expires_at.isoformat() if result.tier_expires_at else None,
        preferences=result.preferences or {},
    )


@router.patch("/me", response_model=UserProfileOut)
async def update_profile(
    updates: UserProfileUpdate,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    """Update current user's profile."""
    # Build dynamic update
    update_fields = []
    params = {"user_id": principal.user_id}

    if updates.display_name is not None:
        update_fields.append("display_name = :display_name")
        params["display_name"] = updates.display_name

    if updates.avatar_url is not None:
        update_fields.append("avatar_url = :avatar_url")
        params["avatar_url"] = updates.avatar_url

    if updates.preferences is not None:
        update_fields.append("preferences = :preferences")
        params["preferences"] = updates.preferences

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields.append("updated_at = NOW()")

    db.execute(
        text(f"""
            UPDATE user_profiles
            SET {', '.join(update_fields)}
            WHERE id = :user_id
        """),
        params
    )
    db.commit()

    return await get_current_user(principal, db)


@router.get("/tier", response_model=TierInfoOut)
async def get_tier_info(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> TierInfoOut:
    """Get current tier and available features."""
    # Get user's tier
    tier_result = db.execute(
        text("SELECT tier, tier_expires_at FROM user_profiles WHERE id = :user_id"),
        {"user_id": principal.user_id}
    ).fetchone()

    current_tier = tier_result.tier if tier_result else "free"
    tier_expires_at = tier_result.tier_expires_at if tier_result else None

    # Get all features with availability
    features = db.execute(
        text("""
            SELECT feature_key, display_name, description, min_tier, enabled
            FROM feature_flags
            WHERE enabled = TRUE
            ORDER BY feature_key
        """)
    ).fetchall()

    tier_levels = {"free": 0, "pro": 1}
    user_level = tier_levels.get(current_tier, 0)

    feature_list = [
        FeatureOut(
            feature_key=f.feature_key,
            display_name=f.display_name,
            description=f.description,
            available=user_level >= tier_levels.get(f.min_tier, 0),
        )
        for f in features
    ]

    return TierInfoOut(
        current_tier=current_tier,
        tier_expires_at=tier_expires_at.isoformat() if tier_expires_at else None,
        features=feature_list,
    )


@router.get("/health")
async def auth_health() -> dict:
    """Health check for auth service."""
    return {"status": "ok", "service": "auth"}
