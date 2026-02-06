#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from tap_tone.capture import record_audio
from tap_tone.analysis import analyze_tap
from tap_tone.config import CaptureConfig, AnalysisConfig
from tap_tone.storage import persist_capture


def main() -> None:
    ap = argparse.ArgumentParser(description="Run N repeatability takes and summarize variance.")
    ap.add_argument("--device", type=int, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--label", type=str, default=None)
    ap.add_argument("--takes", type=int, default=10)
    ap.add_argument("--seconds", type=float, default=2.5)
    ap.add_argument("--sample-rate", type=int, default=48000)
    args = ap.parse_args()

    out_root = Path(args.out).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    cap_cfg = CaptureConfig(
        device=args.device,
        sample_rate=args.sample_rate,
        channels=1,
        seconds=args.seconds,
    )
    an_cfg = AnalysisConfig()

    results: list[dict[str, Any]] = []
    doms: list[float] = []

    for i in range(1, args.takes + 1):
        label_i = args.label or "repeatability"
        label_take = f"{label_i}_take_{i:02d}"

        cap = record_audio(
            device=cap_cfg.device,
            sample_rate=cap_cfg.sample_rate,
            channels=cap_cfg.channels,
            seconds=cap_cfg.seconds,
        )
        res = analyze_tap(
            cap.audio, cap.sample_rate,
            highpass_hz=an_cfg.highpass_hz,
            peak_min_hz=an_cfg.peak_min_hz,
            peak_max_hz=an_cfg.peak_max_hz,
            peak_min_prominence=an_cfg.peak_min_prominence,
            peak_min_spacing_hz=an_cfg.peak_min_spacing_hz,
            max_peaks=an_cfg.max_peaks,
        )

        persisted = persist_capture(
            out_dir=str(out_root),
            label=label_take,
            sample_rate=cap.sample_rate,
            audio=cap.audio,
            analysis=res,
        )

        if res.dominant_hz is not None:
            doms.append(float(res.dominant_hz))

        results.append({
            "take": i,
            "label": label_take,
            "capture_dir": str(persisted.capture_dir),
            "dominant_hz": res.dominant_hz,
            "rms": res.rms,
            "clipped": res.clipped,
            "confidence": res.confidence,
            "peaks": [{"freq_hz": p.freq_hz, "magnitude": p.magnitude} for p in res.peaks[:8]],
        })

        print(f"[{i:02d}/{args.takes}] dominant={res.dominant_hz} rms={res.rms:.6f} clipped={res.clipped} conf={res.confidence:.2f}")

    summary = {
        "takes": args.takes,
        "device": args.device,
        "sample_rate": args.sample_rate,
        "seconds": args.seconds,
        "label": args.label,
        "dominant_hz_mean": mean(doms) if doms else None,
        "dominant_hz_std": pstdev(doms) if len(doms) > 1 else 0.0 if doms else None,
        "results": results,
    }

    takes_path = out_root / "takes.json"
    takes_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[OK] Wrote {takes_path}")


if __name__ == "__main__":
    main()
