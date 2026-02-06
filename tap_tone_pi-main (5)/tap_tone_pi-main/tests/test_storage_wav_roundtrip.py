"""
Regression test for tap_tone/storage.py WAV write path.

This test exercises the persist_capture() -> audio.wav -> read back path,
catching argument transposition bugs like the Bug 2 identified in the
consolidation review (storage.py:57 had write_wav_mono(path, sample_rate, audio)
instead of write_wav_mono(path, audio, sample_rate)).
"""
import numpy as np
import pytest

from modes._shared.wav_io import read_wav_mono
from tap_tone.storage import persist_capture
from tap_tone.analysis import AnalysisResult, Peak


def _make_synthetic_analysis(audio: np.ndarray, sample_rate: int) -> AnalysisResult:
    """Create a minimal AnalysisResult for testing storage."""
    # Simple FFT to populate spectrum fields
    n = len(audio)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate).astype(np.float32)
    mags = np.abs(np.fft.rfft(audio)).astype(np.float32)
    mags /= max(mags.max(), 1e-9)  # Normalize
    
    # Find a peak for the test
    peak_idx = int(np.argmax(mags))
    peak = Peak(freq_hz=float(freqs[peak_idx]), magnitude=float(mags[peak_idx]))
    
    return AnalysisResult(
        dominant_hz=float(freqs[peak_idx]),
        peaks=[peak],
        spectrum_freq_hz=freqs,
        spectrum_mag=mags,
        rms=float(np.sqrt(np.mean(audio ** 2))),
        clipped=False,
        confidence=0.9,
    )


def test_persist_capture_wav_roundtrip(tmp_path):
    """
    Verify that persist_capture writes a valid WAV file that can be read back
    with correct signal content. This catches argument order bugs in the
    write_wav_mono call.
    """
    sample_rate = 48000
    duration_s = 0.5
    freq_hz = 440.0
    amplitude = 0.5
    
    # Generate test signal
    t = np.arange(int(sample_rate * duration_s), dtype=np.float32) / sample_rate
    audio = (amplitude * np.sin(2.0 * np.pi * freq_hz * t)).astype(np.float32)
    
    # Create analysis result
    analysis = _make_synthetic_analysis(audio, sample_rate)
    
    # Persist capture
    result = persist_capture(
        out_dir=str(tmp_path),
        label="test_capture",
        sample_rate=sample_rate,
        audio=audio,
        analysis=analysis,
    )
    
    # Verify WAV file exists
    assert result.audio_path.exists(), "audio.wav was not created"
    
    # Read back and verify
    y, meta = read_wav_mono(result.audio_path)
    
    # Check sample rate is correct (not swapped with audio data)
    assert meta.sample_rate == sample_rate, (
        f"Sample rate mismatch: expected {sample_rate}, got {meta.sample_rate}. "
        "This suggests write_wav_mono arguments are transposed."
    )
    
    # Check signal shape
    assert y.shape == audio.shape, (
        f"Shape mismatch: expected {audio.shape}, got {y.shape}"
    )
    
    # Check signal content (allowing for int16 quantization)
    max_abs_err = float(np.max(np.abs(y - audio)))
    assert max_abs_err <= 2.5e-4, (
        f"Signal content mismatch: max_abs_err={max_abs_err}. "
        "This suggests the WAV file contains wrong data."
    )
    
    # Verify the signal is not garbage (correlation check)
    correlation = float(np.corrcoef(audio, y)[0, 1])
    assert correlation > 0.999, (
        f"Signal correlation too low: {correlation}. "
        "The WAV file may contain noise instead of the input signal."
    )


def test_persist_capture_creates_all_artifacts(tmp_path):
    """Verify persist_capture creates all expected files."""
    sample_rate = 48000
    audio = np.sin(np.linspace(0, 2 * np.pi * 100, sample_rate // 2)).astype(np.float32)
    analysis = _make_synthetic_analysis(audio, sample_rate)
    
    result = persist_capture(
        out_dir=str(tmp_path),
        label="artifact_test",
        sample_rate=sample_rate,
        audio=audio,
        analysis=analysis,
    )
    
    assert result.audio_path.exists(), "audio.wav missing"
    assert result.analysis_path.exists(), "analysis.json missing"
    assert result.spectrum_path.exists(), "spectrum.csv missing"
    assert result.session_log_path.exists(), "session.jsonl missing"
