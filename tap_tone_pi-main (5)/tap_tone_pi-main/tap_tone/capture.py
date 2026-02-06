from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import sounddevice as sd

@dataclass(frozen=True)
class CaptureResult:
    sample_rate: int
    audio: np.ndarray  # shape: (n_samples,)

def list_devices() -> list[dict]:
    devices = sd.query_devices()
    out: list[dict] = []
    for i, d in enumerate(devices):
        out.append({
            "index": i,
            "name": d.get("name"),
            "max_input_channels": d.get("max_input_channels"),
            "max_output_channels": d.get("max_output_channels"),
            "default_samplerate": d.get("default_samplerate"),
        })
    return out

def record_audio(*, device: int | None, sample_rate: int, channels: int, seconds: float) -> CaptureResult:
    if channels != 1:
        raise ValueError("This v0.1 skeleton expects mono (channels=1).")
    if seconds <= 0:
        raise ValueError("seconds must be > 0")

    sd.default.samplerate = sample_rate
    if device is not None:
        sd.default.device = (device, None)

    n_samples = int(sample_rate * seconds)

    # Record float32 in [-1, 1]
    audio = sd.rec(frames=n_samples, channels=channels, dtype="float32", blocking=True)
    audio = audio.reshape(-1)  # mono

    # Replace NaNs (rare but possible)
    audio = np.nan_to_num(audio, nan=0.0)

    return CaptureResult(sample_rate=sample_rate, audio=audio)
