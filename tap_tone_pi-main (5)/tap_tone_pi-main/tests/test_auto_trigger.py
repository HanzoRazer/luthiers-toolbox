"""Unit tests for auto-trigger impulse detection.

Tests use synthetic waveforms only — no hardware required.
"""
from __future__ import annotations

import numpy as np
import pytest

from tap_tone.capture.auto_trigger import (
    AutoTriggerConfig,
    AutoTriggerDetector,
    TriggerMetrics,
    RingBuffer,
    capture_one_impulse_from_stream,
)


# --- Fixtures ---

@pytest.fixture
def config() -> AutoTriggerConfig:
    """Standard test config with fast timing."""
    return AutoTriggerConfig(
        warmup_s=0.1,
        tap_timeout_s=2.0,
        max_retries=2,
        peak_mult=10.0,
        rms_mult=3.0,
        debounce_frames=2,
        pre_ms=50.0,
        post_ms=500.0,
        reject_clipping=True,
        clip_threshold=0.98,
        ema_alpha=0.1,
        min_impulse_ms=2.0,
    )


# --- Synthetic Waveform Generators ---

def make_silence(n_samples: int) -> np.ndarray:
    """Generate silence."""
    return np.zeros(n_samples, dtype=np.float32)


def make_noise(n_samples: int, level: float = 0.01) -> np.ndarray:
    """Generate low-level noise."""
    rng = np.random.default_rng(42)
    return (rng.random(n_samples).astype(np.float32) - 0.5) * 2 * level


def make_impulse(
    n_samples: int,
    impulse_pos: int,
    impulse_peak: float = 0.8,
    decay_samples: int = 2000,
    noise_level: float = 0.01,
    fs: int = 48000,
) -> np.ndarray:
    """Generate noise with an impulse (decaying sine burst)."""
    audio = make_noise(n_samples, noise_level)

    # Create impulse: exponentially decaying sine burst
    t = np.arange(decay_samples)
    freq = 200  # Hz
    decay = np.exp(-t / (decay_samples / 5))
    impulse = impulse_peak * np.sin(2 * np.pi * freq * t / fs) * decay

    # Insert impulse
    end_pos = min(impulse_pos + decay_samples, n_samples)
    audio[impulse_pos:end_pos] += impulse[:end_pos - impulse_pos].astype(np.float32)

    return np.clip(audio, -1.0, 1.0).astype(np.float32)


def make_clipped_impulse(
    n_samples: int,
    impulse_pos: int,
    noise_level: float = 0.01,
    fs: int = 48000,
) -> np.ndarray:
    """Generate noise with a clipped impulse (peak >= 0.98).

    Creates a sharp attack that clips immediately for testing clipping detection.
    """
    audio = make_noise(n_samples, noise_level)

    # Create sharp impulse that clips immediately
    decay_samples = 2000
    t = np.arange(decay_samples)
    # Start at full amplitude, no sine oscillation
    decay = np.exp(-t / (decay_samples / 5))
    # Sharp attack: starts at 1.2 (will clip to 1.0)
    impulse = 1.2 * decay

    # Insert impulse
    end_pos = min(impulse_pos + decay_samples, n_samples)
    audio[impulse_pos:end_pos] += impulse[:end_pos - impulse_pos].astype(np.float32)

    return np.clip(audio, -1.0, 1.0).astype(np.float32)


def stream_from_array(audio: np.ndarray, frame_size: int = 1024):
    """Create a stream callback from an audio array."""
    pos = [0]  # Mutable to allow closure modification

    def callback() -> np.ndarray | None:
        if pos[0] >= len(audio):
            return None
        end = min(pos[0] + frame_size, len(audio))
        frame = audio[pos[0]:end]
        pos[0] = end
        # Pad if needed
        if len(frame) < frame_size:
            frame = np.pad(frame, (0, frame_size - len(frame)))
        return frame.astype(np.float32)

    return callback


# --- RingBuffer Tests ---

class TestRingBuffer:
    def test_push_and_get(self):
        buf = RingBuffer(1000)
        buf.push(np.ones(500, dtype=np.float32))
        buf.push(np.ones(300, dtype=np.float32) * 2)

        result = buf.get()
        assert len(result) == 800
        assert result[0] == 1.0
        assert result[500] == 2.0

    def test_overflow_discards_oldest(self):
        buf = RingBuffer(500)
        buf.push(np.ones(300, dtype=np.float32) * 1)
        buf.push(np.ones(300, dtype=np.float32) * 2)
        buf.push(np.ones(300, dtype=np.float32) * 3)

        result = buf.get()
        # Should have discarded oldest samples, kept last 500
        assert len(result) <= 500
        assert result[-1] == 3.0

    def test_clear(self):
        buf = RingBuffer(1000)
        buf.push(np.ones(500, dtype=np.float32))
        buf.clear()

        result = buf.get()
        assert len(result) == 0


# --- AutoTriggerDetector Tests ---

