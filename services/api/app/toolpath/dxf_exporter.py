# services/api/app/toolpath/dxf_exporter.py

"""
Version-Aware DXF Exporter

Provides DXF export with version control (R12, R14, R18).

Features:
- Minimal DXF header with correct $ACADVER
- ENTITIES section with geometry
- Version-appropriate entity types
- Complete DXF file structure (header, entities, footer)

This is the main entry point for DXF export; it wraps the legacy writer
with proper headers and footers.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, TextIO

from . import MLPath
from .dxf_io_legacy import write_mlpaths_to_dxf_r12


class DXFVersion(str, Enum):
    """Supported DXF file versions."""

    R12 = "R12"
    R14 = "R14"
    R18 = "R18"


class DXFExportOptions:
    """Options for DXF export."""

    def __init__(
        self,
        dxf_version: DXFVersion = DXFVersion.R12,
        prefer_lwpolyline: bool | None = None,
    ) -> None:
        """
        Initialize export options.

        Args:
            dxf_version: Target DXF version (R12, R14, R18)
            prefer_lwpolyline: If True and version >= R14, use LWPOLYLINE
        """
        self.dxf_version = dxf_version
        self.prefer_lwpolyline = prefer_lwpolyline

    @property
    def use_lwpolyline(self) -> bool:
        """Whether to use LWPOLYLINE (requires R14+ and explicit preference)."""
        return (
            self.dxf_version in (DXFVersion.R14, DXFVersion.R18)
            and bool(self.prefer_lwpolyline)
        )


def export_mlpaths_to_dxf(
    paths: Iterable[MLPath],
    stream: TextIO,
    options: DXFExportOptions | None = None,
) -> None:
    """
    Version-aware DXF exporter.

    Exports MLPaths to a complete DXF file with:
    - Proper header section (with $ACADVER)
    - ENTITIES section with geometry
    - Footer (ENDSEC + EOF)

    Args:
        paths: Iterable of MLPath objects to export
        stream: Text stream to write to
        options: Export options (version, LWPOLYLINE preference)

    Notes:
        - R12: Uses POLYLINE + VERTEX + LINE (maximum compatibility)
        - R14/R18: Header advertises later version; entities are currently kept
          R12-style for maximum compatibility. In a later wave we can switch to
          true LWPOLYLINE when use_lwpolyline is True.
    """
    if options is None:
        options = DXFExportOptions()

    _write_header(stream, options)

    # For now, we always use the R12 entity writer, regardless of version.
    # This guarantees that any DXF consumer that handled your original R12
    # exports will still work, while we keep the door open for richer R14/R18.
    if options.use_lwpolyline:
        _write_entities_lwpolyline(paths, stream)
    else:
        write_mlpaths_to_dxf_r12(paths, stream)

    _write_footer(stream)


def _write_header(stream: TextIO, options: DXFExportOptions) -> None:
    """
    Write minimal DXF header that sets $ACADVER to the desired version.

    This is intentionally very small; most consumers don't require more.
    """
    acadver = {
        DXFVersion.R12: "AC1009",  # R12
        DXFVersion.R14: "AC1014",  # R14
        DXFVersion.R18: "AC1018",  # 2004 (roughly R18 family)
    }[options.dxf_version]

    stream.write("0\nSECTION\n2\nHEADER\n")
    stream.write("9\n$ACADVER\n1\n")
    stream.write(f"{acadver}\n")
    stream.write("0\nENDSEC\n")
    stream.write("0\nSECTION\n2\nENTITIES\n")


def _write_footer(stream: TextIO) -> None:
    """Write DXF footer (end of ENTITIES section + EOF marker)."""
    stream.write("0\nENDSEC\n0\nEOF\n")


def _write_entities_lwpolyline(paths: Iterable[MLPath], stream: TextIO) -> None:
    """
    R14/R18 enhanced writer: emit LWPOLYLINE entities.
    
    LWPOLYLINE is more compact than the old POLYLINE+VERTEX+SEQEND format
    and is the preferred entity type for R14+ DXF files.
    
    Format structure:
    - Group 0: LWPOLYLINE
    - Group 8: Layer name (0 = default)
    - Group 90: Number of vertices
    - Group 70: Polyline flag (1 = closed, 0 = open)
    - Group 10/20: X/Y coordinates for each vertex
    """
    for path in paths:
        pts = path.points
        if not pts:
            continue
        
        if len(pts) >= 2:
            _write_lwpolyline(pts, path.is_closed, stream)


def _write_lwpolyline(
    points: list,
    is_closed: bool,
    stream: TextIO,
) -> None:
    """
    Write a path as a single LWPOLYLINE entity.
    
    LWPOLYLINE format (R14+):
    - 0: LWPOLYLINE
    - 8: Layer (0)
    - 90: Vertex count
    - 70: Flags (1=closed, 0=open)
    - 10/20: X/Y for each vertex
    
    Args:
        points: List of (x, y) coordinate tuples
        is_closed: Whether to close the polyline
        stream: Output text stream
    """
    # Start LWPOLYLINE entity
    stream.write("0\nLWPOLYLINE\n")
    # Layer 0
    stream.write("8\n0\n")
    # Vertex count
    stream.write(f"90\n{len(points)}\n")
    # Flags: 1 = closed, 0 = open
    flags = 1 if is_closed else 0
    stream.write(f"70\n{flags}\n")
    
    # Write each vertex
    for (x, y) in points:
        stream.write(f"10\n{x:.6f}\n")
        stream.write(f"20\n{y:.6f}\n")
