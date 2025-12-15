#!/usr/bin/env python3
"""
gcode_reader.py — Enhanced G‑code (.nc/.gcode) reader & summarizer for Luthier's ToolBox.

Features
- Parses common Fanuc‑style G‑code (G0/G1/G2/G3, G20/G21, G90/G91, M3/M5, S, F, T, G17/18/19).
- Extracts summary: units, program bounds (XYZ), total travel, rapid vs feed distance,
  feedrate range, spindle RPMs, tool list, planes, arc count, line counts.
- Emits CSV of the motion path (optional) and JSON summary (optional).
- Prints a human‑readable report by default.
- Enhanced error handling and validation for CNC lutherie workflows.

Usage
  python gcode_reader.py path/to/file.nc
  python gcode_reader.py file.nc --csv path.csv --json summary.json
  python gcode_reader.py file.nc --pretty  # more verbose listing
  python gcode_reader.py file.nc --validate  # check for common issues
  python gcode_reader.py --help

Notes
- Bounding box for arcs (G2/G3) approximates by considering start, end, and arc center (I/J/K).
  This is conservative; if your arcs sweep past extrema, bbox may be slightly under‑estimated.
- Supports absolute (G90) and incremental (G91) modes; default is absolute.
- Units default to mm unless overridden by G20 (inch) / G21 (mm).
- Integrated with Luthier's ToolBox CNC pipeline for guitar lutherie projects.

Part of: Luthier's ToolBox - CNC Guitar Lutherie CAD/CAM System
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

WORD_RE = re.compile(r"([A-Za-z])([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)")
COMMENT_PAREN_RE = re.compile(r"\(.*?\)")
COMMENT_SEMI_RE = re.compile(r";.*$")


@dataclass
class Move:
    n: int
    code: str  # G0/G1/G2/G3 etc.
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]
    feed: Optional[float] = None
    rapid: bool = False
    arc: bool = False
    cw: bool = False
    plane: str = "G17"  # G17 XY, G18 XZ, G19 YZ
    tool: Optional[str] = None
    spindle: Optional[float] = None  # RPM
    raw: str = ""


@dataclass
class Summary:
    units: str = "mm"
    absolute: bool = True
    plane: str = "G17"
    line_count: int = 0
    motion_count: int = 0
    rapid_count: int = 0
    feed_count: int = 0
    arc_count: int = 0
    length_total: float = 0.0
    length_rapid: float = 0.0
    length_feed: float = 0.0
    bbox_min: List[float] = field(default_factory=lambda: [float("inf")] * 3)
    bbox_max: List[float] = field(default_factory=lambda: [float("-inf")] * 3)
    feed_min: Optional[float] = None
    feed_max: Optional[float] = None
    rpm_min: Optional[float] = None
    rpm_max: Optional[float] = None
    tools: List[str] = field(default_factory=list)
    planes: List[str] = field(default_factory=lambda: ["G17"])
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    filename: str = ""
    file_size_bytes: int = 0
    estimated_time_minutes: Optional[float] = None


def strip_comments(line: str) -> str:
    # Remove ( ... ) comments and ; trailing comments
    line = COMMENT_PAREN_RE.sub("", line)
    line = COMMENT_SEMI_RE.sub("", line)
    return line.strip()


def parse_words(line: str) -> Dict[str, float]:
    return {m.group(1).upper(): float(m.group(2)) for m in WORD_RE.finditer(line)}


def update_bbox(summary: Summary, pt: Tuple[float, float, float]) -> None:
    for i in range(3):
        summary.bbox_min[i] = min(summary.bbox_min[i], pt[i])
        summary.bbox_max[i] = max(summary.bbox_max[i], pt[i])


def dist(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return math.dist(a, b)


def add_length(summary: Summary, a: Tuple[float, float, float], b: Tuple[float, float, float], rapid: bool) -> None:
    d = dist(a, b)
    summary.length_total += d
    if rapid:
        summary.length_rapid += d
    else:
        summary.length_feed += d


def approx_arc_bbox(summary: Summary, start: Tuple[float, float, float], end: Tuple[float, float, float],
                    ijk: Tuple[float, float, float], plane: str) -> None:
    # Conservative: include start, end, and center‑point; this will over‑approximate a bit.
    cx, cy, cz = (start[0] + ijk[0], start[1] + ijk[1], start[2] + ijk[2])
    update_bbox(summary, start)
    update_bbox(summary, end)
    update_bbox(summary, (cx, cy, cz))


def validate_gcode(summary: Summary, moves: List[Move]) -> None:
    """Run validation checks and add warnings/errors to summary."""
    
    # Check for common issues
    if summary.motion_count == 0:
        summary.warnings.append("No motion commands found (G0/G1/G2/G3)")
    
    if summary.rpm_min is None and summary.motion_count > 0:
        summary.warnings.append("No spindle speed commands (S) found - manual spindle control?")
    
    if summary.feed_min is None and summary.feed_count > 0:
        summary.warnings.append("Feed moves without explicit feedrate (F) command")
    
    # Check for extremely fast feeds (potential safety issue)
    if summary.feed_max and summary.feed_max > 5000:
        summary.warnings.append(f"Very high feedrate detected: {summary.feed_max:.0f} {summary.units}/min")
    
    # Check for extremely slow feeds
    if summary.feed_min and summary.feed_min < 10:
        summary.warnings.append(f"Very low feedrate detected: {summary.feed_min:.1f} {summary.units}/min")
    
    # Check for high RPM (woodworking typically < 24000 RPM)
    if summary.rpm_max and summary.rpm_max > 24000:
        summary.warnings.append(f"Very high spindle speed: {summary.rpm_max:.0f} RPM")
    
    # Check bbox size (detect potential coordinate system issues)
    if summary.bbox_max[0] - summary.bbox_min[0] > 2000:  # 2 meters
        summary.warnings.append("X axis span > 2000mm - check coordinate system")
    if summary.bbox_max[1] - summary.bbox_min[1] > 2000:
        summary.warnings.append("Y axis span > 2000mm - check coordinate system")
    
    # Check for negative Z (common issue)
    if summary.bbox_min[2] < 0:
        summary.notes.append(f"Program goes below Z=0 (min Z: {summary.bbox_min[2]:.3f}mm)")
    
    # Estimate machining time
    if summary.feed_min and summary.length_feed > 0:
        avg_feed = (summary.feed_min + (summary.feed_max or summary.feed_min)) / 2
        time_minutes = summary.length_feed / avg_feed
        summary.estimated_time_minutes = time_minutes
        summary.notes.append(f"Estimated cut time: {time_minutes:.1f} minutes (excluding rapids)")


def parse_gcode(path: str, pretty: bool = False, validate: bool = False) -> Tuple[Summary, List[Move]]:
    """Parse G-code file and extract summary + move list.
    
    Args:
        path: Path to .nc or .gcode file
        pretty: If True, include verbose motion details
        validate: If True, run validation checks
    
    Returns:
        Tuple of (Summary, List[Move])
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid format
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"G-code file not found: {path}")
    
    file_size = os.path.getsize(path)
    if file_size == 0:
        raise ValueError(f"G-code file is empty: {path}")
    
    if file_size > 100 * 1024 * 1024:  # 100MB
        print(f"⚠️  Warning: Large file ({file_size / 1024 / 1024:.1f} MB) - parsing may take time")

    summary = Summary()
    summary.filename = os.path.basename(path)
    summary.file_size_bytes = file_size
    moves: List[Move] = []

    # modal state
    units = "mm"  # G21=mm, G20=inch
    absolute = True  # G90 abs / G91 inc
    plane = "G17"
    feed: Optional[float] = None
    rpm: Optional[float] = None
    tool: Optional[str] = None

    pos = [0.0, 0.0, 0.0]  # X Y Z current
    last_motion_code: Optional[str] = None

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for ln, raw_line in enumerate(f, start=1):
                summary.line_count += 1
                clean = strip_comments(raw_line)
                if not clean:
                    continue

                words = parse_words(clean)
                if not words:
                    continue

                # modal changes
                if "G" in words:
                    g = int(words.get("G", -1))
                    if g == 20: units = "inch"
                    elif g == 21: units = "mm"
                    elif g == 90: absolute = True
                    elif g == 91: absolute = False
                    elif g in (17, 18, 19):
                        plane = f"G{g}"
                        if plane not in summary.planes:
                            summary.planes.append(plane)

                if "F" in words:
                    feed = words["F"]
                    summary.feed_min = feed if summary.feed_min is None else min(summary.feed_min, feed)
                    summary.feed_max = feed if summary.feed_max is None else max(summary.feed_max, feed)

                if "S" in words:
                    rpm = words["S"]
                    summary.rpm_min = rpm if summary.rpm_min is None else min(summary.rpm_min, rpm)
                    summary.rpm_max = rpm if summary.rpm_max is None else max(summary.rpm_max, rpm)

                if "T" in words:
                    tool = f"T{int(words['T'])}"
                    if tool not in summary.tools:
                        summary.tools.append(tool)

                # motion?
                gcode_found = [m.group(0) for m in re.finditer(r"\bG(0|1|2|3)\b", clean, flags=re.IGNORECASE)]
                if gcode_found:
                    # choose the *last* in the line if multiple (common pattern)
                    code = gcode_found[-1].upper()
                    last_motion_code = code
                elif last_motion_code:
                    code = last_motion_code
                else:
                    # No motion on this line
                    summary.units = units
                    summary.absolute = absolute
                    summary.plane = plane
                    continue

                # target coordinates
                target = pos.copy()
                for axis, idx in (("X", 0), ("Y", 1), ("Z", 2)):
                    if axis in words:
                        val = words[axis]
                        if absolute:
                            target[idx] = val
                        else:
                            target[idx] += val

                start = tuple(pos)
                end = tuple(target)

                rapid = code in ("G0", "G00")
                is_arc = code in ("G2", "G02", "G3", "G03")
                cw = code in ("G2", "G02")

                mv = Move(
                    n=ln, code=code, start=start, end=end, feed=feed, rapid=rapid, arc=is_arc, cw=cw,
                    plane=plane, tool=tool, spindle=rpm, raw=clean
                )
                moves.append(mv)
                summary.motion_count += 1
                if rapid: summary.rapid_count += 1
                if not rapid and not is_arc: summary.feed_count += 1
                if is_arc: summary.arc_count += 1

                # update bbox / lengths
                if is_arc:
                    # read IJK if present (incremental from start in absolute mode per common dialect)
                    I = words.get("I", 0.0)
                    J = words.get("J", 0.0)
                    K = words.get("K", 0.0)
                    approx_arc_bbox(summary, start, end, (I, J, K), plane)
                    # length approx as chord (conservative). Exact arc length would need angle sweep.
                    add_length(summary, start, end, rapid=False)
                else:
                    update_bbox(summary, start)
                    update_bbox(summary, end)
                    add_length(summary, start, end, rapid=rapid)

                pos = target
                summary.units = units
                summary.absolute = absolute
                summary.plane = plane
    
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode G-code file (encoding issue): {e}")
    except Exception as e:
        raise ValueError(f"Error parsing G-code file at line {summary.line_count}: {e}")

    # normalize empty bbox (no motion)
    for i in range(3):
        if summary.bbox_min[i] == float("inf"):
            summary.bbox_min[i] = 0.0
        if summary.bbox_max[i] == float("-inf"):
            summary.bbox_max[i] = 0.0
    
    # Run validation if requested
    if validate:
        validate_gcode(summary, moves)

    return summary, moves


