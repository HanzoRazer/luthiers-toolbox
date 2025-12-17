"""
SQLAlchemy declarative base for Luthier's ToolBox.

All ORM models inherit from this Base class.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy ORM base class for all models."""
    pass
