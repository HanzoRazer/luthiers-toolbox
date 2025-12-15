# services/api/app/api/deps.py
"""
API Dependencies - FastAPI dependency injection helpers.
Provides database sessions, authentication, and common dependencies.
"""

from __future__ import annotations

from typing import Any, Generator, Optional


def get_db_session() -> Generator[Any, None, None]:
    """
    Dependency that provides a database session.
    
    Currently a stub - returns None until database is configured.
    
    Usage:
        @router.get("/items")
        def list_items(db = Depends(get_db_session)):
            ...
    """
    # TODO: Implement actual database session when SQLAlchemy is configured
    yield None


def get_current_user() -> Optional[dict]:
    """
    Dependency that returns the current authenticated user.
    
    Currently a stub - returns None (anonymous) until auth is configured.
    
    Usage:
        @router.get("/profile")
        def get_profile(user = Depends(get_current_user)):
            ...
    """
    # TODO: Implement actual auth when user system is configured
    return None


def get_optional_user() -> Optional[dict]:
    """
    Dependency for optional authentication.
    Returns user if authenticated, None otherwise.
    """
    return None


class Pagination:
    """Pagination parameters dependency."""
    
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = max(0, skip)
        self.limit = min(1000, max(1, limit))


def get_pagination(skip: int = 0, limit: int = 100) -> Pagination:
    """Dependency for pagination parameters."""
    return Pagination(skip=skip, limit=limit)
