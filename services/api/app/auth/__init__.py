# services/api/app/auth/__init__.py
"""
Authentication module.

Provides Principal model and dependency injection for JWT/session auth.
"""

from .principal import Principal
from .deps import get_current_principal, require_roles

__all__ = ["Principal", "get_current_principal", "require_roles"]
