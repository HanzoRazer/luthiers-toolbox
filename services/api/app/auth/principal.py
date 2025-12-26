# services/api/app/auth/principal.py
"""
Principal - authenticated user identity.

Single source of truth for user identity and role membership.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set


@dataclass(frozen=True)
class Principal:
    """
    Authenticated user principal.

    Immutable identity record extracted from JWT or session.
    """

    user_id: str
    roles: Set[str]
    email: Optional[str] = None

    def has_any_role(self, allowed: Iterable[str]) -> bool:
        """Check if principal has any of the allowed roles (case-insensitive)."""
        allowed_set = set(r.lower() for r in allowed)
        return any(r.lower() in allowed_set for r in self.roles)

    def has_role(self, role: str) -> bool:
        """Check if principal has a specific role (case-insensitive)."""
        return role.lower() in {r.lower() for r in self.roles}

    @property
    def is_admin(self) -> bool:
        """Check if principal has admin role."""
        return self.has_role("admin")

    @property
    def is_operator(self) -> bool:
        """Check if principal has operator role."""
        return self.has_role("operator")

    @property
    def is_engineer(self) -> bool:
        """Check if principal has engineer role."""
        return self.has_role("engineer")
