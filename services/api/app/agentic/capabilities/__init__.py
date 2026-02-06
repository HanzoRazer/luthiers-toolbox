"""
Agentic Capabilities Registry

Capability declarations for all tools that participate in agent orchestration.
Each tool (analyzer, CAM engine, etc.) publishes its capabilities here.

Usage:
    from app.agentic.capabilities import get_all_capabilities
    caps = get_all_capabilities()
    for cap in caps:
        print(f"{cap.tool_id}: {cap.actions}")
"""

from .tap_tone_analyzer import (
    TAP_TONE_ANALYZER,
    TAP_TONE_WOLF_DETECTOR,
    TAP_TONE_ODS_ANALYZER,
    TAP_TONE_CHLADNI_ANALYZER,
    TAP_TONE_CAPABILITIES,
    get_tap_tone_capabilities,
    get_capability_by_id as get_tap_tone_capability,
)

from ..contracts import ToolCapabilityV1


def get_all_capabilities() -> list[ToolCapabilityV1]:
    """
    Return all registered capabilities from all repos.

    This is the discovery endpoint for agent orchestration.
    """
    all_caps: list[ToolCapabilityV1] = []

    # Add tap_tone_pi capabilities
    all_caps.extend(get_tap_tone_capabilities())

    # Future: Add other repo capabilities
    # all_caps.extend(get_cam_capabilities())
    # all_caps.extend(get_vision_capabilities())

    return all_caps


def get_capability_by_id(tool_id: str) -> ToolCapabilityV1 | None:
    """
    Look up a specific capability by ID across all repos.
    """
    # Check tap_tone_pi
    cap = get_tap_tone_capability(tool_id)
    if cap:
        return cap

    # Future: Check other repos
    return None


__all__ = [
    # Registry
    "get_all_capabilities",
    "get_capability_by_id",
    # Tap Tone
    "TAP_TONE_ANALYZER",
    "TAP_TONE_WOLF_DETECTOR",
    "TAP_TONE_ODS_ANALYZER",
    "TAP_TONE_CHLADNI_ANALYZER",
    "TAP_TONE_CAPABILITIES",
    "get_tap_tone_capabilities",
]
