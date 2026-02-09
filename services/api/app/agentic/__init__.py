# Agentic module - M1 Advisory Mode spine implementation
"""
Agentic Layer - Cross-Repo Coordination

This module provides contracts and capabilities for agent orchestration.
"""

# Re-export contracts
from .contracts import (
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
    AttentionDirectiveV1,
    AttentionAction,
    FocusTarget,
    AgentEventV1,
    EventType,
    EventSource,
    UWSMv1,
    PreferenceDimension,
    DecayConfig,
)

# Re-export capabilities
from .capabilities import (
    get_all_capabilities,
    get_capability_by_id,
    TAP_TONE_ANALYZER,
    TAP_TONE_WOLF_DETECTOR,
    TAP_TONE_ODS_ANALYZER,
    TAP_TONE_CHLADNI_ANALYZER,
)

__all__ = [
    "ToolCapabilityV1", "CapabilityAction", "SafeDefaults",
    "AttentionDirectiveV1", "AttentionAction", "FocusTarget",
    "AgentEventV1", "EventType", "EventSource",
    "UWSMv1", "PreferenceDimension", "DecayConfig",
    "get_all_capabilities", "get_capability_by_id",
    "TAP_TONE_ANALYZER", "TAP_TONE_WOLF_DETECTOR", "TAP_TONE_ODS_ANALYZER", "TAP_TONE_CHLADNI_ANALYZER",
]
