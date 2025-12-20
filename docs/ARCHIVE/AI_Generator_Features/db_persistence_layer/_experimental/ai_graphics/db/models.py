"""
AI Graphics DB Models

SQLAlchemy ORM models for AI exploration session persistence.
Stores AiSessionState as JSON for flexibility while indexing key fields.

Follows pattern established in workflow/db/models.py.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Text, String, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AiSessionRow(Base):
    """
    Stores the entire AiSessionState as JSON for simplicity.
    Key fields are denormalized for indexing/filtering.

    Columns:
    - session_id (PK): Unique identifier
    - fingerprint_count: Number of explored designs
    - history_count: Number of suggestions in history
    - session_json: Full serialized AiSessionState
    """
    __tablename__ = "ai_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Summary counts for quick queries
    fingerprint_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    history_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    last_activity_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Full serialized AiSessionState JSON
    session_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_ai_sessions_last_activity", "last_activity_utc"),
    )


class AiSuggestionRow(Base):
    """
    Stores individual AI suggestions for history tracking.
    Denormalized from session_json for efficient querying.
    """
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    suggestion_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Scores
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_bucket: Mapped[str] = mapped_column(String(16), nullable=True)
    worst_ring_risk: Mapped[str] = mapped_column(String(16), nullable=True)

    # Timestamps
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_ai_suggestions_session_created", "session_id", "created_at_utc"),
        Index("ix_ai_suggestions_score", "overall_score"),
    )


class AiFingerprintRow(Base):
    """
    Stores explored fingerprints for deduplication.
    Normalized for efficient lookup.
    """
    __tablename__ = "ai_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Fingerprint components
    outer_diameter: Mapped[float] = mapped_column(Float, nullable=False)
    inner_diameter: Mapped[float] = mapped_column(Float, nullable=False)
    ring_widths_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Composite fingerprint hash for fast lookup
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Timestamp
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_ai_fingerprints_session_hash", "session_id", "fingerprint_hash"),
    )


class AiImageAssetRow(Base):
    """
    Stores AI-generated image assets for the Vision Engine.
    Tracks generation, review status, and attachments.
    """
    __tablename__ = "ai_image_assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # Image data
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # Prompt information
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    engineered_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str] = mapped_column(Text, nullable=True)

    # Provider and generation settings
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    quality: Mapped[str] = mapped_column(String(16), nullable=False)
    size: Mapped[str] = mapped_column(String(16), nullable=False)
    style: Mapped[str] = mapped_column(String(32), nullable=True)

    # Detected attributes
    category: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    body_shape: Mapped[str] = mapped_column(String(64), nullable=True)
    finish: Mapped[str] = mapped_column(String(64), nullable=True)

    # Review workflow
    status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False, index=True
    )  # pending, approved, rejected
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(64), nullable=True)
    reviewed_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Run attachment
    attached_to_run_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    attached_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cost tracking
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Timestamps
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Full metadata JSON (for extensibility)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_ai_images_status_created", "status", "created_at_utc"),
        Index("ix_ai_images_provider_category", "provider", "category"),
        Index("ix_ai_images_rating", "rating"),
    )
