"""
Phase 1 Integration Tests: Core Analysis Pipeline

These tests verify the analyze_tap() function works end-to-end with
synthetic audio, producing valid JSON-serializable output.

Added in Phase 1 of v2.0.0 consolidation to establish test baseline
before restructuring.
"""
import json
import numpy as np
import pytest

from tap_tone.analysis import analyze_tap, analysis_to_json_dict, AnalysisResult, Peak


def _make_synthetic_tap(
    sample_rate: int = 48000,
    duration_s: float = 0.5,
    frequencies: list[float] | None = None,
    amplitudes: list[float] | None = None,
    decay_rate: float = 5.0,
) -> np.ndarray:
    """
    Generate synthetic tap response: sum of decaying sinusoids.
    
    Mimics a real tap tone with multiple resonant frequencies.
    """
    if frequencies is None:
        frequencies = [185.0, 320.0, 512.0]  # Typical guitar top modes
    if amplitudes is None:
        amplitudes = [1.0, 0.6, 0.4]
    
    t = np.arange(int(sample_rate * duration_s), dtype=np.float32) / sample_rate
    envelope = np.exp(-decay_rate * t).astype(np.float32)
    
    signal = np.zeros_like(t)
    for freq, amp in zip(frequencies, amplitudes):
        signal += amp * np.sin(2.0 * np.pi * freq * t)
    
    signal = (signal * envelope).astype(np.float32)
    # Normalize to reasonable level
    signal = signal / max(np.abs(signal).max(), 1e-9) * 0.7
    return signal.astype(np.float32)


class TestAnalyzeTapBasic:
    """Basic functionality tests for analyze_tap()."""
    
    def test_returns_analysis_result(self):
        """analyze_tap returns an AnalysisResult dataclass."""
        audio = _make_synthetic_tap()
        result = analyze_tap(audio, sample_rate=48000)
        
        assert isinstance(result, AnalysisResult)
        assert hasattr(result, 'dominant_hz')
        assert hasattr(result, 'peaks')
        assert hasattr(result, 'clipped')
        assert hasattr(result, 'rms')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'spectrum_freq_hz')
        assert hasattr(result, 'spectrum_mag')
    
    def test_detects_known_frequency(self):
        """analyze_tap finds the dominant frequency in synthetic signal."""
        target_freq = 440.0
        audio = _make_synthetic_tap(frequencies=[target_freq], amplitudes=[1.0])
        result = analyze_tap(audio, sample_rate=48000)
        
        assert result.dominant_hz is not None
        # Allow ±5 Hz tolerance for FFT bin resolution
        assert abs(result.dominant_hz - target_freq) < 5.0, (
            f"Expected ~{target_freq} Hz, got {result.dominant_hz} Hz"
        )
    
    def test_detects_multiple_peaks(self):
        """analyze_tap finds multiple peaks in multi-frequency signal."""
        freqs = [185.0, 320.0, 512.0]
        audio = _make_synthetic_tap(frequencies=freqs, amplitudes=[1.0, 0.8, 0.6])
        result = analyze_tap(audio, sample_rate=48000)
        
        assert len(result.peaks) >= 2, "Should detect at least 2 peaks"
        
        # Check that detected peaks are near the input frequencies
        detected_freqs = [p.freq_hz for p in result.peaks]
        for target in freqs[:2]:  # Check at least the two strongest
            matches = [f for f in detected_freqs if abs(f - target) < 10.0]
            assert len(matches) >= 1, f"Should detect peak near {target} Hz"
    
    def test_empty_audio_returns_empty_result(self):
        """analyze_tap handles empty input gracefully."""
        audio = np.array([], dtype=np.float32)
        result = analyze_tap(audio, sample_rate=48000)
        
        assert result.dominant_hz is None
        assert result.peaks == []
        assert result.confidence == 0.0
    
    def test_silent_audio_returns_low_confidence(self):
        """analyze_tap returns low confidence for near-silent input."""
        audio = np.zeros(48000, dtype=np.float32)
        # Add tiny noise to avoid exactly zero
        audio += np.random.randn(48000).astype(np.float32) * 1e-6
        result = analyze_tap(audio, sample_rate=48000)
        
        assert result.confidence < 0.5
        assert result.rms < 0.001


