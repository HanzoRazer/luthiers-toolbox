"""
Agentic Layer Contracts

Cross-repo contracts for the agentic coordination layer.
These contracts define the "thin waist" between:
- Tool repos (tap_tone_pi, CAM engines, etc.)
- Experience shell (ToolBox UI)
- Agent orchestration

Design principles:
1. Contracts are the ONLY coupling between repos
2. Tools expose capabilities, not implementation
3. Events use a unified vocabulary
4. Attention directives are presentation-level, not computational

Version: 1.0.0
"""

from .tool_capability import (
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
)

from .analyzer_attention import (
    AttentionDirectiveV1,
    AttentionAction,
    FocusTarget,
)

from .event_emission import (
    AgentEventV1,
    EventType,
    EventSource,
)

from .uwsm import (
    UWSMv1,
    PreferenceDimension,
    DecayConfig,
)

__all__ = [
    # Tool Capability
    "ToolCapabilityV1",
    "CapabilityAction",
    "SafeDefaults",
    # Analyzer Attention
    "AttentionDirectiveV1",
    "AttentionAction",
    "FocusTarget",
    # Event Emission
    "AgentEventV1",
    "EventType",
    "EventSource",
    # UWSM
    "UWSMv1",
    "PreferenceDimension",
    "DecayConfig",
]
