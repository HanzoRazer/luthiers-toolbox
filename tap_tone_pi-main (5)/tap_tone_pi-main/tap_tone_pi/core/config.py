"""Configuration dataclasses for capture and analysis.

Migration
---------
    # Old import (deprecated)
    from tap_tone.config import CaptureConfig, AnalysisConfig
    
    # New import (v2.0.0+)
    from tap_tone_pi.core.config import CaptureConfig, AnalysisConfig
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureConfig:
    """Audio capture configuration."""
    device: int | None = None
    sample_rate: int = 48000
    channels: int = 1
    seconds: float = 2.5


@dataclass(frozen=True)
class AnalysisConfig:
    """FFT analysis configuration."""
    highpass_hz: float = 20.0
    peak_min_hz: float = 40.0
    peak_max_hz: float = 2000.0
    peak_min_prominence: float = 0.05  # relative (0..1 scaled)
    peak_min_spacing_hz: float = 10.0
    max_peaks: int = 12