def fmt_num(v: Optional[float], units: str = "", none: str = "—") -> str:
    if v is None:
        return none
    if units:
        return f"{v:.4f} {units}"
    return f"{v:.4f}"


def print_report(summary: Summary, moves: List[Move], pretty: bool = False) -> None:
    u = "in" if summary.units == "inch" else "mm"
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         G‑code Summary - Luthier's ToolBox                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print(f"📄 File:           {summary.filename}")
    print(f"📊 Size:           {summary.file_size_bytes:,} bytes ({summary.file_size_bytes / 1024:.1f} KB)")
    print()
    print("⚙️  Program Configuration")
    print("─" * 60)
    print(f"Units:            {summary.units} ({u})")
    print(f"Coordinates:      {'absolute (G90)' if summary.absolute else 'incremental (G91)'}")
    print(f"Planes:           {', '.join(summary.planes)} (active {summary.plane})")
    print(f"Lines:            {summary.line_count:,}")
    print()
    print("🔧 Motion Statistics")
    print("─" * 60)
    print(f"Total motions:    {summary.motion_count:,}")
    print(f"  ├─ Rapids:      {summary.rapid_count:,} moves")
    print(f"  ├─ Feeds:       {summary.feed_count:,} moves")
    print(f"  └─ Arcs:        {summary.arc_count:,} moves")
    print()
    print(f"Feedrate range:   {fmt_num(summary.feed_min, u+'/min')} .. {fmt_num(summary.feed_max, u+'/min')}")
    print(f"Spindle RPM:      {fmt_num(summary.rpm_min, 'RPM')} .. {fmt_num(summary.rpm_max, 'RPM')}")
    print(f"Tools:            {', '.join(summary.tools) if summary.tools else '—'}")
    
    if summary.estimated_time_minutes:
        hours = int(summary.estimated_time_minutes / 60)
        mins = int(summary.estimated_time_minutes % 60)
        if hours > 0:
            print(f"⏱️  Estimated time:  {hours}h {mins}m (cut time only)")
        else:
            print(f"⏱️  Estimated time:  {mins} minutes (cut time only)")
    print()
    print("📏 Program Bounds")
    print("─" * 60)
    x_span = summary.bbox_max[0] - summary.bbox_min[0]
    y_span = summary.bbox_max[1] - summary.bbox_min[1]
    z_span = summary.bbox_max[2] - summary.bbox_min[2]
    print(f"X: {fmt_num(summary.bbox_min[0], u)} .. {fmt_num(summary.bbox_max[0], u)}  (span: {x_span:.3f} {u})")
    print(f"Y: {fmt_num(summary.bbox_min[1], u)} .. {fmt_num(summary.bbox_max[1], u)}  (span: {y_span:.3f} {u})")
    print(f"Z: {fmt_num(summary.bbox_min[2], u)} .. {fmt_num(summary.bbox_max[2], u)}  (span: {z_span:.3f} {u})")
    print()
    print("📐 Total Travel")
    print("─" * 60)
    print(f"Total distance:   {fmt_num(summary.length_total, u)}")
    print(f"  ├─ Rapids:      {fmt_num(summary.length_rapid, u)}")
    print(f"  └─ Feeds:       {fmt_num(summary.length_feed, u)}")
    
    # Print warnings
    if summary.warnings:
        print()
        print("⚠️  Warnings")
        print("─" * 60)
        for warning in summary.warnings:
            print(f"  • {warning}")
    
    # Print notes
    if summary.notes:
        print()
        print("📝 Notes")
        print("─" * 60)
        for note in summary.notes:
            print(f"  • {note}")
    
    # Print errors
    if summary.errors:
        print()
        print("❌ Errors")
        print("─" * 60)
        for error in summary.errors:
            print(f"  • {error}")

    if pretty:
        print("\nFirst 25 motions (start→end):")
        for mv in moves[:25]:
            code = mv.code
            tag = "RAPID" if mv.rapid else ("ARC" if mv.arc else "FEED")
            print(f"[{mv.n:>6}] {code:<3} {tag:<5}  "
                  f"({mv.start[0]:.4f},{mv.start[1]:.4f},{mv.start[2]:.4f}) → "
                  f"({mv.end[0]:.4f},{mv.end[1]:.4f},{mv.end[2]:.4f})  "
                  f"F={fmt_num(mv.feed)} S={fmt_num(mv.spindle)} T={mv.tool or '—'}")


