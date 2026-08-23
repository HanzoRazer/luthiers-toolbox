#!/usr/bin/env python3
"""Extract data-card candidate frames from an MB Sound (or similar) video.

Requires ffmpeg on PATH. Does not invent measurements — frames only.

Examples:
  python scripts/mb_sound_extract_frames.py \\
    --video /data/mb.mp4 --sample-id mb_sound_001 --mode scene

  python scripts/mb_sound_extract_frames.py \\
    --video /data/mb.mp4 --sample-id mb_sound_001 --mode interval --interval-sec 2
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "reference" / "mb-sound" / "staging" / "frames"


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg not found on PATH")
    return path


def extract_scene(ffmpeg: str, video: Path, out_dir: Path, scene_threshold: float) -> None:
    # Scene-change filter; threshold ~0.3–0.4 typical for hard cuts to data cards
    pattern = str(out_dir / "frame_%04d.png")
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-i",
        str(video),
        "-vf",
        f"select='gt(scene,{scene_threshold})',showinfo",
        "-vsync",
        "vfr",
        pattern,
    ]
    subprocess.run(cmd, check=True)


def extract_interval(ffmpeg: str, video: Path, out_dir: Path, interval_sec: float) -> None:
    pattern = str(out_dir / "frame_%04d.png")
    fps = 1.0 / interval_sec if interval_sec > 0 else 0.5
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-i",
        str(video),
        "-vf",
        f"fps={fps}",
        pattern,
    ]
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--sample-id", required=True, help="Stable id, e.g. mb_sound_adirondack_001")
    p.add_argument("--mode", choices=("scene", "interval"), default="scene")
    p.add_argument("--interval-sec", type=float, default=2.0)
    p.add_argument("--scene-threshold", type=float, default=0.35)
    p.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    args = p.parse_args(argv)

    if not args.video.is_file():
        raise SystemExit(f"video not found: {args.video}")

    out_dir = args.out_root / args.sample_id
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = _require_ffmpeg()

    if args.mode == "scene":
        extract_scene(ffmpeg, args.video, out_dir, args.scene_threshold)
    else:
        extract_interval(ffmpeg, args.video, out_dir, args.interval_sec)

    frames = sorted(out_dir.glob("frame_*.png"))
    print(f"wrote {len(frames)} frames → {out_dir}")
    if not frames:
        print(
            "warning: zero frames; try --mode interval or lower --scene-threshold",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
