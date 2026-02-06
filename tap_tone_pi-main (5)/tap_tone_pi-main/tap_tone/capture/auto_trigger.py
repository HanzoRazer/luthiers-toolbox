# tap_tone/capture/auto_trigger.py
"""
Auto-Trigger Capture — impulse detection with sounddevice.

This module provides automatic tap detection for hands-free measurement.
No manual timing required: arm → wait → tap → capture → process.

Usage:
    from tap_tone.capture.auto_trigger import capture_one_impulse, AutoTriggerConfig

    result = capture_one_impulse(device=1, sample_rate=48000)
    # result.audio — mono float32 array
    # result.trigger_metrics — provenance info
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Deque, Callable, TYPE_CHECKING
from collections import deque
import time
import math
import queue

import numpy as np

# Lazy import for testing without hardware
if TYPE_CHECKING:
    import sounddevice as sd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AutoTriggerConfig:
    """Configuration for auto-trigger impulse detection."""

    # Detection timing
    warmup_s: float = 0.5           # Noise floor estimation period
    tap_timeout_s: float = 8.0      # Max wait for impulse
    max_retries: int = 3            # Retries before giving up

    # Detection thresholds
    peak_mult: float = 10.0         # Peak must exceed noise * this
    rms_mult: float = 3.0           # RMS must exceed noise * this
    debounce_frames: int = 2        # Consecutive trigger frames required
    ema_alpha: float = 0.05         # Noise floor EMA update rate

    # Capture window
    pre_ms: float = 50.0            # Pre-roll before trigger (ms)
    post_ms: float = 1500.0         # Post-roll after trigger (ms)

    # Guards
    min_impulse_ms: float = 2.0     # Ignore ultra-short glitches
    reject_clipping: bool = False   # Reject and retry if clipped
    clip_threshold: float = 0.98    # Peak level considered clipping


# ---------------------------------------------------------------------------
# Trigger Metrics (Provenance)
# ---------------------------------------------------------------------------

@dataclass
class TriggerMetrics:
    """Metrics from a successful trigger detection."""

    noise_rms: float
    trigger_rms: float
    trigger_peak: float
    snr_est_db: float
    clipped: bool
    triggered_at_utc: str

    def to_provenance_dict(self) -> dict:
        """Return trigger metrics for inclusion in provenance.json."""
        return {
            "auto_trigger": {
                "enabled": True,
                "noise_rms": round(self.noise_rms, 6),
                "trigger_peak": round(self.trigger_peak, 6),
                "trigger_rms": round(self.trigger_rms, 6),
                "trigger_time_utc": self.triggered_at_utc,
                "snr_est_db": round(self.snr_est_db, 2),
                "clipped": self.clipped,
            }
        }


# ---------------------------------------------------------------------------
# Result Dataclass (matches tap_tone.capture.CaptureResult pattern)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AutoTriggerResult:
    """Result from auto-trigger capture — extends CaptureResult pattern."""

    sample_rate: int
    audio: np.ndarray               # shape: (n_samples,), mono float32 [-1, 1]
    trigger_metrics: TriggerMetrics


# ---------------------------------------------------------------------------
# Ring Buffer
# ---------------------------------------------------------------------------

class RingBuffer:
    """Simple mono ring buffer holding the last N samples."""

    def __init__(self, capacity_samples: int):
        self.capacity = int(capacity_samples)
        self._buf: Deque[np.ndarray] = deque()
        self._len = 0

    def push(self, x: np.ndarray) -> None:
        """Add samples, discarding oldest if over capacity."""
        self._buf.append(x)
        self._len += len(x)
        while self._len > self.capacity:
            head = self._buf[0]
            overflow = self._len - self.capacity
            if overflow >= len(head):
                self._buf.popleft()
                self._len -= len(head)
            else:
                self._buf[0] = head[overflow:]
                self._len -= overflow

    def get(self) -> np.ndarray:
        """Return all buffered samples as contiguous array."""
        if not self._buf:
            return np.zeros((0,), dtype=np.float32)
        return np.concatenate(list(self._buf), axis=0)

    def clear(self) -> None:
        """Clear the buffer."""
        self._buf.clear()
        self._len = 0


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class AutoTriggerDetector:
    """Maintains a noise floor estimate and decides when a frame triggers."""

    def __init__(self, cfg: AutoTriggerConfig):
        self.cfg = cfg
        self.noise_rms: float = 1e-6
        self._debounce_hits: int = 0
        self._samples_processed: int = 0

    def arm(self) -> None:
        """Reset detector state for new capture."""
        self._debounce_hits = 0
        self.noise_rms = 1e-6
        self._samples_processed = 0

    def _update_noise(self, rms: float) -> None:
        a = self.cfg.ema_alpha
        self.noise_rms = (1.0 - a) * self.noise_rms + a * max(rms, 1e-9)

    def process_frame(self, x: np.ndarray, fs: int) -> Tuple[bool, Optional[TriggerMetrics]]:
        """
        Process one audio frame.

        Args:
            x: mono float frame, shape (n,)
            fs: sample rate

        Returns:
            (triggered, metrics_if_triggered)
        """
        warmup_samples = int(self.cfg.warmup_s * fs)
        in_warmup = self._samples_processed < warmup_samples
        self._samples_processed += len(x)

        # Basic stats
        rms = float(np.sqrt(np.mean(np.square(x))) + 1e-12)
        peak = float(np.max(np.abs(x)) + 1e-12)

        # Update noise only during warmup or when quiet
        if in_warmup:
            self._update_noise(rms)
            return (False, None)

        if rms < self.cfg.rms_mult * self.noise_rms * 0.5:
            self._update_noise(rms)

        # Trigger conditions
        cond_peak = peak > self.cfg.peak_mult * self.noise_rms
        cond_rms = rms > self.cfg.rms_mult * self.noise_rms

        if cond_peak and cond_rms:
            self._debounce_hits += 1
        else:
            self._debounce_hits = 0

        if self._debounce_hits < self.cfg.debounce_frames:
            return (False, None)

        clipped = peak >= self.cfg.clip_threshold
        snr_db = 20.0 * math.log10(max(rms / max(self.noise_rms, 1e-9), 1e-9))

        metrics = TriggerMetrics(
            noise_rms=self.noise_rms,
            trigger_rms=rms,
            trigger_peak=peak,
            snr_est_db=snr_db,
            clipped=clipped,
            triggered_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        return (True, metrics)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_mono_float32(indata: np.ndarray) -> np.ndarray:
    """Convert (frames, channels) or (frames,) to mono float32 1D."""
    x = indata
    if x.ndim == 2:
        x = np.mean(x, axis=1)
    return np.asarray(x, dtype=np.float32).reshape(-1)


# ---------------------------------------------------------------------------
# Main Capture Function (sounddevice only)
# ---------------------------------------------------------------------------

def capture_one_impulse(
    *,
    device: int | None,
    sample_rate: int,
    cfg: Optional[AutoTriggerConfig] = None,
    channels: int = 1,
    frames_per_buffer: int = 2048,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> AutoTriggerResult:
    """
    Capture one impulse using auto-trigger detection.

    Matches signature convention of tap_tone.capture.record_audio():
        device: int | None
        sample_rate: int
        channels: int (must be 1 for this v1)

    Args:
        device: Audio device index (None for default)
        sample_rate: Sample rate in Hz
        cfg: AutoTriggerConfig (uses defaults if None)
        channels: Number of input channels (downmixed to mono)
        frames_per_buffer: Audio buffer size
        progress_cb: Optional callback for progress messages

    Returns:
        AutoTriggerResult with audio and trigger_metrics

    Raises:
        TimeoutError: If no impulse detected within timeout
        RuntimeError: If audio device fails
        ValueError: If channels != 1 (v1 limitation)
    """
    import sounddevice as sd  # Late import for testing without hardware

    if channels != 1:
        raise ValueError("Auto-trigger v1 expects mono (channels=1).")

    cfg = cfg or AutoTriggerConfig()

    pre_n = int(sample_rate * cfg.pre_ms / 1000.0)
    post_n = int(sample_rate * cfg.post_ms / 1000.0)
    min_impulse_n = int(sample_rate * cfg.min_impulse_ms / 1000.0)

    ring = RingBuffer(pre_n)
    det = AutoTriggerDetector(cfg)
    det.arm()

    q: "queue.Queue[np.ndarray]" = queue.Queue()
    started = time.monotonic()
    triggered_metrics: Optional[TriggerMetrics] = None
    post_audio: list[np.ndarray] = []
    post_collected = 0

    def _log(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)

    _log("Armed (auto-trigger). Waiting for impulse...")

    def callback(indata, frames, time_info, status):
        x = _to_mono_float32(indata)
        q.put(x)

    # Use same device selection pattern as record_audio()
    sd.default.samplerate = sample_rate
    if device is not None:
        sd.default.device = (device, None)

    with sd.InputStream(
        samplerate=sample_rate,
        device=device,
        channels=channels,
        dtype="float32",
        blocksize=frames_per_buffer,
        callback=callback,
    ):
        while True:
            if (time.monotonic() - started) > cfg.tap_timeout_s:
                raise TimeoutError(f"No impulse detected within {cfg.tap_timeout_s:.1f}s")

            try:
                x = q.get(timeout=0.5)
            except queue.Empty:
                continue

            ring.push(x)

            # Post-roll collection
            if triggered_metrics is not None:
                post_audio.append(x)
                post_collected += len(x)
                if post_collected >= post_n:
                    break
                continue

            # Test for trigger
            triggered, metrics = det.process_frame(x, sample_rate)
            if not triggered:
                continue

            # Glitch guard
            above = np.abs(x) > (cfg.peak_mult * det.noise_rms)
            if int(np.sum(above)) < min_impulse_n:
                continue

            assert metrics is not None
            if metrics.clipped and cfg.reject_clipping:
                _log("Impulse detected but clipped; rejecting and continuing...")
                det.arm()
                ring = RingBuffer(pre_n)
                continue

            triggered_metrics = metrics
            _log(f"Impulse detected (SNR≈{metrics.snr_est_db:.1f} dB). Capturing post-roll...")

            post_audio.append(x)
            post_collected = len(x)
            if post_collected >= post_n:
                break

    # Assemble final audio
    pre = ring.get()
    post = np.concatenate(post_audio, axis=0)[:post_n] if post_audio else np.array([], dtype=np.float32)
    audio = np.concatenate([pre, post], axis=0).astype(np.float32)

    # Replace NaNs (rare but possible)
    audio = np.nan_to_num(audio, nan=0.0)

    return AutoTriggerResult(
        sample_rate=sample_rate,
        audio=audio,
        trigger_metrics=triggered_metrics,
    )


# ---------------------------------------------------------------------------
# Testing Helper (no hardware required)
# ---------------------------------------------------------------------------

def capture_one_impulse_from_stream(
    stream_callback: Callable[[], Optional[np.ndarray]],
    sample_rate: int,
    cfg: Optional[AutoTriggerConfig] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[np.ndarray], Optional[TriggerMetrics], str]:
    """
    Capture one impulse from a synthetic stream (for testing).

    Args:
        stream_callback: Function returning next audio frame or None if stream ended
        sample_rate: Sample rate in Hz
        cfg: AutoTriggerConfig
        progress_cb: Optional callback for progress messages

    Returns:
        (waveform_or_None, metrics_or_None, status_string)
        status_string is one of: "success", "timeout", "aborted"
    """
    cfg = cfg or AutoTriggerConfig()

    pre_n = int(sample_rate * cfg.pre_ms / 1000.0)
    post_n = int(sample_rate * cfg.post_ms / 1000.0)
    min_impulse_n = int(sample_rate * cfg.min_impulse_ms / 1000.0)
    timeout_samples = int(sample_rate * cfg.tap_timeout_s)

    ring = RingBuffer(pre_n)
    det = AutoTriggerDetector(cfg)
    det.arm()

    samples_processed = 0
    triggered_metrics: Optional[TriggerMetrics] = None
    post_audio: list[np.ndarray] = []
    post_collected = 0

    def _log(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)

    _log("Armed (auto-trigger). Waiting for impulse...")

    while True:
        if samples_processed > timeout_samples:
            return (None, None, "timeout")

        frame = stream_callback()
        if frame is None:
            return (None, None, "aborted")

        x = _to_mono_float32(frame)
        samples_processed += len(x)
        ring.push(x)

        if triggered_metrics is not None:
            post_audio.append(x)
            post_collected += len(x)
            if post_collected >= post_n:
                break
            continue

        triggered, metrics = det.process_frame(x, sample_rate)
        if not triggered:
            continue

        above = np.abs(x) > (cfg.peak_mult * det.noise_rms)
        if int(np.sum(above)) < min_impulse_n:
            continue

        assert metrics is not None
        if metrics.clipped and cfg.reject_clipping:
            _log("Impulse detected but clipped; rejecting and continuing...")
            det.arm()
            ring = RingBuffer(pre_n)
            continue

        triggered_metrics = metrics
        _log(f"Impulse detected (SNR≈{metrics.snr_est_db:.1f} dB). Capturing post-roll...")

        post_audio.append(x)
        post_collected = len(x)
        if post_collected >= post_n:
            break

    pre = ring.get()
    post = np.concatenate(post_audio, axis=0)[:post_n] if post_audio else np.array([], dtype=np.float32)
    audio = np.concatenate([pre, post], axis=0).astype(np.float32)

    return (audio, triggered_metrics, "success")
