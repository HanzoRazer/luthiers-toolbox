"""
DEPRECATED: Migrated to app.rmos.ai.structured_generator

This is a compatibility shim. Import from canonical location instead.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core.structured_generator import generate_constrained_candidate
    
    # New (canonical)
    from app.rmos.ai.structured_generator import generate_constrained_candidate

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

from app.rmos.ai.structured_generator import *  # noqa: F401, F403

__all__ = ["generate_constrained_candidate"]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    warnings.warn(
        "Module 'app._experimental.ai_core.structured_generator' is deprecated. "
        "Import from 'app.rmos.ai.structured_generator' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_warn_once()
