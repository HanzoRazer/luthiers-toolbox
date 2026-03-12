"""
Neck DXF export - exports neck geometry to DXF format.

Extracted from neck_router.py.
"""
import io

from fastapi import HTTPException

from .schemas import NeckParameters, NeckGeometryOut

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


def export_neck_dxf(params: NeckParameters, geometry: NeckGeometryOut) -> bytes:
    """
    Export neck geometry to DXF R12 format.

    Layers:
    - NECK_PROFILE: Side view profile
    - FRETBOARD: Top view fretboard outline
    - FRET_SLOTS: Fret slot positions
    - HEADSTOCK: Headstock outline
    - TUNER_HOLES: Tuner hole positions
    - CENTERLINE: Reference line
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(500, detail="ezdxf library not installed")

    # Create DXF document (R12 format for maximum compatibility)
    doc = ezdxf.new('R12', setup=True)
    msp = doc.modelspace()

    # Layer definitions with colors
    layers = {
        'NECK_PROFILE': 1,      # Red
        'FRETBOARD': 2,         # Yellow
        'FRET_SLOTS': 3,        # Green
        'HEADSTOCK': 4,         # Cyan
        'TUNER_HOLES': 5,       # Blue
        'CENTERLINE': 8         # Gray
    }

    for layer_name, color in layers.items():
        doc.layers.new(name=layer_name, dxfattribs={'color': color})

    # Add neck profile (side view)
    profile_pts = [(p.x, p.y) for p in geometry.profile_points]
    if len(profile_pts) >= 2:
        msp.add_polyline2d(
            profile_pts,
            dxfattribs={'layer': 'NECK_PROFILE'}
        )

    # Add fretboard outline (top view)
    if geometry.fretboard_points:
        fretboard_pts = [(p.x, p.y) for p in geometry.fretboard_points]
        if len(fretboard_pts) >= 2:
            msp.add_polyline2d(
                fretboard_pts,
                dxfattribs={'layer': 'FRETBOARD'}
            )

    # Add fret slots (lines across fretboard)
    if geometry.fretboard_points:
        fb_width = params.nut_width if params.units == "in" else params.nut_width * 25.4
        for fret_pos in geometry.fret_positions:
            msp.add_line(
                (fret_pos, -fb_width / 2),
                (fret_pos, fb_width / 2),
                dxfattribs={'layer': 'FRET_SLOTS'}
            )

    # Add headstock outline
    headstock_pts = [(p.x, p.y) for p in geometry.headstock_points]
    if len(headstock_pts) >= 2:
        msp.add_polyline2d(
            headstock_pts,
            dxfattribs={'layer': 'HEADSTOCK'}
        )

    # Add tuner holes (circles)
    tuner_radius = (params.tuner_diameter / 2) if params.units == "in" else (params.tuner_diameter * 25.4 / 2)
    for hole in geometry.tuner_holes:
        msp.add_circle(
            (hole.x, hole.y),
            radius=tuner_radius,
            dxfattribs={'layer': 'TUNER_HOLES'}
        )

    # Add centerline
    centerline_pts = [(p.x, p.y) for p in geometry.centerline]
    if len(centerline_pts) >= 2:
        msp.add_line(
            centerline_pts[0],
            centerline_pts[1],
            dxfattribs={'layer': 'CENTERLINE'}
        )

    # Add metadata text
    msp.add_text(
        f"Les Paul Neck - Scale: {geometry.scale_length:.3f}{geometry.units}",
        dxfattribs={
            'layer': 'CENTERLINE',
            'height': 0.25 if params.units == "in" else 6.0,
            'insert': (0, -3 if params.units == "in" else -75)
        }
    )

    # Write to bytes
    stream = io.StringIO()
    doc.write(stream, fmt='asc')  # ASCII format for R12
    stream.seek(0)
    dxf_content = stream.getvalue()
    return dxf_content.encode('utf-8')
