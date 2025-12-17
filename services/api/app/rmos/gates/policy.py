"""
RMOS Replay Gate Policy

Defines policy for handling drift detection during replay.
Controls whether drift blocks fork acceptance or requires override.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any, List


GateMode = Literal["block", "soft_block"]


@dataclass(frozen=True)
class ReplayGatePolicy:
    """Configuration for replay gate behavior."""
    policy_id: str
    version: str
    mode: GateMode
    require_override_note_on_drift: bool


def get_replay_gate_policy() -> ReplayGatePolicy:
    """
    Get the active replay gate policy.
    
    Configured via environment variables:
    - RMOS_REPLAY_GATE_MODE: "block" | "soft_block"
    - RMOS_REPLAY_GATE_REQUIRE_NOTE: "true" | "false"
    """
    mode = os.getenv("RMOS_REPLAY_GATE_MODE", "block").lower()
    if mode not in ("block", "soft_block"):
        mode = "block"

    require_note = os.getenv("RMOS_REPLAY_GATE_REQUIRE_NOTE", "true").lower() == "true"

    return ReplayGatePolicy(
        policy_id="contract_driven_replay_gate",
        version="1.0.0",
        mode=mode,
        require_override_note_on_drift=require_note,
    )


def summarize_drift(drift: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize drift items into compact representation."""
    fields = [d.get("field") for d in drift if d.get("field")]
    return {
        "count": len(drift),
        "fields": sorted(set(fields)),
    }


def drift_requires_override(
    *,
    drift_detected: bool,
    require_note: bool,
    override_note: Optional[str],
) -> bool:
    """
    Determine if drift requires an override note.
    
    Returns True if:
    - Drift was detected AND
    - Policy requires override note AND
    - No override note was provided
    """
    if not drift_detected:
        return False
    if not require_note:
        return False
    return not (override_note and override_note.strip())
