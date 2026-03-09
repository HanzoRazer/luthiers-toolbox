"""
UserProfile model - extends Supabase auth.users.

Stores subscription tier and user preferences.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class UserProfile(Base):
    """
    User profile extending Supabase auth.users.

    Links to auth.users via id (UUID).
    Stores subscription tier, preferences, and billing info.
    """
    __tablename__ = "user_profiles"

    # Primary key - matches Supabase auth.users.id
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    # Subscription tier
    tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )
    tier_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
    )
    tier_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Profile metadata
    display_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Billing (for Stripe integration)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    # User preferences (stored as JSON)
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "tier IN ('free', 'pro')",
            name="tier_check",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserProfile {self.id} tier={self.tier}>"
