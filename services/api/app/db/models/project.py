"""
Project model - user-owned instrument design projects.

Stores project data with RLS for user isolation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class Project(Base):
    """
    User project for instrument design/manufacturing.

    Stores flexible JSON data with optional instrument type classification.
    Uses RLS policies for user data isolation.
    """
    __tablename__ = "projects"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Owner reference (FK to auth.users handled in migration)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Project metadata
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    instrument_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Flexible data storage
    data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
    )

    # Features used in this project (for tier validation)
    features_used: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
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
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("idx_projects_owner", "owner_id"),
        Index("idx_projects_instrument", "instrument_type"),
    )

    def __repr__(self) -> str:
        return f"<Project {self.id} name={self.name!r}>"

    @property
    def is_archived(self) -> bool:
        """Check if project is archived."""
        return self.archived_at is not None
