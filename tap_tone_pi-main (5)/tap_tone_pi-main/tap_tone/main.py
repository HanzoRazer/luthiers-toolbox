from __future__ import annotations

import argparse
import sys

from .config import CaptureConfig, AnalysisConfig
from .capture import list_devices, record_audio
from .analysis import analyze_tap
from .storage import persist_capture
from .ui_simple import print_summary

def cmd_devices(_: argparse.Namespace) -> int:
    devs = list_devices()
    for d in devs:
        print(f'[{d["index"]}] {d["name"]} (in={d["max_input_channels"]}, out={d["max_output_channels"]})')
    return 0

def cmd_record(args: argparse.Namespace) -> int:
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

    print_summary(args.label, res)

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
    from .cli.gold_run import main as gold_run_main
    # Pass remaining args to gold-run's own parser
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tap-tone", description="Offline tap tone analyzer")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_dev = sub.add_parser("devices", help="List audio devices")
    p_dev.set_defaults(fn=cmd_devices)

    p_rec = sub.add_parser("record", help="Record one window and analyze")
    p_rec.add_argument("--device", type=int, default=None, help="Input device index (see devices)")
    p_rec.add_argument("--sample-rate", type=int, default=48000)
    p_rec.add_argument("--channels", type=int, default=1)
    p_rec.add_argument("--seconds", type=float, default=2.5)
    p_rec.add_argument("--out", type=str, required=True, help="Output directory root")
    p_rec.add_argument("--label", type=str, default=None, help="Tap point label")
    p_rec.set_defaults(fn=cmd_record)

    p_live = sub.add_parser("live", help="Loop record+analyze")
    p_live.add_argument("--device", type=int, default=None)
    p_live.add_argument("--sample-rate", type=int, default=48000)
    p_live.add_argument("--channels", type=int, default=1)
    p_live.add_argument("--seconds", type=float, default=2.5)
    p_live.add_argument("--out", type=str, required=True)
    p_live.add_argument("--label", type=str, default=None)
    p_live.set_defaults(fn=cmd_live)

    p_gold = sub.add_parser("gold-run", help="One-command Gold Standard Run")
    p_gold.add_argument("--specimen-id", required=True, help="Specimen identifier")
    p_gold.add_argument("--device", required=True, help="Audio device (index or name)")
    p_gold.add_argument("--out-dir", required=True, help="Output directory for ZIP")
    p_gold.add_argument("--points", type=int, default=3, help="Number of points (default: 3)")
    p_gold.add_argument("--session-id", help="Custom session ID")
    p_gold.add_argument("--batch-label", help="Batch label for grouping")
    p_gold.add_argument("--dry-run", action="store_true", help="Preview mode, no capture")
    p_gold.add_argument("--json", action="store_true", help="Output JSON summary")
    p_gold.add_argument("--ingest", action="store_true", help="Ingest to ToolBox")
    p_gold.set_defaults(fn=cmd_gold_run)

    return p

def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    rc = args.fn(args)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
