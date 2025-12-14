"""
Neck Taper Suite: DXF Exporter

Wave 17 - Instrument Geometry Integration

R12-safe DXF export using POLYLINE/VERTEX/SEQEND pattern for maximum
CAM compatibility with legacy systems.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from .taper_math import TaperInputs
from .neck_outline_generator import generate_neck_outline

Point = Tuple[float, float]


# ---------------------------------------------------------------------------
# Low-level R12 POLYLINE writer
# ---------------------------------------------------------------------------

def build_r12_polyline_dxf(
    points: Iterable[Point],
    layer: str = "NECK_TAPER",
    closed: bool = True,
) -> str:
    """
    Build a minimal DXF R12 file containing a single 2D POLYLINE.

    We deliberately use the old POLYLINE / VERTEX / SEQEND pattern so it is
    R12 compatible and robust with existing toolchains.

    Args:
        points: Sequence of (x, y) coordinates
        layer: DXF layer name
        closed: If True, flags the polyline as closed (70 = 1)

    Returns:
        Complete DXF file content as string

    Note:
        Units are whatever the neck taper math uses (mm or inches).
        The DXF consumer must know how to interpret units.
    """
    pts: List[Point] = list(points)
    if not pts:
        raise ValueError("Cannot build DXF: no points in outline")

    # DXF header + tables (minimal)
    header = [
        "0", "SECTION",
        "2", "HEADER",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "TABLES",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "BLOCKS",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "ENTITIES",
    ]

    # POLYLINE entity header
    # 66 = 1 means "entities follow"
    # 70 = 1 (closed polyline) or 0 (open)
    polyline_flags = 1 if closed else 0
    entities: List[str] = [
        "0", "POLYLINE",
        "8", layer,
        "66", "1",
        "70", str(polyline_flags),
    ]

    # VERTEX records
    for x, y in pts:
        entities.extend([
            "0", "VERTEX",
            "8", layer,
            "10", f"{x}",
            "20", f"{y}",
            "30", "0.0",
        ])

    # SEQEND to terminate the polyline
    entities.extend([
        "0", "SEQEND",
        "8", layer,
    ])

    # Close ENTITIES and file
    footer = [
        "0", "ENDSEC",
        "0", "EOF",
    ]

    lines = header + entities + footer
    # DXF is line-based with \n-separated code/value pairs
    return "\n".join(lines)


def write_r12_polyline_dxf_file(
    points: Iterable[Point],
    out_path: Path,
    layer: str = "NECK_TAPER",
    closed: bool = True,
) -> Path:
    """
    Convenience wrapper: build an R12 DXF string and write it to disk.

    Args:
        points: Sequence of (x, y) coordinates
        out_path: Output file path
        layer: DXF layer name
        closed: If True, creates closed polyline

    Returns:
        The output path for chaining
    """
    dxf_text = build_r12_polyline_dxf(points, layer=layer, closed=closed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dxf_text, encoding="utf-8", newline="\n")
    return out_path


# ---------------------------------------------------------------------------
# High-level helper: from TaperInputs to DXF file
# ---------------------------------------------------------------------------

def export_neck_outline_to_dxf(
    inputs: TaperInputs,
    frets: Iterable[int],
    out_path: Path,
    layer: str = "NECK_TAPER",
) -> Path:
    """
    Full pipeline: taper math → outline → DXF file.

    Args:
        inputs: Taper input parameters
        frets: Fret numbers to include in outline
        out_path: Output DXF file path
        layer: DXF layer name

    Returns:
        The output path

    Example:
        >>> inputs = TaperInputs(scale_length=647.7, nut_width=42.0,
        ...                      end_fret=12, end_width=57.0)
        >>> path = export_neck_outline_to_dxf(
        ...     inputs,
        ...     frets=range(0, 13),
        ...     out_path=Path("exports/neck_taper_strat_25_5.dxf"),
        ... )
    """
    outline_points = generate_neck_outline(inputs, list(frets))
    return write_r12_polyline_dxf_file(
        points=outline_points,
        out_path=out_path,
        layer=layer,
        closed=True,
    )
