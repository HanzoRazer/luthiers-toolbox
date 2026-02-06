from __future__ import annotations
"""
Tiny tone generator for tests (float32 in [-1, 1]).
"""
import math
import numpy as np


def sine_tone(fs: int, dur_s: float, freq_hz: float, amp: float = 0.25, phase: float = 0.0) -> np.ndarray:
    """
    Generate a single-channel sine tone.
    - fs: sample rate (Hz)
    - dur_s: duration (seconds)
    - freq_hz: frequency (Hz)
    - amp: linear amplitude (<= 1.0)
    - phase: radians
    Returns float32 array in [-1, 1].
    """
    n = int(round(dur_s * fs))
    t = np.arange(n, dtype=np.float32) / float(fs)
    x = amp * np.sin(2.0 * np.pi * freq_hz * t + phase)
    return x.astype(np.float32, copy=False)


def rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float32)
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(x * x)))


def db(x_rms: float) -> float:
    if x_rms <= 0.0:
        return float("-inf")
    return 20.0 * math.log10(x_rms)
