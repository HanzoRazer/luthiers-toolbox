"""
Agentic Spine - Event-driven moment detection and directive generation.

The spine is the core processing pipeline for agentic features:
1. Events are collected from UI components (AgentEventV1)
2. Moments are detected from event patterns
3. Policy decisions determine what directive to show
4. Replay enables testing and analysis

Modules:
- schemas: Data models for events, moments, decisions
- moments: Moment detection from event sequences
- policy: UWSM-based directive generation
- replay: Event loading, grouping, and shadow replay

Usage:
    from app.agentic.spine import detect_moments, decide, load_events

    events = load_events(Path("events.jsonl"))
    moments = detect_moments(events)
    if moments:
        decision = decide(moments[0])
        if decision.emit_directive:
            print(decision.directive.title)
"""

__version__ = "1.0.0"

# Module is now implemented
IMPLEMENTED = True

# Re-export core functions
from .moments import detect_moments, IMPLEMENTED as MOMENTS_IMPLEMENTED
from .policy import decide, build_directive, IMPLEMENTED as POLICY_IMPLEMENTED
from .replay import (
    load_events,
    group_by_session,
    run_shadow_replay,
    select_moment_with_grace,
    is_critical_moment,
    export_events_jsonl,
    ReplayConfig,
    ReplayResult,
    IMPLEMENTED as REPLAY_IMPLEMENTED,
)

# Re-export schemas
from .schemas import (
    AgentEventV1,
    EventSource,
    SessionInfo,
    DetectedMoment,
    AttentionDirective,
    PolicyDecision,
    PolicyDiagnostic,
    UWSMSnapshot,
    UWSMDimensions,
    UWSMDimension,
    DEFAULT_UWSM,
    MOMENT_PRIORITY,
    CRITICAL_MOMENTS,
)

__all__ = [
    # Version
    "__version__",
    "IMPLEMENTED",
    # Moment detection
    "detect_moments",
    # Policy
    "decide",
    "build_directive",
    # Replay
    "load_events",
    "group_by_session",
    "run_shadow_replay",
    "select_moment_with_grace",
    "is_critical_moment",
    "export_events_jsonl",
    "ReplayConfig",
    "ReplayResult",
    # Schemas
    "AgentEventV1",
    "EventSource",
    "SessionInfo",
    "DetectedMoment",
    "AttentionDirective",
    "PolicyDecision",
    "PolicyDiagnostic",
    "UWSMSnapshot",
    "UWSMDimensions",
    "UWSMDimension",
    "DEFAULT_UWSM",
    "MOMENT_PRIORITY",
    "CRITICAL_MOMENTS",
]
