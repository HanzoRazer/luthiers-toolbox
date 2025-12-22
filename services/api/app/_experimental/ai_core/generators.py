"""
DEPRECATED: Migrated to app.rmos.ai.generators

This is a compatibility shim. Import from canonical location instead.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core.generators import make_candidate_generator_for_request
    
    # New (canonical)
    from app.rmos.ai.generators import make_candidate_generator_for_request

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

from app.rmos.ai.generators import *  # noqa: F401, F403

__all__ = ["make_candidate_generator_for_request", "CandidateGenerator"]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    warnings.warn(
        "Module 'app._experimental.ai_core.generators' is deprecated. "
        "Import from 'app.rmos.ai.generators' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_warn_once()
