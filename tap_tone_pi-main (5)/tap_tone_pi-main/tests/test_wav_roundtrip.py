"""WAV round-trip test: write → read → verify energy and correlation."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from modes._shared.wav_io import level_dbfs, read_wav_mono, write_wav_mono


def _tone(fs: int = 48000, f: float = 997.0, dur: float = 0.5, amp: float = 0.3):
    """Generate a test sine tone."""
    t = np.arange(int(fs * dur)) / fs
    return (amp * np.sin(2 * np.pi * f * t)).astype(np.float32), fs


def test_wav_roundtrip(tmp_path: Path):
    """Verify WAV write/read preserves signal within quantization tolerance."""
    x, fs = _tone()
    p = tmp_path / "roundtrip.wav"

    # Write and read back
    write_wav_mono(str(p), x, fs)
    y, meta = read_wav_mono(str(p))

    # Sample rate preserved
    assert meta.sample_rate == fs

    # Energy tolerance: allow small write/read quantization error
    db_x = level_dbfs(x)
    db_y = level_dbfs(y)
    assert abs(db_x - db_y) < 0.5, f"RMS drift too large: {db_x:.2f} vs {db_y:.2f} dBFS"

    # Correlation check
    n = min(x.size, y.size)
    r = float(np.corrcoef(x[:n], y[:n])[0, 1])
    assert r > 0.999, f"Correlation too low: {r:.6f}"


def test_wav_roundtrip_quiet_signal(tmp_path: Path):
    """Verify quiet signals also round-trip correctly."""
    x, fs = _tone(amp=0.01)  # -40 dBFS
    p = tmp_path / "quiet.wav"

    write_wav_mono(str(p), x, fs)
    y, meta = read_wav_mono(str(p))

    assert meta.sample_rate == fs
    n = min(x.size, y.size)
    r = float(np.corrcoef(x[:n], y[:n])[0, 1])
    assert r > 0.99, f"Quiet signal correlation too low: {r:.6f}"
