"""
G-code Reporting

Human-readable reports, CSV export, and JSON summary generation.
"""
from __future__ import annotations

import csv
import json
from typing import List, Optional

from .types import Move, Summary


def fmt_num(v: Optional[float], units: str = "", none: str = "—") -> str:
    """Format numeric value with optional units, handling None."""
    if v is None:
        return none
    if units:
        return f"{v:.4f} {units}"
    return f"{v:.4f}"


def print_report(summary: Summary, moves: List[Move], pretty: bool = False) -> None:
    """Print human-readable G-code summary report."""
    u = "in" if summary.units == "inch" else "mm"
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         G-code Summary - The Production Shop                ║")
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
    print("📐 Program Bounds")
    print("─" * 60)
    x_span = summary.bbox_max[0] - summary.bbox_min[0]
    y_span = summary.bbox_max[1] - summary.bbox_min[1]
    z_span = summary.bbox_max[2] - summary.bbox_min[2]
    print(f"X: {fmt_num(summary.bbox_min[0], u)} .. {fmt_num(summary.bbox_max[0], u)}  (span: {x_span:.3f} {u})")
    print(f"Y: {fmt_num(summary.bbox_min[1], u)} .. {fmt_num(summary.bbox_max[1], u)}  (span: {y_span:.3f} {u})")
    print(f"Z: {fmt_num(summary.bbox_min[2], u)} .. {fmt_num(summary.bbox_max[2], u)}  (span: {z_span:.3f} {u})")
    print()
    print("📏 Total Travel")
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
    """Export moves to CSV file."""
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


def write_json(path: str, summary: Summary) -> None:
    """Export summary to JSON file."""
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def summary_to_dict(summary: Summary) -> dict:
    """Convert Summary to dictionary for JSON serialization."""
    return {
        "units": summary.units,
        "absolute": summary.absolute,
        "planes": summary.planes,
        "active_plane": summary.plane,
        "lines": summary.line_count,
        "filename": summary.filename,
        "file_size_bytes": summary.file_size_bytes,
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
        "estimated_time_minutes": summary.estimated_time_minutes,
        "notes": summary.notes,
        "warnings": summary.warnings,
        "errors": summary.errors,
    }
