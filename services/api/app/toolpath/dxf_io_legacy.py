# services/api/app/toolpath/dxf_io_legacy.py

"""
Legacy DXF I/O Module

Provides DXF parsing (import) and R12-style DXF writing (export) functions.

This module handles:
- Reading DXF files to extract geometry as MLPaths
- Writing MLPaths to R12-compatible DXF format

Supported DXF entities for import:
- LINE
- POLYLINE (with VERTEX entities)
- LWPOLYLINE

Supported DXF entities for export:
- POLYLINE + VERTEX + SEQEND (for closed paths)
- LINE (for open paths)
"""

from __future__ import annotations

from typing import Iterable, List, Optional, TextIO, Tuple

from . import MLPath, Point2D


# ---------------------------------------------------------------------------
# DXF → MLPath (Import)
# ---------------------------------------------------------------------------


def read_dxf_to_mlpaths(stream: TextIO) -> List[MLPath]:
    """
    Parse a DXF file stream and extract geometry as MLPaths.

    Supports:
    - LINE entities
    - POLYLINE entities (with VERTEX)
    - LWPOLYLINE entities

    Args:
        stream: Text stream of DXF content

    Returns:
        List of MLPath objects representing the geometry
    """
    content = stream.read()
    pairs = _to_code_value_pairs(content)
    mlpaths: List[MLPath] = []

    idx = 0
    while idx < len(pairs):
        code, value = pairs[idx]

        # Look for entity start
        if code == 0:
            if value == "LINE":
                path, idx = _parse_line_entity(pairs, idx + 1)
                if path:
                    mlpaths.append(path)
                continue

            if value == "POLYLINE":
                path, idx = _parse_polyline_entity(pairs, idx + 1)
                if path:
                    mlpaths.append(path)
                continue

            if value == "LWPOLYLINE":
                path, idx = _parse_lwpolyline_entity(pairs, idx + 1)
                if path:
                    mlpaths.append(path)
                continue

        idx += 1

    return mlpaths


def _to_code_value_pairs(content: str) -> List[Tuple[int, str]]:
    """
    Convert DXF content to list of (code, value) pairs.

    DXF files alternate between group codes (integers) and values (strings).
    """
    lines = content.strip().split("\n")
    pairs: List[Tuple[int, str]] = []

    i = 0
    while i + 1 < len(lines):
        try:
            code = int(lines[i].strip())
            value = lines[i + 1].strip()
            pairs.append((code, value))
            i += 2
        except ValueError:
            i += 1

    return pairs


def _parse_line_entity(
    pairs: List[Tuple[int, str]],
    idx: int,
) -> Tuple[Optional[MLPath], int]:
    """
    Parse a LINE entity.

    LINE uses codes 10/20 for start point and 11/21 for end point.
    """
    x1 = y1 = x2 = y2 = None

    while idx < len(pairs):
        code, value = pairs[idx]

        if code == 0:
            # Next entity
            break

        if code == 10:
            x1 = float(value)
        elif code == 20:
            y1 = float(value)
        elif code == 11:
            x2 = float(value)
        elif code == 21:
            y2 = float(value)

        idx += 1

    if all(v is not None for v in (x1, y1, x2, y2)):
        return MLPath(points=[(x1, y1), (x2, y2)], is_closed=False), idx

    return None, idx


def _parse_polyline_entity(
    pairs: List[Tuple[int, str]],
    idx: int,
) -> Tuple[Optional[MLPath], int]:
    """
    Parse a POLYLINE entity (followed by VERTEX entities, ended by SEQEND).
    """
    points: List[Point2D] = []

    while idx < len(pairs):
        code, value = pairs[idx]

        if code == 0 and value == "VERTEX":
            # parse vertices
            idx = _parse_vertices(pairs, idx, points)
            continue

        if code == 0 and value == "SEQEND":
            idx += 1
            break

        # End of ENTITIES or start of another entity
        if code == 0 and value not in ("VERTEX", "SEQEND"):
            break

        idx += 1

    if points:
        is_closed = len(points) > 2 and points[0] == points[-1]
        return MLPath(points=points, is_closed=is_closed), idx

    return None, idx


