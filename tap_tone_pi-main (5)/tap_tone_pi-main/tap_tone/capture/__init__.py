"""tap_tone.capture subpackage — audio capture utilities."""
from __future__ import annotations

from .auto_trigger import (
    AutoTriggerConfig,
    AutoTriggerDetector,
    AutoTriggerResult,
    TriggerMetrics,
    RingBuffer,
    capture_one_impulse,
    capture_one_impulse_from_stream,
)

__all__ = [
    "AutoTriggerConfig",
    "AutoTriggerDetector",
    "AutoTriggerResult",
    "TriggerMetrics",
    "RingBuffer",
    "capture_one_impulse",
    "capture_one_impulse_from_stream",
]
