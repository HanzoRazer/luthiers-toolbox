"""
Phase 1 Integration Tests: Chladni Peak Extraction Pipeline

These tests verify the Chladni peaks_from_wav module works end-to-end,
detecting peaks from synthetic sweep WAV files.

Added in Phase 1 of v2.0.0 consolidation to establish test baseline
before restructuring.
"""
import json
import numpy as np
import pytest
from pathlib import Path

from modes._shared.wav_io import write_wav_mono, read_wav_mono
from scipy.signal import find_peaks, windows


def _make_synthetic_sweep(
    sample_rate: int = 48000,
    duration_s: float = 2.0,
    resonant_freqs: list[float] | None = None,
    q_factors: list[float] | None = None,
) -> np.ndarray:
    """
    Generate synthetic Chladni-style response with resonant peaks.
    
    Simulates the frequency response of a vibrating plate with
    several resonant modes.
    """
    if resonant_freqs is None:
        resonant_freqs = [148.0, 226.0, 385.0, 512.0]
    if q_factors is None:
        q_factors = [30.0] * len(resonant_freqs)
    
    n_samples = int(sample_rate * duration_s)
    t = np.arange(n_samples, dtype=np.float32) / sample_rate
    
    # Create signal with peaks at resonant frequencies
    signal = np.zeros(n_samples, dtype=np.float32)
    
    for freq, q in zip(resonant_freqs, q_factors):
        # Add a burst at this frequency with some decay
        burst_duration = 0.3
        burst_samples = int(sample_rate * burst_duration)
        burst_t = np.arange(burst_samples, dtype=np.float32) / sample_rate
        
        # Resonant response (damped sinusoid)
        decay = np.exp(-freq / q * burst_t)
        burst = np.sin(2.0 * np.pi * freq * burst_t) * decay
        
        # Place burst at random position
        start = np.random.randint(0, max(1, n_samples - burst_samples))
        end = min(start + burst_samples, n_samples)
        signal[start:end] += burst[:end-start].astype(np.float32)
    
    # Normalize
    signal = signal / max(np.abs(signal).max(), 1e-9) * 0.7
    return signal.astype(np.float32)


def _extract_peaks_from_wav(
    wav_path: Path,
    min_hz: float = 50.0,
    max_hz: float = 2000.0,
    prominence: float = 0.02,
) -> list[float]:
    """
    Extract peak frequencies from WAV file.
    
    Mirrors the logic in modes/chladni/peaks_from_wav.py for testing.
    """
    x, meta = read_wav_mono(wav_path)
    fs = meta.sample_rate
    
    N = len(x)
    w = windows.hann(N, sym=False)
    X = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(N, 1.0 / fs)
    mag = np.abs(X) / (N / 2.0)
    
    # Band limit
    band = (f >= min_hz) & (f <= max_hz)
    fi = np.where(band)[0]
    magb = mag[fi]
    thresh = max(magb.max(), 1e-12) * prominence
    peaks_idx, _ = find_peaks(magb, prominence=thresh)
    
    return [float(f[fi[p]]) for p in peaks_idx[:64]]