def _parse_vertices(
    pairs: List[Tuple[int, str]],
    idx: int,
    points: List[Point2D],
) -> int:
    """
    Parse VERTEX entities until SEQEND or non-VERTEX entity.
    idx is positioned at '0, VERTEX'.
    """
    while idx < len(pairs):
        code, value = pairs[idx]
        if code == 0 and value != "VERTEX":
            # next entity; return
            break

        # one VERTEX
        x = y = None
        idx += 1
        while idx < len(pairs):
            c, v = pairs[idx]
            if c == 0:
                # next entity (VERTEX or SEQEND)
                break
            if c == 10:
                x = float(v)
            elif c == 20:
                y = float(v)
            idx += 1

        if x is not None and y is not None:
            points.append((x, y))

    return idx


def _parse_lwpolyline_entity(
    pairs: List[Tuple[int, str]],
    idx: int,
) -> Tuple[Optional[MLPath], int]:
    """
    Parse LWPOLYLINE entity.

    We look for (10, x), (20, y) pairs.
    For simplicity, we ignore bulge (42) and flags (70) here.
    """
    points: List[Point2D] = []

    while idx < len(pairs):
        code, value = pairs[idx]

        if code == 0:
            # next entity
            break

        if code == 10:
            # x coordinate, expect 20 for y soon
            x = float(value)
            # search ahead for 20
            y = None
            j = idx + 1
            while j < len(pairs):
                c2, v2 = pairs[j]
                if c2 == 20:
                    y = float(v2)
                    break
                if c2 == 0:
                    # new entity, bail from this search
                    break
                j += 1

            if y is not None:
                points.append((x, y))

        idx += 1

    if points:
        is_closed = len(points) > 2 and points[0] == points[-1]
        return MLPath(points=points, is_closed=is_closed), idx

    return None, idx


# ---------------------------------------------------------------------------
# MLPath → DXF (R12-style Export)
# ---------------------------------------------------------------------------


def write_mlpaths_to_dxf_r12(paths: Iterable[MLPath], stream: TextIO) -> None:
    """
    Write a minimal R12-compatible DXF (ENTITIES section only).

    - Closed MLPaths become POLYLINE + VERTEX + SEQEND.
    - Open MLPaths are emitted as a series of LINE entities.

    Note: Header/footer are not written here — this function writes only ENTITIES.
    Use export_mlpaths_to_dxf() from dxf_exporter.py for complete DXF files.

    Args:
        paths: Iterable of MLPath objects
        stream: Text stream to write to
    """
    for path in paths:
        pts = path.points
        if not pts:
            continue

        if path.is_closed and len(pts) >= 3:
            _write_polyline_r12(pts, stream)
        else:
            _write_lines_r12(pts, stream)


def _write_polyline_r12(points: List[Point2D], stream: TextIO) -> None:
    """Write a closed path as POLYLINE + VERTEX + SEQEND."""
    stream.write("0\nPOLYLINE\n8\n0\n66\n1\n")
    for (x, y) in points:
        stream.write("0\nVERTEX\n8\n0\n10\n")
        stream.write(f"{x:.6f}\n20\n{y:.6f}\n")
    stream.write("0\nSEQEND\n")


def _write_lines_r12(points: List[Point2D], stream: TextIO) -> None:
    """Write an open path as a series of LINE entities."""
    for (p1, p2) in zip(points[:-1], points[1:]):
        x1, y1 = p1
        x2, y2 = p2
        stream.write("0\nLINE\n8\n0\n10\n")
        stream.write(f"{x1:.6f}\n20\n{y1:.6f}\n11\n")
        stream.write(f"{x2:.6f}\n21\n{y2:.6f}\n")
