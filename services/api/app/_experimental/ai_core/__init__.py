"""
DEPRECATED: This module has been migrated to app.rmos.ai

This is a compatibility shim. All exports now come from the canonical location.
Please update your imports to use 'from app.rmos.ai import ...' instead.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core import make_candidate_generator_for_request
    
    # New (canonical)
    from app.rmos.ai import make_candidate_generator_for_request

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

# Re-export everything from canonical location
from app.rmos.ai import *  # noqa: F401, F403

__all__ = [
    "make_candidate_generator_for_request",
    "generate_constrained_candidate",
    "coerce_to_rosette_spec",
    "constraints_from_context",
    "get_ai_client",
]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    """Emit deprecation warning only once per process."""
    warnings.warn(
        "Module 'app._experimental.ai_core' is deprecated. "
        "Please import from 'app.rmos.ai' instead. "
        "This shim will be removed in Wave 21 (January 2026).",
        DeprecationWarning,
        stacklevel=3,
    )


# Trigger warning on first import
_warn_once()
