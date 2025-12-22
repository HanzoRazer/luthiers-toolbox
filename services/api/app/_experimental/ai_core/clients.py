"""
DEPRECATED: Migrated to app.rmos.ai.clients

This is a compatibility shim. Import from canonical location instead.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core.clients import get_ai_client
    
    # New (canonical)
    from app.rmos.ai.clients import get_ai_client

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

from app.rmos.ai.clients import *  # noqa: F401, F403

__all__ = ["get_ai_client", "LLMClientAdapter"]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    warnings.warn(
        "Module 'app._experimental.ai_core.clients' is deprecated. "
        "Import from 'app.rmos.ai.clients' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_warn_once()
