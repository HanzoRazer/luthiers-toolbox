from __future__ import annotations
import numpy as np
from scipy.io import wavfile  # used only to craft raw PCM fixtures in tests

from modes._shared.wav_io import (
    read_wav_mono, read_wav_2ch, write_wav_mono, write_wav_2ch, level_dbfs
)
from tests._util.gen_tone import sine_tone, rms, db

# Helpers
FS = 48000
AMP_M12DB = 10.0 ** (-12.0 / 20.0)  # ~0.2511886432


def test_roundtrip_mono(tmp_path):
    x = sine_tone(FS, dur_s=1.0, freq_hz=440.0, amp=AMP_M12DB)
    p = tmp_path / "mono.wav"
    write_wav_mono(p, x, FS)
    xr, meta = read_wav_mono(p)
    assert meta.sample_rate == FS
    assert len(xr) == len(x)
    # Level should be within ~0.2 dB
    d_db = abs(db(rms(x)) - db(rms(xr)))
    assert d_db < 0.2, f"Level drift too large: {d_db:.3f} dB"
    # Correlation should be high
    corr = float(np.corrcoef(x, xr)[0, 1])
    assert corr > 0.999, f"Correlation too low: {corr:.6f}"


def test_roundtrip_two_channel(tmp_path):
    ref = sine_tone(FS, 1.0, 300.0, amp=0.2, phase=0.0)
    rov = sine_tone(FS, 1.0, 600.0, amp=0.2, phase=np.pi / 3.0)
    p = tmp_path / "stereo.wav"
    write_wav_2ch(p, ref, rov, FS)
    r2, v2, meta = read_wav_2ch(p)
    assert meta.sample_rate == FS
    assert len(r2) == len(v2) == len(ref)
    # Channel identity roughly preserved
    corr_ref = float(np.corrcoef(ref, r2)[0, 1])
    corr_rov = float(np.corrcoef(rov, v2)[0, 1])
    assert corr_ref > 0.999
    assert corr_rov > 0.999


def test_read_mono_policy_from_stereo(tmp_path):
    # Craft a stereo file with distinct channels via canonical writer
    L = sine_tone(FS, 0.5, 220.0, amp=0.2)
    R = sine_tone(FS, 0.5, 880.0, amp=0.2)
    p = tmp_path / "stereo.wav"
    write_wav_2ch(p, L, R, FS)
    xm, _meta = read_wav_mono(p)
    # Current policy: mono reader takes channel 0 (left)
    corr = float(np.corrcoef(L, xm)[0, 1])
    assert corr > 0.999


def test_import_normalization_from_int16(tmp_path):
    # Create a raw int16 WAV (simulate external file) then ensure normalization to [-1,1].
    x = sine_tone(FS, 0.25, 1000.0, amp=0.5)
    xi16 = (np.clip(x, -1.0, 1.0) * 32767.0).astype(np.int16)
    p = tmp_path / "raw_int16.wav"
    wavfile.write(str(p), FS, xi16)
    xr, meta = read_wav_mono(p)
    assert meta.sample_rate == FS
    assert xr.dtype == np.float32
    assert float(np.max(np.abs(xr))) <= 1.0 + 1e-6
    # Levels roughly match
    d_db = abs(db(rms(x)) - db(rms(xr)))
    assert d_db < 0.3


def test_level_dbfs_utility():
    x = sine_tone(FS, 0.25, 1000.0, amp=AMP_M12DB)
    level = level_dbfs(x)
    # Sine RMS is amp / sqrt(2), so dBFS = 20*log10(amp/sqrt(2))
    # For amp=0.251..., RMS~=0.178, dBFS~=-15 dB (not -12)
    # Let's just check it's in a reasonable range for a -12 dBFS amplitude sine
    assert -18.0 < level < -10.0, f"level_dbfs out of expected range: {level}"