class TestAutoTriggerDetector:
    def test_initial_noise_rms(self, config):
        detector = AutoTriggerDetector(config)
        assert detector.noise_rms == pytest.approx(1e-6)

    def test_arm_resets_state(self, config):
        detector = AutoTriggerDetector(config)
        detector.arm()
        assert detector.noise_rms == pytest.approx(1e-6)
        assert detector._debounce_hits == 0

    def test_warmup_period_no_trigger(self, config):
        detector = AutoTriggerDetector(config)
        detector.arm()

        fs = 48000
        frame_size = 1024

        # During warmup, even high signal should not trigger
        loud_frame = np.ones(frame_size, dtype=np.float32) * 0.5
        triggered, metrics = detector.process_frame(loud_frame, fs)
        assert not triggered
        assert metrics is None

    def test_noise_updates_floor(self, config):
        detector = AutoTriggerDetector(config)
        detector.arm()

        fs = 48000
        frame_size = 1024

        # Process several frames of noise
        for _ in range(50):
            noise = make_noise(frame_size, 0.01)
            detector.process_frame(noise, fs)

        # Noise floor should have increased from initial 1e-6
        assert detector.noise_rms > 1e-5

    def test_silence_no_trigger(self, config):
        detector = AutoTriggerDetector(config)
        detector.arm()

        fs = 48000
        frame_size = 1024

        silence = make_silence(frame_size * 50)
        triggered_any = False
        for i in range(50):
            start = i * frame_size
            frame = silence[start:start + frame_size]
            triggered, _ = detector.process_frame(frame, fs)
            if triggered:
                triggered_any = True
                break

        assert not triggered_any

    def test_impulse_triggers(self, config):
        # Faster warmup for test
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=2.0,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,  # Single frame trigger for simplicity
            pre_ms=50.0,
            post_ms=500.0,
            ema_alpha=0.1,
        )
        detector = AutoTriggerDetector(config)
        detector.arm()

        fs = 48000
        frame_size = 1024

        # First do warmup with noise
        warmup_frames = int(config.warmup_s * fs / frame_size) + 5
        for _ in range(warmup_frames):
            noise = make_noise(frame_size, 0.01)
            detector.process_frame(noise, fs)

        # Now send impulse frame
        impulse_frame = np.zeros(frame_size, dtype=np.float32)
        impulse_frame[100:300] = 0.8  # Strong impulse
        triggered, metrics = detector.process_frame(impulse_frame, fs)

        assert triggered
        assert metrics is not None
        assert metrics.trigger_peak > 0.7
        assert metrics.snr_est_db > 10

    def test_debounce_requires_consecutive_frames(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.1,  # Long enough warmup to establish noise floor
            debounce_frames=3,
            peak_mult=10.0,
            rms_mult=3.0,
            ema_alpha=0.2,  # Faster EMA for test
        )
        detector = AutoTriggerDetector(config)
        detector.arm()

        fs = 48000
        frame_size = 1024

        # Warmup with consistent noise (need enough frames to establish floor)
        warmup_frames = int(config.warmup_s * fs / frame_size) + 2
        for _ in range(warmup_frames):
            detector.process_frame(make_noise(frame_size, 0.01), fs)

        # Single spike frame followed by noise should not trigger
        spike = np.zeros(frame_size, dtype=np.float32)
        spike[100:200] = 0.9

        triggered, _ = detector.process_frame(spike, fs)
        assert not triggered  # Not enough consecutive frames (need 3)

        # Back to noise resets debounce
        triggered, _ = detector.process_frame(make_noise(frame_size, 0.01), fs)
        assert not triggered


# --- Full Capture Pipeline Tests ---

