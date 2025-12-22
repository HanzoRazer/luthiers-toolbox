"""
DEPRECATED: Migrated to app.rmos.ai.constraints

This is a compatibility shim. Import from canonical location instead.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core.generator_constraints import constraints_from_context
    
    # New (canonical)
    from app.rmos.ai.constraints import constraints_from_context

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

from app.rmos.ai.constraints import *  # noqa: F401, F403

__all__ = ["RosetteGeneratorConstraints", "constraints_from_context"]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    warnings.warn(
        "Module 'app._experimental.ai_core.generator_constraints' is deprecated. "
        "Import from 'app.rmos.ai.constraints' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_warn_once()
