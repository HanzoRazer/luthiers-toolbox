#!/usr/bin/env python3
"""
tap_tone_pi CLI — Unified command dispatcher.

Migration: Canonical location is now tap_tone_pi.cli.main
           (previously tap_tone/main.py)

Usage:
    ttp devices              # List audio devices
    ttp record --out ./out   # Record single tap
    ttp live --out ./out     # Continuous recording
    ttp gold-run ...         # Gold standard run
    ttp gui                  # Launch Tkinter GUI
    ttp phase2 ...           # Phase 2 ODS workflow
    ttp chladni ...          # Chladni pattern analysis
    ttp bending ...          # Bending MOE calculation
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable


def cmd_devices(_args: argparse.Namespace) -> int:
    """List available audio devices."""
    try:
        from tap_tone_pi.capture import list_devices
    except ImportError:
        # Fallback to legacy location
        from tap_tone.capture import list_devices
    
    devs = list_devices()
    for d in devs:
        print(f'[{d["index"]}] {d["name"]} (in={d["max_input_channels"]}, out={d["max_output_channels"]})')
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    """Record a single tap and analyze."""
    try:
        from tap_tone_pi.core.config import CaptureConfig, AnalysisConfig
        from tap_tone_pi.core.analysis import analyze_tap
        from tap_tone.capture import record_audio  # Capture still in legacy
        from tap_tone.storage import persist_capture
    except ImportError:
        from tap_tone.config import CaptureConfig, AnalysisConfig
        from tap_tone.analysis import analyze_tap
        from tap_tone.capture import record_audio
        from tap_tone.storage import persist_capture
    
    cap_cfg = CaptureConfig(
        device=args.device,
        sample_rate=args.sample_rate,
        channels=args.channels,
        seconds=args.seconds,
    )
    an_cfg = AnalysisConfig()

    cap = record_audio(
        device=cap_cfg.device,
        sample_rate=cap_cfg.sample_rate,
        channels=cap_cfg.channels,
        seconds=cap_cfg.seconds,
    )

    res = analyze_tap(
        cap.audio,
        cap.sample_rate,
        highpass_hz=an_cfg.highpass_hz,
        peak_min_hz=an_cfg.peak_min_hz,
        peak_max_hz=an_cfg.peak_max_hz,
        peak_min_prominence=an_cfg.peak_min_prominence,
        peak_min_spacing_hz=an_cfg.peak_min_spacing_hz,
        max_peaks=an_cfg.max_peaks,
    )

    _print_summary(args.label, res)

    persisted = persist_capture(
        out_dir=args.out,
        label=args.label,
        sample_rate=cap.sample_rate,
        audio=cap.audio,
        analysis=res,
    )
    print(f"Wrote: {persisted.capture_dir}")
    return 0


def cmd_live(args: argparse.Namespace) -> int:
    """Continuous tap recording mode."""
    print("Live mode: press Ctrl+C to stop. Tap, wait, tap...")
    i = 0
    try:
        while True:
            i += 1
            label = args.label or f"live_{i:03d}"
            ns = argparse.Namespace(
                device=args.device,
                sample_rate=args.sample_rate,
                channels=args.channels,
                seconds=args.seconds,
                out=args.out,
                label=label,
            )
            rc = cmd_record(ns)
            if rc != 0:
                return rc
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


def cmd_gold_run(args: argparse.Namespace) -> int:
    """Dispatch to gold-run module."""
    from tap_tone.cli.gold_run import main as gold_run_main
    
    gold_argv = []
    gold_argv.extend(["--specimen-id", args.specimen_id])
    gold_argv.extend(["--device", str(args.device)])
    gold_argv.extend(["--out-dir", str(args.out_dir)])
    if args.points != 3:
        gold_argv.extend(["--points", str(args.points)])
    if args.dry_run:
        gold_argv.append("--dry-run")
    if args.json:
        gold_argv.append("--json")
    if args.ingest:
        gold_argv.append("--ingest")
    if args.session_id:
        gold_argv.extend(["--session-id", args.session_id])
    if args.batch_label:
        gold_argv.extend(["--batch-label", args.batch_label])
    return gold_run_main(gold_argv)


def cmd_gui(_args: argparse.Namespace) -> int:
    """Launch the Tkinter GUI."""
    try:
        from tap_tone_pi.gui.app import App
    except ImportError:
        from gui.app import App
    
    app = App()
    app.mainloop()
    return 0


def cmd_phase2(args: argparse.Namespace) -> int:
    """Run Phase 2 ODS workflow."""
    import subprocess
    import sys
    
    argv = [sys.executable, "scripts/phase2_slice.py", "run"]
    if args.synthetic:
        argv.append("--synthetic")
    if args.grid:
        argv.extend(["--grid", args.grid])
    if args.out:
        argv.extend(["--out", args.out])
    if args.device:
        argv.extend(["--device", str(args.device)])
    
    return subprocess.call(argv)


def cmd_chladni(args: argparse.Namespace) -> int:
    """Run Chladni pattern analysis."""
    import subprocess
    import sys
    
    if args.subcommand == "peaks":
        argv = [
            sys.executable, "-m", "tap_tone_pi.chladni.peaks_from_wav",
            "--wav", args.wav,
            "--out", args.out,
        ]
        if args.min_hz:
            argv.extend(["--min-hz", str(args.min_hz)])
        if args.max_hz:
            argv.extend(["--max-hz", str(args.max_hz)])
    elif args.subcommand == "index":
        argv = [
            sys.executable, "-m", "tap_tone_pi.chladni.index_patterns",
            "--peaks-json", args.peaks_json,
            "--plate-id", args.plate_id,
            "--out", args.out,
            "--images", *args.images,
        ]
    else:
        print(f"Unknown chladni subcommand: {args.subcommand}", file=sys.stderr)
        return 1
    
    return subprocess.call(argv)


def cmd_bending(args: argparse.Namespace) -> int:
    """Run bending MOE calculation."""
    import subprocess
    import sys
    
    argv = [
        sys.executable, "-m", "tap_tone_pi.bending.merge_and_moe",
        "--load", args.load,
        "--disp", args.disp,
        "--out-dir", args.out_dir,
        "--method", args.method,
        "--span", str(args.span),
        "--width", str(args.width),
        "--thickness", str(args.thickness),
    ]
    if args.rate:
        argv.extend(["--rate", str(args.rate)])
    
    return subprocess.call(argv)


def _print_summary(label: str | None, res) -> None:
    """Print analysis summary to console."""
    print("")
    if label:
        print(f"Label: {label}")
    print(f"Dominant: {res.dominant_hz if res.dominant_hz else 'n/a'} Hz")
    print(f"RMS: {res.rms:.6f}   Clipped: {res.clipped}   Confidence: {res.confidence:.2f}")
    if res.peaks:
        print("Top peaks:")
        for p in res.peaks[:8]:
            print(f"  - {p.freq_hz:8.2f} Hz   mag={p.magnitude:.3f}")
    else:
        print("No peaks detected (try higher gain or quieter room).")
    print("")


def build_parser() -> argparse.ArgumentParser:
    """Build the unified CLI argument parser."""
    p = argparse.ArgumentParser(
        prog="ttp",
        description="Tap Tone Pi — Acoustic measurement instrument (v2.0.0)"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # devices
    p_dev = sub.add_parser("devices", help="List audio devices")
    p_dev.set_defaults(fn=cmd_devices)

    # record
    p_rec = sub.add_parser("record", help="Record one window and analyze")
    p_rec.add_argument("--device", type=int, default=None, help="Input device index")
    p_rec.add_argument("--sample-rate", type=int, default=48000)
    p_rec.add_argument("--channels", type=int, default=1)
    p_rec.add_argument("--seconds", type=float, default=2.5)
    p_rec.add_argument("--out", type=str, required=True, help="Output directory")
    p_rec.add_argument("--label", type=str, default=None, help="Tap point label")
    p_rec.set_defaults(fn=cmd_record)

    # live
    p_live = sub.add_parser("live", help="Loop record+analyze")
    p_live.add_argument("--device", type=int, default=None)
    p_live.add_argument("--sample-rate", type=int, default=48000)
    p_live.add_argument("--channels", type=int, default=1)
    p_live.add_argument("--seconds", type=float, default=2.5)
    p_live.add_argument("--out", type=str, required=True)
    p_live.add_argument("--label", type=str, default=None)
    p_live.set_defaults(fn=cmd_live)

    # gold-run
    p_gold = sub.add_parser("gold-run", help="One-command Gold Standard Run")
    p_gold.add_argument("--specimen-id", required=True, help="Specimen identifier")
    p_gold.add_argument("--device", required=True, help="Audio device")
    p_gold.add_argument("--out-dir", required=True, help="Output directory")
    p_gold.add_argument("--points", type=int, default=3)
    p_gold.add_argument("--session-id", help="Custom session ID")
    p_gold.add_argument("--batch-label", help="Batch label")
    p_gold.add_argument("--dry-run", action="store_true")
    p_gold.add_argument("--json", action="store_true")
    p_gold.add_argument("--ingest", action="store_true")
    p_gold.set_defaults(fn=cmd_gold_run)

    # gui
    p_gui = sub.add_parser("gui", help="Launch Tkinter GUI")
    p_gui.set_defaults(fn=cmd_gui)

    # phase2
    p_p2 = sub.add_parser("phase2", help="Phase 2 ODS workflow")
    p_p2.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    p_p2.add_argument("--grid", help="Grid definition JSON")
    p_p2.add_argument("--out", help="Output directory")
    p_p2.add_argument("--device", type=int, help="Audio device")
    p_p2.set_defaults(fn=cmd_phase2)

    # chladni
    p_ch = sub.add_parser("chladni", help="Chladni pattern analysis")
    ch_sub = p_ch.add_subparsers(dest="subcommand", required=True)
    
    p_ch_peaks = ch_sub.add_parser("peaks", help="Extract peaks from WAV")
    p_ch_peaks.add_argument("--wav", required=True)
    p_ch_peaks.add_argument("--out", required=True)
    p_ch_peaks.add_argument("--min-hz", type=float, default=50)
    p_ch_peaks.add_argument("--max-hz", type=float, default=2000)
    
    p_ch_index = ch_sub.add_parser("index", help="Index patterns to frequencies")
    p_ch_index.add_argument("--peaks-json", required=True)
    p_ch_index.add_argument("--plate-id", required=True)
    p_ch_index.add_argument("--out", required=True)
    p_ch_index.add_argument("--images", nargs="+", required=True)
    
    p_ch.set_defaults(fn=cmd_chladni)

    # bending
    p_bend = sub.add_parser("bending", help="Bending MOE calculation")
    p_bend.add_argument("--load", required=True, help="Load series JSON")
    p_bend.add_argument("--disp", required=True, help="Displacement series JSON")
    p_bend.add_argument("--out-dir", required=True)
    p_bend.add_argument("--method", default="3point", choices=["3point", "4point"])
    p_bend.add_argument("--span", type=float, required=True, help="Span in mm")
    p_bend.add_argument("--width", type=float, required=True, help="Width in mm")
    p_bend.add_argument("--thickness", type=float, required=True, help="Thickness in mm")
    p_bend.add_argument("--rate", type=float, default=50, help="Resample rate Hz")
    p_bend.set_defaults(fn=cmd_bending)

    return p


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
