"""Canonical WAV I/O utilities (single source of truth).

Why this exists
---------------
Historically, multiple scripts performed their own WAV read/write and int16↔float scaling.
That causes subtle amplitude/normalization drift and increases maintenance cost.

Policy
------
- All readers return float32 in [-1, 1] (best effort).
- All writers accept float32 in [-1, 1] and write PCM int16 by default.
- Any direct usage of scipy.io.wavfile.read/write outside this module should be treated as a bug.

Notes
-----
- Stereo handling is explicit:
  - read_wav_mono(): if 2ch, uses channel 0 by default (policy can be changed later).
  - read_wav_2ch(): if mono, duplicates channel to (ref, roving).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
from scipy.io import wavfile


@dataclass(frozen=True)
class WavMeta:
    sample_rate: int
    dtype: str
    num_channels: int
    num_samples: int


def _to_float32(x: np.ndarray) -> np.ndarray:
    """Convert PCM integer or float arrays to float32 ~[-1, 1]."""
    if np.issubdtype(x.dtype, np.floating):
        y = x.astype(np.float32, copy=False)
        # If already in [-1,1] keep; else scale by max abs.
        m = float(np.max(np.abs(y))) if y.size else 0.0
        if m <= 1.0 + 1e-6 or m == 0.0:
            return y
        return (y / m).astype(np.float32)

    # Integer PCM normalization
    if x.dtype == np.int16:
        return (x.astype(np.float32) / 32768.0)
    if x.dtype == np.int32:
        # common 24-bit packed into 32-bit, or true 32-bit PCM
        return (x.astype(np.float32) / 2147483648.0)
    if x.dtype == np.uint8:
        # 8-bit unsigned PCM (0..255) with 128 bias
        return ((x.astype(np.float32) - 128.0) / 128.0)

    # Fallback for other integer widths
    info = np.iinfo(x.dtype)
    denom = float(max(abs(info.min), info.max))
    return (x.astype(np.float32) / denom)


def read_wav_mono(path: str | Path) -> Tuple[np.ndarray, WavMeta]:
    """Read WAV and return mono float32 signal + metadata.

    If file is multi-channel, channel 0 is used (policy).
    """
    fs, x = wavfile.read(str(path))
    x_f = _to_float32(np.asarray(x))
    if x_f.ndim == 2:
        num_channels = int(x_f.shape[1])
        x_m = x_f[:, 0]
    else:
        num_channels = 1
        x_m = x_f
    meta = WavMeta(
        sample_rate=int(fs),
        dtype=str(np.asarray(x).dtype),
        num_channels=num_channels,
        num_samples=int(x_m.shape[0]),
    )
    return x_m.astype(np.float32, copy=False), meta


def read_wav_2ch(path: str | Path) -> Tuple[np.ndarray, np.ndarray, WavMeta]:
    """Read WAV and return (ref, roving) float32 signals + metadata.

    If file is mono, duplicates channel.
    If file has >2 channels, uses channels 0 and 1 (policy).
    """
    fs, x = wavfile.read(str(path))
    x_f = _to_float32(np.asarray(x))
    if x_f.ndim == 1:
        ref = x_f
        rov = x_f.copy()
        num_channels = 1
        n = int(x_f.shape[0])
    else:
        num_channels = int(x_f.shape[1])
        ref = x_f[:, 0]
        rov = x_f[:, 1] if x_f.shape[1] > 1 else x_f[:, 0]
        n = int(x_f.shape[0])
    meta = WavMeta(
        sample_rate=int(fs),
        dtype=str(np.asarray(x).dtype),
        num_channels=num_channels,
        num_samples=n,
    )
    return ref.astype(np.float32, copy=False), rov.astype(np.float32, copy=False), meta


def write_wav_mono(path: str | Path, x: np.ndarray, fs: int, *, pcm_bits: int = 16) -> None:
    """Write mono float signal to WAV."""
    _write_wav(path, x, fs, pcm_bits=pcm_bits)


def write_wav_2ch(
    path: str | Path,
    x_ref: np.ndarray,
    x_rov: np.ndarray,
    fs: int,
    *,
    pcm_bits: int = 16,
) -> None:
    """Write 2-channel float signals to WAV."""
    x_ref = np.asarray(x_ref, dtype=np.float32)
    x_rov = np.asarray(x_rov, dtype=np.float32)
    n = min(x_ref.shape[0], x_rov.shape[0])
    y = np.column_stack([x_ref[:n], x_rov[:n]]).astype(np.float32, copy=False)
    _write_wav(path, y, fs, pcm_bits=pcm_bits)


def _write_wav(path: str | Path, x: np.ndarray, fs: int, *, pcm_bits: int = 16) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    y = np.asarray(x, dtype=np.float32)
    y = np.clip(y, -1.0, 1.0)

    # Today we standardize on int16 to avoid scipy 24-bit portability issues.
    # If you later switch to 24-bit, do it here in one place.
    if pcm_bits != 16:
        pcm_bits = 16

    wavfile.write(str(p), int(fs), (y * 32767.0).astype(np.int16))


def level_dbfs(x: np.ndarray) -> float:
    """RMS level in dBFS for float32 [-1,1] signals."""
    y = np.asarray(x, dtype=np.float32)
    if y.size == 0:
        return float("-inf")
    rms = float(np.sqrt(np.mean(y * y)))
    if rms <= 0.0:
        return float("-inf")
    return float(20.0 * np.log10(rms))