def write_csv(path: str, moves: List[Move]) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "code", "type", "x0", "y0", "z0", "x1", "y1", "z1", "feed", "spindle", "tool", "plane"])
        for mv in moves:
            w.writerow([
                mv.n, mv.code, ("rapid" if mv.rapid else ("arc" if mv.arc else "feed")),
                f"{mv.start[0]:.6f}", f"{mv.start[1]:.6f}", f"{mv.start[2]:.6f}",
                f"{mv.end[0]:.6f}", f"{mv.end[1]:.6f}", f"{mv.end[2]:.6f}",
                "" if mv.feed is None else f"{mv.feed:.6f}",
                "" if mv.spindle is None else f"{mv.spindle:.6f}",
                mv.tool or "",
                mv.plane
            ])


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Read & summarize a G‑code (.nc/.gcode) file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s program.nc --pretty
  %(prog)s program.nc --validate --json summary.json
  %(prog)s program.nc --csv moves.csv --json summary.json
  
Integration with Luthier's ToolBox:
  This tool is integrated into server/pipelines/gcode_explainer/ for
  automated G-code analysis in CAM workflows.
        """
    )
    p.add_argument("file", help="Path to .nc or .gcode file")
    p.add_argument("--csv", help="Optional CSV path to write motion path")
    p.add_argument("--json", help="Optional JSON path to write summary")
    p.add_argument("--pretty", action="store_true", help="Print extra motion listing with enhanced formatting")
    p.add_argument("--validate", action="store_true", help="Run safety validation checks (speeds, coordinates, etc.)")
    p.add_argument("--quiet", action="store_true", help="Suppress report output (useful with --json)")
    args = p.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}", file=sys.stderr)
        return 1

    summary, moves = parse_gcode(args.file, pretty=args.pretty, validate=args.validate)
    
    if not args.quiet:
        print_report(summary, moves, pretty=args.pretty)

    if args.csv:
        write_csv(args.csv, moves)
        print(f"\nCSV path written: {args.csv} ({len(moves)} rows)")
    if args.json:
        obj = {
            "units": summary.units,
            "absolute": summary.absolute,
            "planes": summary.planes,
            "active_plane": summary.plane,
            "lines": summary.line_count,
            "motions": {
                "total": summary.motion_count,
                "rapid": summary.rapid_count,
                "feed": summary.feed_count,
                "arcs": summary.arc_count,
            },
            "feedrate": {"min": summary.feed_min, "max": summary.feed_max},
            "spindle_rpm": {"min": summary.rpm_min, "max": summary.rpm_max},
            "tools": summary.tools,
            "bbox": {"min": summary.bbox_min, "max": summary.bbox_max},
            "travel": {
                "total": summary.length_total,
                "rapid": summary.length_rapid,
                "feed": summary.length_feed,
            },
            "notes": summary.notes,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        print(f"JSON summary written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
