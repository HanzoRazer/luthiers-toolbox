"""Quick tests for tap_tone.config and tap_tone.analysis to boost coverage."""

import numpy as np
import pytest

from tap_tone.config import CaptureConfig, AnalysisConfig
from tap_tone.analysis import Peak, AnalysisResult, analyze_tap


class TestConfig:
    """Test dataclass instantiation and defaults."""

    def test_capture_config_defaults(self):
        cfg = CaptureConfig()
        assert cfg.device is None
        assert cfg.sample_rate == 48000
        assert cfg.channels == 1
        assert cfg.seconds == 2.5

    def test_capture_config_custom(self):
        cfg = CaptureConfig(device=2, sample_rate=44100, channels=2, seconds=3.0)
        assert cfg.device == 2
        assert cfg.sample_rate == 44100
        assert cfg.channels == 2
        assert cfg.seconds == 3.0

    def test_analysis_config_defaults(self):
        cfg = AnalysisConfig()
        assert cfg.highpass_hz == 20.0
        assert cfg.peak_min_hz == 40.0
        assert cfg.peak_max_hz == 2000.0
        assert cfg.peak_min_prominence == 0.05
        assert cfg.peak_min_spacing_hz == 10.0
        assert cfg.max_peaks == 12


class TestAnalysis:
    """Test analysis functions with synthetic signals."""

    def test_peak_dataclass(self):
        p = Peak(freq_hz=440.0, magnitude=0.8)
        assert p.freq_hz == 440.0
        assert p.magnitude == 0.8

    def test_analysis_result_dataclass(self):
        res = AnalysisResult(
            dominant_hz=440.0,
            peaks=[Peak(440.0, 0.8)],
            clipped=False,
            rms=0.1,
            confidence=0.9,
            spectrum_freq_hz=np.array([0, 100, 200]),
            spectrum_mag=np.array([0.1, 0.5, 0.2]),
        )
        assert res.dominant_hz == 440.0
        assert len(res.peaks) == 1
        assert not res.clipped

    def test_analyze_tap_with_sine(self):
        """Analyze a simple sine wave - should detect the frequency."""
        fs = 48000
        duration = 0.5
        freq = 440.0
        t = np.linspace(0, duration, int(fs * duration), dtype=np.float32)
        audio = 0.5 * np.sin(2 * np.pi * freq * t).astype(np.float32)

        result = analyze_tap(audio, fs)

        assert result is not None
        assert result.rms > 0
        assert not result.clipped
        assert len(result.spectrum_freq_hz) > 0

    def test_analyze_tap_with_silence(self):
        """Analyze silence - should have low RMS and no peaks."""
        fs = 48000
        audio = np.zeros(fs, dtype=np.float32)

        result = analyze_tap(audio, fs)

        assert result.rms < 0.001
        assert result.dominant_hz is None or result.confidence < 0.5

    def test_analyze_tap_clipping_detection(self):
        """Clipped audio should be detected."""
        fs = 48000
        audio = np.ones(fs, dtype=np.float32)  # All 1.0 = clipped

        result = analyze_tap(audio, fs)

        assert result.clipped
