#!/usr/bin/env python3
"""
Extract vector paths directly from PDF technical drawings.

Technical drawings are often vector-based, meaning we can extract
the actual path data without relying on AI vision.
"""

import fitz  # PyMuPDF
import json
from pathlib import Path

def extract_paths_from_pdf(pdf_path: str, page_num: int = 0):
    """
    Extract all vector paths from a PDF page.

    Returns list of paths, each with points and properties.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Get page dimensions
    rect = page.rect
    page_width = rect.width
    page_height = rect.height

    print(f"Page size: {page_width:.1f} x {page_height:.1f} points")
    print(f"Page size: {page_width/72*25.4:.1f} x {page_height/72*25.4:.1f} mm")

    # Extract drawings (vector content)
    drawings = page.get_drawings()

    print(f"\nFound {len(drawings)} drawing elements")

    paths = []
    for i, drawing in enumerate(drawings):
        items = drawing.get("items", [])
        path_points = []

        for item in items:
            cmd = item[0]  # Command type: 'l' (line), 'c' (curve), 'm' (move), etc.

            if cmd == 'm':  # moveto
                path_points.append(('M', item[1].x, item[1].y))
            elif cmd == 'l':  # lineto
                path_points.append(('L', item[1].x, item[1].y))
            elif cmd == 'c':  # curveto (bezier)
                # item[1], item[2], item[3] are control points
                path_points.append(('C', item[1].x, item[1].y,
                                   item[2].x, item[2].y,
                                   item[3].x, item[3].y))
            elif cmd == 're':  # rectangle
                r = item[1]  # Rect object
                path_points.append(('R', r.x0, r.y0, r.x1, r.y1))

        if path_points:
            # Calculate bounding box
            xs = []
            ys = []
            for pt in path_points:
                if pt[0] in ('M', 'L'):
                    xs.append(pt[1])
                    ys.append(pt[2])
                elif pt[0] == 'C':
                    xs.extend([pt[1], pt[3], pt[5]])
                    ys.extend([pt[2], pt[4], pt[6]])
                elif pt[0] == 'R':
                    xs.extend([pt[1], pt[3]])
                    ys.extend([pt[2], pt[4]])

            if xs and ys:
                bbox_width = max(xs) - min(xs)
                bbox_height = max(ys) - min(ys)

                paths.append({
                    'index': i,
                    'points': path_points,
                    'point_count': len(path_points),
                    'bbox_width': bbox_width,
                    'bbox_height': bbox_height,
                    'bbox_area': bbox_width * bbox_height,
                    'color': drawing.get('color'),
                    'fill': drawing.get('fill'),
                    'stroke_width': drawing.get('width', 0),
                })

    doc.close()
    return paths, page_width, page_height


def find_body_outline(paths: list, min_area: float = 10000):
    """
    Find the largest closed path that's likely the body outline.

    Heuristics:
    - Large bounding box area
    - Many points (smooth curves)
    - No fill (outline only)
    """
    # Filter to large paths
    large_paths = [p for p in paths if p['bbox_area'] > min_area]

    print(f"\nPaths with area > {min_area}: {len(large_paths)}")

    # Sort by area (largest first)
    large_paths.sort(key=lambda p: p['bbox_area'], reverse=True)

    # Show top candidates
    print("\nTop 10 largest paths by AREA:")
    for p in large_paths[:10]:
        print(f"  #{p['index']}: {p['point_count']} pts, "
              f"area={p['bbox_area']:.0f}, "
              f"size={p['bbox_width']:.1f}x{p['bbox_height']:.1f}")

    # Also find paths with MANY points (likely actual curves)
    curved_paths = [p for p in paths if p['point_count'] >= 15]
    curved_paths.sort(key=lambda p: p['point_count'], reverse=True)

    print(f"\nPaths with 15+ points (curves): {len(curved_paths)}")
    print("\nTop 10 paths by POINT COUNT:")
    for p in curved_paths[:10]:
        print(f"  #{p['index']}: {p['point_count']} pts, "
              f"area={p['bbox_area']:.0f}, "
              f"size={p['bbox_width']:.1f}x{p['bbox_height']:.1f}")

    # Best candidate: large area AND many points
    good_candidates = [p for p in paths if p['bbox_area'] > 50000 and p['point_count'] >= 10]
    good_candidates.sort(key=lambda p: p['bbox_area'], reverse=True)

    print(f"\nGood candidates (area>50000 AND pts>=10): {len(good_candidates)}")
    for p in good_candidates[:5]:
        print(f"  #{p['index']}: {p['point_count']} pts, "
              f"area={p['bbox_area']:.0f}, "
              f"size={p['bbox_width']:.1f}x{p['bbox_height']:.1f}")

    return good_candidates if good_candidates else large_paths


def path_to_polygon(path_data: dict) -> list:
    """Convert path commands to simple polygon points."""
    points = []
    for cmd in path_data['points']:
        if cmd[0] == 'M':
            points.append((cmd[1], cmd[2]))
        elif cmd[0] == 'L':
            points.append((cmd[1], cmd[2]))
        elif cmd[0] == 'C':
            # For curves, sample the endpoint (simplified)
            points.append((cmd[5], cmd[6]))
    return points


def export_path_to_dxf(path_data: dict, output_path: str, page_height: float):
    """Export a path to DXF using ezdxf."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

    try:
        from util.dxf_compat import create_document, add_polyline
    except ImportError:
        import ezdxf
        def create_document(version='R12', setup=False):
            return ezdxf.new(version)
        def add_polyline(msp, points, layer='0', closed=False, version='R12'):
            n = len(points)
            end = n if closed else n - 1
            for i in range(end):
                msp.add_line(points[i], points[(i + 1) % n], dxfattribs={'layer': layer})

    # Convert path to polygon points
    polygon = path_to_polygon(path_data)

    # Convert from PDF points to mm, flip Y axis
    mm_points = []
    for x, y in polygon:
        x_mm = x / 72 * 25.4
        y_mm = (page_height - y) / 72 * 25.4  # Flip Y
        mm_points.append((x_mm, y_mm))

    # Center on origin
    xs = [p[0] for p in mm_points]
    ys = [p[1] for p in mm_points]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    centered = [(x - cx, y - cy) for x, y in mm_points]

    # Create DXF
    doc = create_document(version='R12')
    msp = doc.modelspace()
    add_polyline(msp, centered, layer='BODY_OUTLINE', closed=True, version='R12')
    doc.saveas(output_path)

    return centered


def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_body.dxf"

    print(f"Extracting vectors from: {pdf_path}\n")

    paths, page_w, page_h = extract_paths_from_pdf(pdf_path)

    # Find body outline candidates
    candidates = find_body_outline(paths)

    # Try path #0 which has 71 points
    path_0 = next((p for p in paths if p['index'] == 0), None)

    if path_0:
        print("\n" + "="*50)
        print("EXPORTING PATH #0 (71 points - likely body outline):")
        print("="*50)

        print(f"Points: {path_0['point_count']}")
        print(f"Size: {path_0['bbox_width']/72*25.4:.1f} x {path_0['bbox_height']/72*25.4:.1f} mm")

        # Export to DXF
        points = export_path_to_dxf(path_0, output_path, page_h)
        print(f"\nExported to: {output_path}")
        print(f"Polygon has {len(points)} vertices")

        # Calculate final dimensions
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        print(f"Final size: {width:.1f} x {height:.1f} mm")


if __name__ == "__main__":
    main()
