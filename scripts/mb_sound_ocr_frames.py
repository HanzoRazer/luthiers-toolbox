#!/usr/bin/env python3
"""OCR extracted MB Sound frames with tesseract (optional dependency).

Writes docs/reference/mb-sound/staging/ocr/<sample_id>.txt

  python scripts/mb_sound_ocr_frames.py --sample-id mb_sound_001 --lang spa+eng
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "docs" / "reference" / "mb-sound" / "staging" / "frames"
OCR_DIR = ROOT / "docs" / "reference" / "mb-sound" / "staging" / "ocr"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample-id", required=True)
    p.add_argument("--lang", default="spa+eng")
    p.add_argument("--frames-root", type=Path, default=FRAMES)
    p.add_argument("--ocr-dir", type=Path, default=OCR_DIR)
    args = p.parse_args(argv)

    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise SystemExit(
            "tesseract not found. Install tesseract-ocr + spa/eng packs, "
            "or key fields manually into staging/rows.jsonl"
        )

    frame_dir = args.frames_root / args.sample_id
    frames = sorted(frame_dir.glob("frame_*.png"))
    if not frames:
        raise SystemExit(f"no frames in {frame_dir}")

    args.ocr_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.ocr_dir / f"{args.sample_id}.txt"
    chunks: list[str] = []
    for frame in frames:
        proc = subprocess.run(
            [tesseract, str(frame), "stdout", "-l", args.lang],
            check=True,
            capture_output=True,
            text=True,
        )
        chunks.append(f"===== {frame.name} =====\n{proc.stdout.strip()}\n")

    out_path.write_text("\n".join(chunks), encoding="utf-8")
    print(f"wrote OCR dump → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
