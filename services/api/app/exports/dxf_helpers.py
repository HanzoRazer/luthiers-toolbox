"""
DXF Generation Helpers for Luthier's Tool Box
Provides utilities for generating DXF files in ASCII R12 format (fallback)
and native ezdxf format (preferred when available)

Migrated from legacy ./server/dxf_helpers.py
"""

import math
from typing import List, Tuple, Optional, Dict


def _layer_name(layers: Optional[Dict[str, str]], key: str, default: str) -> str:
    """Resolve layer name from mapping dictionary"""
    if not layers:
        return default
    return layers.get(key, default) or default


def _ascii_r12_header(comment: Optional[str] = None) -> str:
    """Generate DXF R12 header for ASCII format with optional comment"""
    header_parts = ["0", "SECTION", "2", "HEADER"]

    if comment:
        header_parts.extend(["999", comment])

    header_parts.extend([
        "9", "$ACADVER", "1", "AC1009",
        "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES",
        "0", "TABLE", "2", "LAYER", "70", "1",
        "0", "LAYER", "2", "0", "70", "0", "62", "7", "6", "CONTINUOUS",
        "0", "ENDTAB",
        "0", "ENDSEC",
        "0", "SECTION", "2", "BLOCKS",
        "0", "ENDSEC",
        "0", "SECTION", "2", "ENTITIES"
    ])

    return "\n".join(header_parts) + "\n"


def _ascii_r12_footer() -> str:
    """Generate DXF R12 footer for ASCII format"""
    return "0\nENDSEC\n0\nEOF\n"


def write_polyline_ascii(points: List[Tuple[float, float]], layer: str = "CURVE") -> str:
    """
    Generate ASCII DXF POLYLINE entity from points

    Args:
        points: List of (x, y) coordinates in mm
        layer: DXF layer name (default: "CURVE")

    Returns:
        ASCII DXF string for polyline entity
    """
    lines = ["0", "POLYLINE", "8", layer, "66", "1", "70", "0"]

    for (x, y) in points:
        lines.extend([
            "0", "VERTEX", "8", layer,
            "10", f"{x:.6f}",
            "20", f"{y:.6f}",
            "30", "0.0"
        ])

    lines.extend(["0", "SEQEND"])
    return "\n".join(lines) + "\n"


def write_arc_ascii(
    center: Tuple[float, float],
    radius: float,
    start_angle_deg: float,
    end_angle_deg: float,
    layer: str = "CURVE"
) -> str:
    """
    Generate ASCII DXF ARC entity

    Args:
        center: (x, y) center point in mm
        radius: Arc radius in mm
        start_angle_deg: Start angle in degrees
        end_angle_deg: End angle in degrees
        layer: DXF layer name

    Returns:
        ASCII DXF string for arc entity
    """
    start_norm = start_angle_deg % 360
    end_norm = end_angle_deg % 360

    lines = [
        "0", "ARC", "8", layer,
        "10", f"{center[0]:.6f}",
        "20", f"{center[1]:.6f}",
        "30", "0.0",
        "40", f"{radius:.6f}",
        "50", f"{start_norm:.6f}",
        "51", f"{end_norm:.6f}"
    ]

    return "\n".join(lines) + "\n"


def build_ascii_r12(entities: List[str], comment: Optional[str] = None) -> bytes:
    """
    Build complete DXF R12 file in ASCII format

    Args:
        entities: List of entity strings
        comment: Optional comment string for DXF header

    Returns:
        Complete DXF file as bytes
    """
    header = _ascii_r12_header(comment=comment)
    footer = _ascii_r12_footer()
    body = "".join(entities)

    complete = header + body + footer
    return complete.encode("ascii")


def try_build_with_ezdxf(entities: List[Tuple[str, dict]]) -> Optional[bytes]:
    """
    Attempt to build DXF using native ezdxf library (if available)

    Args:
        entities: List of (entity_type, params) tuples

    Returns:
        DXF file as bytes if ezdxf available, None otherwise
    """
    try:
        import ezdxf
        from io import BytesIO
    except ImportError:
        return None

    try:
        doc = ezdxf.new("R12")
        msp = doc.modelspace()

        comment = None
        if entities:
            comment = entities[0][1].get('comment')
            if comment:
                try:
                    doc.header.custom_vars.append(("COMMENT", comment))
                except (ValueError, AttributeError):  # WP-1: narrowed from except Exception
                    pass

        for (etype, params) in entities:
            layer = params.get('layer', '0')

            if layer not in doc.layers:
                doc.layers.add(layer)

            if etype == 'polyline':
                points = params['points']
                points_3d = [(x, y, 0) for (x, y) in points]
                msp.add_lwpolyline(points_3d, dxfattribs={'layer': layer})

            elif etype == 'arc':
                center = params['center']
                radius = params['radius']
                start_angle = params['start_angle']
                end_angle = params['end_angle']
                msp.add_arc(
                    center=(center[0], center[1], 0),
                    radius=radius,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    dxfattribs={'layer': layer}
                )

            elif etype == 'line':
                start = params['start']
                end = params['end']
                msp.add_line(
                    start=(start[0], start[1], 0),
                    end=(end[0], end[1], 0),
                    dxfattribs={'layer': layer}
                )

            elif etype == 'circle':
                center = params['center']
                radius = params['radius']
                msp.add_circle(
                    center=(center[0], center[1], 0),
                    radius=radius,
                    dxfattribs={'layer': layer}
                )

        bio = BytesIO()
        doc.write(bio, fmt='asc')
        return bio.getvalue()

    except (OSError, ValueError) as e:  # WP-1: narrowed from except Exception
        print(f"ezdxf export failed: {e}")
        return None


def angle_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate angle from p1 to p2 in degrees"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))


def distance_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)
