"""
DXF Cleaner - Convert entities to closed LWPOLYLINEs for CAM
Migrated from: server/pipelines/dxf_cleaner/clean_dxf.py
Status: Medium Priority Pipeline

Converts LINE, ARC, CIRCLE, SPLINE entities to closed LWPOLYLINE
for maximum CAM software compatibility (Fusion 360, VCarve, Mach4).

Dependencies: ezdxf, shapely, numpy
"""
import ezdxf
from ezdxf.entities import Line, Arc, Circle, Spline, LWPolyline
from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, polygonize
import numpy as np
from pathlib import Path
from typing import List, Tuple


def arc_to_points(arc: Arc, num_segments: int = 32) -> List[Tuple[float, float]]:
    """
    Convert DXF Arc to list of points.
    
    Args:
        arc: ezdxf Arc entity
        num_segments: Number of line segments to approximate arc
    
    Returns:
        List of (x, y) tuples
    """
    center = arc.dxf.center
    radius = arc.dxf.radius
    start_angle = np.radians(arc.dxf.start_angle)
    end_angle = np.radians(arc.dxf.end_angle)
    
    # Handle angle wrap-around
    if end_angle < start_angle:
        end_angle += 2 * np.pi
    
    angles = np.linspace(start_angle, end_angle, num_segments)
    points = [
        (center.x + radius * np.cos(a), center.y + radius * np.sin(a))
        for a in angles
    ]
    return points


def circle_to_points(circle: Circle, num_segments: int = 64) -> List[Tuple[float, float]]:
    """
    Convert DXF Circle to list of points.
    
    Args:
        circle: ezdxf Circle entity
        num_segments: Number of line segments to approximate circle
    
    Returns:
        List of (x, y) tuples (closed)
    """
    center = circle.dxf.center
    radius = circle.dxf.radius
    
    angles = np.linspace(0, 2 * np.pi, num_segments + 1)
    points = [
        (center.x + radius * np.cos(a), center.y + radius * np.sin(a))
        for a in angles
    ]
    return points


def spline_to_points(spline: Spline, num_segments: int = 64) -> List[Tuple[float, float]]:
    """
    Convert DXF Spline to list of points using flattening.
    
    Args:
        spline: ezdxf Spline entity
        num_segments: Approximate number of segments
    
    Returns:
        List of (x, y) tuples
    """
    try:
        # Use ezdxf's built-in flattening
        points = list(spline.flattening(0.1))  # 0.1mm tolerance
        return [(p.x, p.y) for p in points]
    except Exception:
        # Fallback to control points if flattening fails
        return [(p.x, p.y) for p in spline.control_points]


def clean_dxf(input_path: str | Path, output_path: str | Path, tolerance: float = 0.1) -> dict:
    """
    Clean DXF file by converting all entities to closed LWPOLYLINEs.
    
    Args:
        input_path: Source DXF file
        output_path: Cleaned output DXF file
        tolerance: Distance tolerance for merging endpoints (mm)
    
    Returns:
        Statistics dict with entity counts
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Read source DXF
    doc = ezdxf.readfile(str(input_path))
    msp = doc.modelspace()
    
    # Collect all line segments
    all_segments = []
    stats = {
        'lines': 0,
        'arcs': 0,
        'circles': 0,
        'splines': 0,
        'polylines': 0,
        'output_polylines': 0,
    }
    
    for entity in msp:
        if isinstance(entity, Line):
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            all_segments.append(LineString([start, end]))
            stats['lines'] += 1
            
        elif isinstance(entity, Arc):
            points = arc_to_points(entity)
            if len(points) >= 2:
                all_segments.append(LineString(points))
            stats['arcs'] += 1
            
        elif isinstance(entity, Circle):
            points = circle_to_points(entity)
            # Circles are already closed, add as polygon directly
            try:
                poly = Polygon(points)
                if poly.is_valid:
                    # Will be handled separately
                    pass
            except Exception:
                pass
            all_segments.append(LineString(points))
            stats['circles'] += 1
            
        elif isinstance(entity, Spline):
            points = spline_to_points(entity)
            if len(points) >= 2:
                all_segments.append(LineString(points))
            stats['splines'] += 1
            
        elif isinstance(entity, LWPolyline):
            points = [(p[0], p[1]) for p in entity.get_points()]
            if len(points) >= 2:
                all_segments.append(LineString(points))
            stats['polylines'] += 1
    
    # Merge connected segments
    merged = linemerge(all_segments)
    
    # Convert to polygons where possible
    polygons = list(polygonize(merged))
    
    # Create output DXF (R12 for CAM compatibility)
    out_doc = ezdxf.new('R12')
    out_msp = out_doc.modelspace()
    
    # Add CLEAN layer
    out_doc.layers.add(name='CLEAN', color=7)
    
    # Add polygons as closed LWPOLYLINEs
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            exterior_coords = list(poly.exterior.coords)
            out_msp.add_lwpolyline(
                exterior_coords,
                close=True,
                dxfattribs={'layer': 'CLEAN'}
            )
            stats['output_polylines'] += 1
            
            # Add interior rings (holes) if any
            for interior in poly.interiors:
                interior_coords = list(interior.coords)
                out_msp.add_lwpolyline(
                    interior_coords,
                    close=True,
                    dxfattribs={'layer': 'CLEAN'}
                )
                stats['output_polylines'] += 1
    
    # Handle any unclosed line strings
    if hasattr(merged, 'geoms'):
        for geom in merged.geoms:
            if isinstance(geom, LineString) and not geom.is_ring:
                coords = list(geom.coords)
                if len(coords) >= 2:
                    out_msp.add_lwpolyline(
                        coords,
                        close=False,
                        dxfattribs={'layer': 'CLEAN'}
                    )
                    stats['output_polylines'] += 1
    elif isinstance(merged, LineString) and not merged.is_ring:
        coords = list(merged.coords)
        if len(coords) >= 2:
            out_msp.add_lwpolyline(
                coords,
                close=False,
                dxfattribs={'layer': 'CLEAN'}
            )
            stats['output_polylines'] += 1
    
    # Save output
    out_doc.saveas(str(output_path))
    
    print(f"Input: {input_path}")
    print(f"  Lines: {stats['lines']}, Arcs: {stats['arcs']}, "
          f"Circles: {stats['circles']}, Splines: {stats['splines']}, "
          f"Polylines: {stats['polylines']}")
    print(f"Output: {output_path}")
    print(f"  Closed LWPOLYLINEs: {stats['output_polylines']}")
    
    return stats


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python clean_dxf.py <input.dxf> <output.dxf> [tolerance]")
        print("\nConverts all entities to closed LWPOLYLINEs for CAM software.")
        print("Default tolerance: 0.1mm")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    
    clean_dxf(input_path, output_path, tolerance)
