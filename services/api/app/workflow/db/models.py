"""
Workflow DB Models

SQLAlchemy ORM models for workflow session persistence.
Stores WorkflowSession as JSON for flexibility while indexing key fields.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Text, String, DateTime, Integer, Column
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class WorkflowSessionRow(Base):
    """
    Stores the entire WorkflowSession as JSON (text) for simplicity.
    This keeps the system lightweight and avoids complex relational schemas early.

    Key fields are denormalized for indexing/filtering:
    - session_id (PK)
    - mode (design_first, constraint_first, ai_assisted)
    - state (draft, approved, rejected, etc.)
    - tool_id, material_id, machine_id (from index_meta)
    """
    __tablename__ = "workflow_sessions"
    id = Column(Integer, primary_key=True)

    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)

    # Serialized WorkflowSession JSON (Pydantic dict -> JSON string)
    session_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Denormalized index fields from index_meta
    tool_id: Mapped[str] = mapped_column(String(128), nullable=True)
    material_id: Mapped[str] = mapped_column(String(128), nullable=True)
    machine_id: Mapped[str] = mapped_column(String(128), nullable=True)

    # Candidate loop counter (for AI/constraint-first modes)
    candidate_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