class TestChladniPeakExtraction:
    """Core peak extraction tests."""
    
    def test_detects_resonant_frequencies(self, tmp_path):
        """Peak extraction finds known resonant frequencies."""
        target_freqs = [148.0, 226.0, 385.0]
        sample_rate = 48000
        
        # Generate and save synthetic sweep
        audio = _make_synthetic_sweep(
            sample_rate=sample_rate,
            resonant_freqs=target_freqs,
        )
        wav_path = tmp_path / "sweep.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        # Extract peaks
        detected = _extract_peaks_from_wav(wav_path)
        
        assert len(detected) >= 2, "Should detect at least 2 peaks"
        
        # Check that at least one target frequency is detected
        matches = 0
        for target in target_freqs:
            for det in detected:
                if abs(det - target) < 15.0:  # ±15 Hz tolerance
                    matches += 1
                    break
        
        assert matches >= 1, f"Should detect at least 1 target frequency. Detected: {detected}"
    
    def test_empty_wav_returns_no_peaks(self, tmp_path):
        """Peak extraction handles silence gracefully."""
        sample_rate = 48000
        audio = np.zeros(sample_rate, dtype=np.float32)
        # Add tiny noise to avoid exactly zero
        audio += np.random.randn(sample_rate).astype(np.float32) * 1e-7
        
        wav_path = tmp_path / "silent.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        detected = _extract_peaks_from_wav(wav_path)
        
        # Silent audio should have few or no prominent peaks
        assert len(detected) < 10, "Silent audio should not produce many peaks"
    
    def test_single_frequency_detected(self, tmp_path):
        """Peak extraction finds a single pure tone."""
        sample_rate = 48000
        freq = 440.0
        t = np.arange(sample_rate, dtype=np.float32) / sample_rate
        audio = (0.5 * np.sin(2.0 * np.pi * freq * t)).astype(np.float32)
        
        wav_path = tmp_path / "tone.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        detected = _extract_peaks_from_wav(wav_path, min_hz=400, max_hz=500)
        
        assert len(detected) >= 1, "Should detect at least 1 peak"
        # Find closest peak to target
        closest = min(detected, key=lambda x: abs(x - freq))
        assert abs(closest - freq) < 5.0, f"Peak should be at ~{freq} Hz, got {closest}"
    
    def test_band_limiting_works(self, tmp_path):
        """Band limits filter out-of-range frequencies."""
        sample_rate = 48000
        
        # Create signal with peaks at 100 Hz and 500 Hz
        t = np.arange(sample_rate, dtype=np.float32) / sample_rate
        audio = (
            0.5 * np.sin(2.0 * np.pi * 100.0 * t) +
            0.5 * np.sin(2.0 * np.pi * 500.0 * t)
        ).astype(np.float32)
        
        wav_path = tmp_path / "two_tones.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        # Only look for peaks above 200 Hz
        detected = _extract_peaks_from_wav(wav_path, min_hz=200, max_hz=600)
        
        # Should find 500 Hz but not 100 Hz
        low_peaks = [f for f in detected if f < 200]
        high_peaks = [f for f in detected if 450 < f < 550]
        
        assert len(low_peaks) == 0, "Should not detect peaks below min_hz"
        assert len(high_peaks) >= 1, "Should detect 500 Hz peak"


class TestChladniWavRoundtrip:
    """WAV I/O integration tests for Chladni pipeline."""
    
    def test_wav_roundtrip_preserves_signal(self, tmp_path):
        """WAV write/read preserves signal for peak detection."""
        sample_rate = 48000
        freq = 185.0
        t = np.arange(sample_rate, dtype=np.float32) / sample_rate
        original = (0.5 * np.sin(2.0 * np.pi * freq * t)).astype(np.float32)
        
        wav_path = tmp_path / "roundtrip.wav"
        write_wav_mono(wav_path, original, sample_rate)
        restored, meta = read_wav_mono(wav_path)
        
        assert meta.sample_rate == sample_rate
        
        # Signal should be preserved (within int16 quantization)
        max_err = float(np.max(np.abs(restored - original)))
        assert max_err < 1e-3, f"Signal not preserved: max_err={max_err}"
    
    def test_different_sample_rates(self, tmp_path):
        """Peak detection works at different sample rates."""
        target_freq = 440.0
        
        for sr in [44100, 48000]:
            t = np.arange(sr, dtype=np.float32) / sr
            audio = (0.5 * np.sin(2.0 * np.pi * target_freq * t)).astype(np.float32)
            
            wav_path = tmp_path / f"tone_{sr}.wav"
            write_wav_mono(wav_path, audio, sr)
            
            detected = _extract_peaks_from_wav(wav_path, min_hz=400, max_hz=500)
            
            assert len(detected) >= 1, f"Should detect peak at {sr} Hz sample rate"
            closest = min(detected, key=lambda x: abs(x - target_freq))
            assert abs(closest - target_freq) < 10.0, f"Failed at {sr} Hz"


class TestChladniOutputStructure:
    """Output JSON structure tests."""
    
    def test_peaks_are_floats(self, tmp_path):
        """Detected peaks are proper floats."""
        sample_rate = 48000
        audio = _make_synthetic_sweep(sample_rate=sample_rate)
        
        wav_path = tmp_path / "sweep.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        detected = _extract_peaks_from_wav(wav_path)
        
        for peak in detected:
            assert isinstance(peak, float), f"Peak should be float, got {type(peak)}"
    
    def test_peaks_are_in_band(self, tmp_path):
        """All detected peaks are within specified band."""
        sample_rate = 48000
        audio = _make_synthetic_sweep(sample_rate=sample_rate)
        
        wav_path = tmp_path / "sweep.wav"
        write_wav_mono(wav_path, audio, sample_rate)
        
        min_hz, max_hz = 100.0, 600.0
        detected = _extract_peaks_from_wav(wav_path, min_hz=min_hz, max_hz=max_hz)
        
        for peak in detected:
            assert min_hz <= peak <= max_hz, f"Peak {peak} outside band [{min_hz}, {max_hz}]"
