"""
Agentic Module - AI-assisted user guidance for luthier workflows.

This module provides intelligent, context-aware guidance to help users
navigate complex workflows. It implements the M1 (Advisory) mode of
the agentic system.

Components:
- spine: Core event processing, moment detection, and directive generation
- (future) actuators: M2 mode - automated actions

Architecture:
1. UI components emit AgentEventV1 events
2. Spine detects significant moments (ERROR, FINDING, HESITATION, etc.)
3. Policy engine generates AttentionDirectives based on UWSM
4. Coach Bubble UI displays directives to user
5. User feedback updates UWSM for personalization

Usage:
    from app.agentic.spine import detect_moments, decide

    # Detect moments from events
    moments = detect_moments(events)

    # Generate directive
    if moments:
        decision = decide(moments[0], uwsm=user_style)
        if decision.emit_directive:
            return decision.directive
"""

__version__ = "1.0.0"

# Re-export spine module
from . import spine

# Re-export commonly used items for convenience
from .spine import (
    # Core functions
    detect_moments,
    decide,
    load_events,
    group_by_session,
    run_shadow_replay,
    select_moment_with_grace,
    # Schemas
    AgentEventV1,
    DetectedMoment,
    AttentionDirective,
    PolicyDecision,
    UWSMSnapshot,
    # Constants
    IMPLEMENTED,
    MOMENT_PRIORITY,
    CRITICAL_MOMENTS,
)

__all__ = [
    "__version__",
    "spine",
    # Core functions
    "detect_moments",
    "decide",
    "load_events",
    "group_by_session",
    "run_shadow_replay",
    "select_moment_with_grace",
    # Schemas
    "AgentEventV1",
    "DetectedMoment",
    "AttentionDirective",
    "PolicyDecision",
    "UWSMSnapshot",
    # Constants
    "IMPLEMENTED",
    "MOMENT_PRIORITY",
    "CRITICAL_MOMENTS",
]
