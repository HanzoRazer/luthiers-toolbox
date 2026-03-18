"""
Safety-critical function decorators and utilities.

DEPRECATED: Import from app.core.safety instead.

This module re-exports from app.core.safety for backward compatibility.
All new code should import directly from app.core.safety:

    from app.core.safety import safety_critical, is_safety_critical

Functions marked with @safety_critical are identified as having
direct impact on physical machine operations (G-code generation,
feeds/speeds calculation, feasibility decisions).

These functions:
1. Must never silently swallow exceptions
2. Are logged for audit purposes
3. Are tracked by fence_checker_v2 for coverage
"""

# Re-export from canonical location
from app.core.safety import safety_critical, is_safety_critical

__all__ = ["safety_critical", "is_safety_critical"]
