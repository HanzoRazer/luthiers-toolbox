# scripts/phase2/io_wav.py
# Backward-compat wrapper — delegates to canonical modes._shared.wav_io
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Canonical WAV I/O layer
from modes._shared.wav_io import (
    read_wav_2ch as _read_wav_2ch,
    write_wav_2ch as _write_wav_2ch,
)


@dataclass(frozen=True)
class Wav2Ch:
    """Legacy dataclass kept for backward compatibility."""

    sample_rate: int
    x_ref: np.ndarray  # shape (n,)
    x_rov: np.ndarray  # shape (n,)


def read_wav_2ch(path: Path) -> Wav2Ch:
    """Read 2-channel WAV file. Delegates to canonical layer."""
    # Canonical signature returns: (ref, rov, meta)
    ref, rov, meta = _read_wav_2ch(path)
    return Wav2Ch(sample_rate=meta.sample_rate, x_ref=ref, x_rov=rov)


def write_wav_2ch(path: Path, fs: int, x_ref: np.ndarray, x_rov: np.ndarray) -> None:
    """Write 2-channel WAV file. Delegates to canonical layer."""
    # Canonical signature: write_wav_2ch(path, x_ref, x_rov, fs)
    _write_wav_2ch(path, x_ref, x_rov, fs)
