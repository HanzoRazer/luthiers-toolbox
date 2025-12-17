from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Text, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class WorkflowSessionRow(Base):
    """
    Stores the entire WorkflowSession as JSON (text) for simplicity.
    This keeps the system lightweight and avoids complex relational schemas early.
    """
    __tablename__ = "workflow_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(64), nullable=False)

    state: Mapped[str] = mapped_column(String(64), nullable=False)

    # Serialized WorkflowSession JSON (Pydantic dict -> JSON string)
    session_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)