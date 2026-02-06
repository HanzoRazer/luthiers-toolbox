import numpy as np

from modes._shared.wav_io import read_wav_mono, write_wav_mono


def test_read_write_mono_roundtrip_within_int16_tolerance(tmp_path):
    """
    Round-trip invariant:
      write_wav_mono(float32 [-1,1]) -> PCM int16 -> read_wav_mono() -> float32 [-1,1]

    This catches scaling / normalization regressions (e.g., /32767 vs /32768 mistakes,
    unintended max-abs normalization, etc.).
    """
    fs = 48_000
    seconds = 1.0
    f_hz = 440.0
    amp = 0.5

    t = np.arange(int(fs * seconds), dtype=np.float32) / np.float32(fs)
    x = (amp * np.sin(2.0 * np.pi * np.float32(f_hz) * t)).astype(np.float32)

    wav_path = tmp_path / "tone.wav"
    write_wav_mono(wav_path, x, fs)

    y, meta = read_wav_mono(wav_path)

    assert meta.sample_rate == fs
    assert y.dtype == np.float32
    assert y.shape == x.shape

    # Int16 quantization step is ~1/32768 ≈ 3.05e-5
    # We allow a small cushion for rounding behavior.
    max_abs_err = float(np.max(np.abs(y - x)))
    assert max_abs_err <= 2.5e-4, f"max_abs_err={max_abs_err} exceeded tolerance"

    # Also ensure the round-trip does not "renormalize" unexpectedly.
    assert float(np.max(np.abs(y))) <= amp + 1e-3
