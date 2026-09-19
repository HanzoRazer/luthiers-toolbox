"""Streaming sheet-border removal for R12 DXF. Reference implementation for the dev order.

The ezdxf version of this (parse -> delete -> rewrite) costs a full document round-trip to
remove ~2% of entities: measured at 122 s for 462k entities and still running past 900 s on a
1M-entity file. That is fine at a bench and unacceptable as a pipeline stage, which is why
DEV_ORDER_RESTORED_BASELINE_FALLBACK.md section 7a flags it.

This does the same job by streaming the DXF text. An R12 LINE entity is a fixed group-code
block, so the file can be scanned for its 10/20/11/21 pairs without building a document:

    pass 1  read the 10/20/11/21 values, compute the drawing bounding box
    pass 2  copy the file through, dropping LINE blocks that lie on the border

A border segment is defined geometrically, with no guessing: BOTH endpoints within `margin` of
the same bounding-box edge, AND the segment running parallel to that edge within `tol`.
Identical rule to the ezdxf version, so results are comparable.

Nothing else in the file is touched -- header, tables, blocks and non-LINE entities pass
through byte for byte.

    py -3.11 strip_border_streaming.py <in.dxf> <out.dxf> [--margin 6.0] [--tol 1.0]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path


def _blocks(lines: list[str]):
    """Yield (start, end) index pairs for each '0/<TYPE>' block in the file."""
    starts = [i for i in range(0, len(lines) - 1, 2) if lines[i].strip() == "0"]
    for a, b in zip(starts, starts[1:] + [len(lines)]):
        yield a, b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--margin", type=float, default=6.0)
    ap.add_argument("--tol", type=float, default=1.0)
    args = ap.parse_args()

    t0 = time.time()
    raw = args.src.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"read {len(raw):,} lines in {time.time()-t0:.1f}s")

    # ---- pass 1: collect endpoints of every LINE, and the bounding box
    coords: dict[int, tuple[float, float, float, float]] = {}
    xs_min = ys_min = float("inf")
    xs_max = ys_max = float("-inf")
    for a, b in _blocks(raw):
        if raw[a + 1].strip() != "LINE":
            continue
        v: dict[str, float] = {}
        for i in range(a + 2, b - 1, 2):
            code = raw[i].strip()
            if code in ("10", "20", "11", "21"):
                try:
                    v[code] = float(raw[i + 1])
                except ValueError:
                    pass
            if len(v) == 4:
                break
        if len(v) == 4:
            x1, y1, x2, y2 = v["10"], v["20"], v["11"], v["21"]
            coords[a] = (x1, y1, x2, y2)
            xs_min = min(xs_min, x1, x2)
            xs_max = max(xs_max, x1, x2)
            ys_min = min(ys_min, y1, y2)
            ys_max = max(ys_max, y1, y2)

    if not coords:
        print("no LINE entities found")
        return 1
    print(f"{len(coords):,} LINE entities, extent "
          f"{xs_max-xs_min:.1f} x {ys_max-ys_min:.1f} mm")

    # ---- decide which are border
    m, tol = args.margin, args.tol
    drop: set[int] = set()
    for a, (x1, y1, x2, y2) in coords.items():
        vertical = abs(x1 - x2) < tol
        horizontal = abs(y1 - y2) < tol
        near_l = abs(x1 - xs_min) < m and abs(x2 - xs_min) < m
        near_r = abs(x1 - xs_max) < m and abs(x2 - xs_max) < m
        near_b = abs(y1 - ys_min) < m and abs(y2 - ys_min) < m
        near_t = abs(y1 - ys_max) < m and abs(y2 - ys_max) < m
        if ((near_l or near_r) and vertical) or ((near_b or near_t) and horizontal):
            drop.add(a)
    print(f"border: {len(drop):,} segments ({len(drop)/len(coords)*100:.2f}%)")

    # ---- pass 2: copy through, skipping the dropped blocks
    out: list[str] = []
    skip_until = -1
    for a, b in _blocks(raw):
        if a in drop:
            skip_until = b
            continue
        if a < skip_until:
            continue
        out.extend(raw[a:b])
    # anything before the first block (rare) is preserved
    first = next(iter(_blocks(raw)))[0]
    head = raw[:first]
    args.dst.write_text("\n".join(head + out) + "\n", encoding="utf-8")

    kept = len(coords) - len(drop)
    print(f"-> {args.dst.name}  {kept:,} LINE kept  "
          f"{args.dst.stat().st_size/1e6:.1f} MB  total {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