class TestCaptureOneImpulseFromStream:
    def test_successful_capture(self, config):
        fs = 48000
        frame_size = 1024

        # Create audio with impulse after warmup
        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 5000
        post_samples = int(config.post_ms * fs / 1000)
        total_samples = impulse_pos + post_samples + 10000
        audio = make_impulse(total_samples, impulse_pos, 0.8, 5000, 0.01, fs)

        callback = stream_from_array(audio, frame_size)
        wave, metrics, status = capture_one_impulse_from_stream(
            callback, fs, config
        )

        assert status == "success"
        assert wave is not None
        assert len(wave) > 0
        assert metrics is not None
        assert metrics.snr_est_db > 5
        assert not metrics.clipped

    def test_timeout_on_silence(self, config):
        # Very short timeout
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=0.2,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=2,
        )
        fs = 48000
        silence = make_silence(int(fs * 1.0))

        callback = stream_from_array(silence, 1024)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        # May timeout or abort if stream ends first
        assert status in ("timeout", "aborted")
        assert wave is None
        assert metrics is None

    def test_clipped_impulse_rejected(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=1.0,
            reject_clipping=True,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,
        )
        fs = 48000
        frame_size = 1024

        # Only clipped impulses available
        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 3000
        post_samples = int(config.post_ms * fs / 1000)
        total = impulse_pos + post_samples + 5000
        audio = make_clipped_impulse(total, impulse_pos, 0.01, fs)

        callback = stream_from_array(audio, frame_size)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        # Should fail because clipping rejected and stream ends
        assert status in ("timeout", "aborted")

    def test_clipped_impulse_accepted_when_allowed(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.2,  # Longer warmup to establish noise floor
            tap_timeout_s=2.0,
            reject_clipping=False,  # Allow clipping
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,  # Single frame trigger to capture clipped frame
            ema_alpha=0.2,  # Faster EMA for stable floor
            clip_threshold=0.98,
        )
        fs = 48000
        frame_size = 1024

        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 3000
        post_samples = int(config.post_ms * fs / 1000)
        total = impulse_pos + post_samples + 10000
        audio = make_clipped_impulse(total, impulse_pos, 0.01, fs)

        callback = stream_from_array(audio, frame_size)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        assert status == "success"
        assert metrics is not None
        assert metrics.clipped  # Should be flagged since peak >= 0.98

    def test_provenance_dict(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=2.0,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,
        )
        fs = 48000
        frame_size = 1024

        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 3000
        post_samples = int(config.post_ms * fs / 1000)
        total = impulse_pos + post_samples + 10000
        audio = make_impulse(total, impulse_pos, 0.8, 5000, 0.01, fs)

        callback = stream_from_array(audio, frame_size)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        assert status == "success"
        assert metrics is not None

        prov = metrics.to_provenance_dict()
        assert prov["auto_trigger"]["enabled"]
        assert prov["auto_trigger"]["snr_est_db"] > 0
        assert prov["auto_trigger"]["trigger_time_utc"] is not None

    def test_progress_callback(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=2.0,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,
        )
        fs = 48000
        frame_size = 1024
        messages: list[str] = []

        def on_progress(msg: str):
            messages.append(msg)

        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 3000
        post_samples = int(config.post_ms * fs / 1000)
        total = impulse_pos + post_samples + 10000
        audio = make_impulse(total, impulse_pos, 0.8, 5000, 0.01, fs)

        callback = stream_from_array(audio, frame_size)
        wave, metrics, status = capture_one_impulse_from_stream(
            callback, fs, config, progress_cb=on_progress
        )

        assert status == "success"
        assert len(messages) >= 2  # Armed + Impulse detected


# --- Edge Cases ---

class TestEdgeCases:
    def test_very_short_audio(self, config):
        """Stream ends before any detection."""
        fs = 48000
        audio = make_noise(1024 * 2, 0.01)
        callback = stream_from_array(audio, 1024)

        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)
        assert status == "aborted"
        assert wave is None

    def test_impulse_during_warmup_ignored(self, config):
        """Impulse during warmup should not trigger."""
        config = AutoTriggerConfig(
            warmup_s=0.2,  # Longer warmup
            tap_timeout_s=0.3,  # Short timeout after warmup
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,
        )
        fs = 48000

        # Impulse happens during warmup
        impulse_pos = 1024 * 2  # Very early
        warmup_samples = int(config.warmup_s * fs)
        total = warmup_samples + 50000
        audio = make_impulse(total, impulse_pos, 0.8, 3000, 0.01, fs)

        callback = stream_from_array(audio, 1024)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        # Should timeout or abort because impulse was during warmup
        assert status in ("timeout", "aborted")

    def test_zero_pre_roll(self, config):
        config = AutoTriggerConfig(
            warmup_s=0.05,
            tap_timeout_s=2.0,
            pre_ms=0,  # No pre-roll
            post_ms=500.0,
            peak_mult=10.0,
            rms_mult=3.0,
            debounce_frames=1,
        )
        fs = 48000

        warmup_samples = int(config.warmup_s * fs)
        impulse_pos = warmup_samples + 3000
        post_samples = int(config.post_ms * fs / 1000)
        total = impulse_pos + post_samples + 10000
        audio = make_impulse(total, impulse_pos, 0.8, 5000, 0.01, fs)

        callback = stream_from_array(audio, 1024)
        wave, metrics, status = capture_one_impulse_from_stream(callback, fs, config)

        assert status == "success"
        assert wave is not None
        # Audio should be mostly post-roll
        assert len(wave) >= post_samples * 0.8


# --- TriggerMetrics Tests ---

class TestTriggerMetrics:
    def test_to_provenance_dict(self):
        metrics = TriggerMetrics(
            noise_rms=0.01,
            trigger_rms=0.5,
            trigger_peak=0.8,
            snr_est_db=30.0,
            clipped=False,
            triggered_at_utc="2026-01-21T12:00:00Z",
        )

        prov = metrics.to_provenance_dict()
        assert prov["auto_trigger"]["enabled"]
        assert prov["auto_trigger"]["noise_rms"] == 0.01
        assert prov["auto_trigger"]["trigger_peak"] == 0.8
        assert prov["auto_trigger"]["snr_est_db"] == 30.0
        assert prov["auto_trigger"]["clipped"] is False
        assert prov["auto_trigger"]["trigger_time_utc"] == "2026-01-21T12:00:00Z"

    def test_clipped_flag(self):
        metrics = TriggerMetrics(
            noise_rms=0.01,
            trigger_rms=0.9,
            trigger_peak=0.99,
            snr_est_db=40.0,
            clipped=True,
            triggered_at_utc="2026-01-21T12:00:00Z",
        )

        assert metrics.clipped
        prov = metrics.to_provenance_dict()
        assert prov["auto_trigger"]["clipped"] is True
