"""
RMOS Runs v2 DB Models

SQLAlchemy ORM models for RunArtifact persistence.
Stores RunArtifact as JSON for flexibility while indexing key fields.

Follows pattern established in workflow/db/models.py.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Text, String, DateTime, Float, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunArtifactRow(Base):
    """
    Stores the entire RunArtifact as JSON (text) for simplicity.
    Key fields are denormalized for indexing/filtering.

    Columns:
    - run_id (PK): Unique identifier
    - status: OK, BLOCKED, ERROR
    - mode: saw, router, cam, etc.
    - risk_level: GREEN, YELLOW, RED, UNKNOWN, ERROR
    - tool_id, material_id, machine_id: Context fields for filtering
    - workflow_session_id: Parent workflow session (if any)
    - score: Numeric feasibility score (0-100)
    - artifact_json: Full serialized RunArtifact
    """
    __tablename__ = "run_artifacts"

    # Primary key
    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Core fields (indexed for queries)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # Timestamps
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Context fields (indexed for filtering)
    tool_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    material_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    machine_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    workflow_session_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # Score for range queries
    score: Mapped[float] = mapped_column(Float, nullable=True)

    # Hashes for integrity verification
    feasibility_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    toolpaths_sha256: Mapped[str] = mapped_column(String(64), nullable=True)
    gcode_sha256: Mapped[str] = mapped_column(String(64), nullable=True)

    # Explanation tracking
    explanation_status: Mapped[str] = mapped_column(String(16), default="NONE", nullable=False)
    has_advisory_inputs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Full serialized RunArtifact JSON
    artifact_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_runs_status_created", "status", "created_at_utc"),
        Index("ix_runs_mode_risk", "mode", "risk_level"),
        Index("ix_runs_tool_material", "tool_id", "material_id"),
        Index("ix_runs_session_created", "workflow_session_id", "created_at_utc"),
    )


class AdvisoryAttachmentRow(Base):
    """
    Junction table linking RunArtifacts to Advisory assets.
    Supports the append-only advisory_inputs pattern.
    """
    __tablename__ = "run_advisory_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    advisory_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=True)
    engine_id: Mapped[str] = mapped_column(String(64), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=True)

    __table_args__ = (
        Index("ix_advisory_run_id", "run_id"),
        Index("ix_advisory_advisory_id", "advisory_id"),
    )
