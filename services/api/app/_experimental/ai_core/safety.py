"""
DEPRECATED: Split between app.ai.safety (policy) and app.rmos.ai.coercion (domain)

This is a compatibility shim. Domain coercion moved to app.rmos.ai.coercion.

Migration Path:
    # Old (deprecated)
    from app._experimental.ai_core.safety import coerce_to_rosette_spec
    
    # New (canonical)
    from app.rmos.ai.coercion import coerce_to_rosette_spec

For general AI safety policy, use: from app.ai.safety import ...

This shim will be removed in Wave 21 (January 2026).
"""

import warnings
from functools import lru_cache

# Domain coercion moved to RMOS namespace
from app.rmos.ai.coercion import *  # noqa: F401, F403

__all__ = ["coerce_to_rosette_spec"]


@lru_cache(maxsize=1)
def _warn_once() -> None:
    warnings.warn(
        "Module 'app._experimental.ai_core.safety' is deprecated. "
        "Import coerce_to_rosette_spec from 'app.rmos.ai.coercion' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_warn_once()
