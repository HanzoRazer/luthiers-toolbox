from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np

# Canonical WAV I/O
from modes._shared.wav_io import write_wav_mono

from .analysis import AnalysisResult, analysis_to_json_dict

@dataclass(frozen=True)
class PersistedCapture:
    capture_dir: Path
    audio_path: Path
    analysis_path: Path
    spectrum_path: Path
    session_log_path: Path

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def _append_jsonl(path: Path, obj: Any) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True))
        f.write("\n")

def persist_capture(
    *,
    out_dir: str,
    label: str | None,
    sample_rate: int,
    audio: np.ndarray,
    analysis: AnalysisResult,
) -> PersistedCapture:
    root = Path(out_dir).expanduser().resolve()
    _ensure_dir(root)

    # One capture per timestamp folder (safe for repeated runs)
    import datetime as _dt
    ts = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    cap_dir = root / f"capture_{ts}"
    _ensure_dir(cap_dir)

    audio_path = cap_dir / "audio.wav"
    analysis_path = cap_dir / "analysis.json"
    spectrum_path = cap_dir / "spectrum.csv"
    session_log_path = root / "session.jsonl"

    # Write WAV using canonical layer
    write_wav_mono(audio_path, audio, sample_rate)

    analysis_obj = analysis_to_json_dict(analysis)
    analysis_obj["label"] = label
    analysis_obj["sample_rate"] = sample_rate
    analysis_obj["ts_utc"] = ts
    _write_json(analysis_path, analysis_obj)

    # Spectrum CSV (freq, mag)
    lines = ["freq_hz,magnitude\n"]
    for f, m in zip(analysis.spectrum_freq_hz, analysis.spectrum_mag):
        lines.append(f"{float(f):.6f},{float(m):.8f}\n")
    spectrum_path.write_text("".join(lines), encoding="utf-8")

    # Append-only session log
    _append_jsonl(session_log_path, {
        "ts_utc": ts,
        "label": label,
        "capture_dir": str(cap_dir),
        "dominant_hz": analysis.dominant_hz,
        "peaks": [{"freq_hz": p.freq_hz, "magnitude": p.magnitude} for p in analysis.peaks],
        "confidence": analysis.confidence,
        "clipped": analysis.clipped,
        "rms": analysis.rms,
    })

    return PersistedCapture(
        capture_dir=cap_dir,
        audio_path=audio_path,
        analysis_path=analysis_path,
        spectrum_path=spectrum_path,
        session_log_path=session_log_path,
    )
