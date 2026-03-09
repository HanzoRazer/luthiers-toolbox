"""
FeatureFlag model - tier-based feature access control.

Defines which features are available at each subscription tier.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, Integer, DateTime, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class FeatureFlag(Base):
    """
    Feature flag for tier-based access control.

    Defines feature availability per subscription tier.
    """
    __tablename__ = "feature_flags"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Feature identifier
    feature_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    # Display info
    display_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Tier requirements
    min_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )

    # Override flags
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    rollout_percentage: Mapped[int] = mapped_column(
        Integer,
        default=100,
        server_default="100",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "min_tier IN ('free', 'pro')",
            name="min_tier_check",
        ),
        CheckConstraint(
            "rollout_percentage BETWEEN 0 AND 100",
            name="rollout_check",
        ),
    )

    def __repr__(self) -> str:
        return f"<FeatureFlag {self.feature_key} min_tier={self.min_tier}>"

    def is_available_for_tier(self, tier: str) -> bool:
        """Check if feature is available for a given tier."""
        if not self.enabled:
            return False

        tier_levels = {"free": 0, "pro": 1}
        user_level = tier_levels.get(tier, 0)
        required_level = tier_levels.get(self.min_tier, 0)

        return user_level >= required_level