class TestAnalyzeTapClipping:
    """Clipping detection tests."""
    
    def test_detects_clipped_audio(self):
        """analyze_tap flags clipped audio."""
        audio = _make_synthetic_tap()
        # Clip the signal
        audio = np.clip(audio * 2.0, -0.999, 0.999).astype(np.float32)
        result = analyze_tap(audio, sample_rate=48000)
        
        assert result.clipped is True
    
    def test_unclipped_audio_not_flagged(self):
        """analyze_tap does not flag unclipped audio."""
        audio = _make_synthetic_tap()
        # Ensure not clipped
        audio = audio * 0.5
        result = analyze_tap(audio, sample_rate=48000)
        
        assert result.clipped is False


class TestAnalysisToJsonDict:
    """JSON serialization tests."""
    
    def test_output_is_json_serializable(self):
        """analysis_to_json_dict produces JSON-serializable output."""
        audio = _make_synthetic_tap()
        result = analyze_tap(audio, sample_rate=48000)
        json_dict = analysis_to_json_dict(result)
        
        # Should not raise
        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)
    
    def test_output_has_required_fields(self):
        """analysis_to_json_dict includes all expected fields."""
        audio = _make_synthetic_tap()
        result = analyze_tap(audio, sample_rate=48000)
        json_dict = analysis_to_json_dict(result)
        
        required_fields = ['dominant_hz', 'peaks', 'clipped', 'rms', 'confidence']
        for field in required_fields:
            assert field in json_dict, f"Missing required field: {field}"
    
    def test_peaks_structure(self):
        """analysis_to_json_dict peaks have correct structure."""
        audio = _make_synthetic_tap()
        result = analyze_tap(audio, sample_rate=48000)
        json_dict = analysis_to_json_dict(result)
        
        assert isinstance(json_dict['peaks'], list)
        if json_dict['peaks']:
            peak = json_dict['peaks'][0]
            assert 'freq_hz' in peak
            assert 'magnitude' in peak
            assert isinstance(peak['freq_hz'], float)
            assert isinstance(peak['magnitude'], float)
    
    def test_roundtrip_json(self):
        """JSON encode/decode preserves all values."""
        audio = _make_synthetic_tap()
        result = analyze_tap(audio, sample_rate=48000)
        json_dict = analysis_to_json_dict(result)
        
        # Round-trip through JSON
        json_str = json.dumps(json_dict)
        restored = json.loads(json_str)
        
        assert restored['dominant_hz'] == json_dict['dominant_hz']
        assert restored['clipped'] == json_dict['clipped']
        assert abs(restored['rms'] - json_dict['rms']) < 1e-9
        assert abs(restored['confidence'] - json_dict['confidence']) < 1e-9
        assert len(restored['peaks']) == len(json_dict['peaks'])


class TestAnalyzeTapParameters:
    """Parameter sensitivity tests."""
    
    def test_peak_min_hz_filter(self):
        """peak_min_hz parameter filters low frequencies."""
        audio = _make_synthetic_tap(frequencies=[50.0, 200.0], amplitudes=[1.0, 0.8])
        
        # With low min, should detect 50 Hz
        result_low = analyze_tap(audio, sample_rate=48000, peak_min_hz=30.0)
        low_freqs = [p.freq_hz for p in result_low.peaks if p.freq_hz < 100]
        
        # With high min, should not detect 50 Hz
        result_high = analyze_tap(audio, sample_rate=48000, peak_min_hz=100.0)
        high_freqs = [p.freq_hz for p in result_high.peaks if p.freq_hz < 100]
        
        assert len(low_freqs) > len(high_freqs)
    
    def test_different_sample_rates(self):
        """analyze_tap works at different sample rates."""
        for sr in [44100, 48000, 96000]:
            audio = _make_synthetic_tap(sample_rate=sr, frequencies=[440.0])
            result = analyze_tap(audio, sample_rate=sr)
            
            assert result.dominant_hz is not None
            assert abs(result.dominant_hz - 440.0) < 10.0, f"Failed at {sr} Hz sample rate"
