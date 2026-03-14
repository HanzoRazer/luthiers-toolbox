"""
G-code File Reader

Parse G-code files and extract summary statistics.
Handles file I/O, validation, and summary generation.
"""
from __future__ import annotations

import math
import os
import re
from typing import Dict, List, Optional, Tuple

from .lexer import parse_words, strip_comments
from .types import Move, Summary


def update_bbox(summary: Summary, pt: Tuple[float, float, float]) -> None:
    """Expand summary bounding box to include point."""
    for i in range(3):
        summary.bbox_min[i] = min(summary.bbox_min[i], pt[i])
        summary.bbox_max[i] = max(summary.bbox_max[i], pt[i])


def add_length(
    summary: Summary,
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    rapid: bool,
) -> None:
    """Add distance between points to summary totals."""
    d = math.dist(a, b)
    summary.length_total += d
    if rapid:
        summary.length_rapid += d
    else:
        summary.length_feed += d


def approx_arc_bbox(
    summary: Summary,
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    ijk: Tuple[float, float, float],
    plane: str,
) -> None:
    """Conservative arc bbox: include start, end, and center point."""
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
        print(f"Warning: Large file ({file_size / 1024 / 1024:.1f} MB) - parsing may take time")

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
                    if g == 20:
                        units = "inch"
                    elif g == 21:
                        units = "mm"
                    elif g == 90:
                        absolute = True
                    elif g == 91:
                        absolute = False
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
                if rapid:
                    summary.rapid_count += 1
                if not rapid and not is_arc:
                    summary.feed_count += 1
                if is_arc:
                    summary.arc_count += 1

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
    except (ValueError, TypeError, IndexError, KeyError, AttributeError) as e:
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
