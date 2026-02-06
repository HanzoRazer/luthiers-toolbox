"""
Agentic Layer — Luthier's ToolBox

Cross-repo coordination layer for agent orchestration.

This module provides:
1. Contracts: Shared schemas for cross-repo communication
2. Capabilities: Registry of what each tool can do
3. Events: Unified event vocabulary
4. UWSM: User preference model

Design principles:
- Contracts are the ONLY coupling between repos
- Privacy by default (UWSM is local-only, events respect layers)
- Safe defaults are explicit and auditable
- Event vocabulary is unified across all repos

Usage:
    from app.agentic import get_all_capabilities, ToolCapabilityV1
    from app.agentic.contracts import AttentionDirectiveV1, AgentEventV1
"""

__version__ = "1.0.0"

# Re-export contracts
from .contracts import (
    # Tool Capability
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
    # Analyzer Attention
    AttentionDirectiveV1,
    AttentionAction,
    FocusTarget,
    # Event Emission
    AgentEventV1,
    EventType,
    EventSource,
    # UWSM
    UWSMv1,
    PreferenceDimension,
    DecayConfig,
)

# Re-export capabilities
from .capabilities import (
    get_all_capabilities,
    get_capability_by_id,
    TAP_TONE_ANALYZER,
    TAP_TONE_CAPABILITIES,
)

__all__ = [
    # Contracts
    "ToolCapabilityV1",
    "CapabilityAction",
    "SafeDefaults",
    "AttentionDirectiveV1",
    "AttentionAction",
    "FocusTarget",
    "AgentEventV1",
    "EventType",
    "EventSource",
    "UWSMv1",
    "PreferenceDimension",
    "DecayConfig",
    # Capabilities
    "get_all_capabilities",
    "get_capability_by_id",
    "TAP_TONE_ANALYZER",
    "TAP_TONE_CAPABILITIES",
]
