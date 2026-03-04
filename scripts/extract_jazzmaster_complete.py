#!/usr/bin/env python3
"""
Extract complete Jazzmaster body with cavities
- Body outline
- Neck pocket
- Pickup routes
- Control cavity
"""
import sys
from pathlib import Path
import numpy as np
import cv2

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

def classify_contour(contour, mm_per_px, img_width_mm, img_height_mm):
    """Classify a contour by size and position."""
    area = cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)

    w_mm = w * mm_per_px
    h_mm = h * mm_per_px
    x_mm = x * mm_per_px
    y_mm = y * mm_per_px

    # Body outline: 450-600mm long, 300-400mm wide (check first!)
    if 450 < max(w_mm, h_mm) < 650 and 300 < min(w_mm, h_mm) < 450:
        return 'body_outline', w_mm, h_mm

    # Page border: spans nearly full page
    if w_mm > img_width_mm * 0.95 or h_mm > img_height_mm * 0.95:
        return 'page_border', w_mm, h_mm

    # Neck pocket: ~55-60mm wide, ~75-100mm long
    if 40 < w_mm < 80 and 60 < h_mm < 120:
        return 'neck_pocket', w_mm, h_mm
    if 60 < w_mm < 120 and 40 < h_mm < 80:
        return 'neck_pocket', w_mm, h_mm

    # Pickup routes: ~70-90mm long, ~35-45mm wide (single coils)
    if 60 < max(w_mm, h_mm) < 100 and 25 < min(w_mm, h_mm) < 55:
        return 'pickup_route', w_mm, h_mm

    # Control cavity: ~80-150mm, irregular shape
    if 70 < max(w_mm, h_mm) < 180 and 50 < min(w_mm, h_mm) < 120:
        return 'control_cavity', w_mm, h_mm

    # Bridge/tremolo: ~80-120mm
    if 70 < max(w_mm, h_mm) < 140 and 30 < min(w_mm, h_mm) < 80:
        return 'bridge_route', w_mm, h_mm

    # Small features (screw holes, etc): < 20mm
    if max(w_mm, h_mm) < 25:
        return 'small_feature', w_mm, h_mm

    # Title block text / annotations: thin and long
    if w_mm > 50 and h_mm < 15:
        return 'text', w_mm, h_mm
    if h_mm > 50 and w_mm < 15:
        return 'text', w_mm, h_mm

    # Large partial outlines (may be other guitar bodies on the page)
    if max(w_mm, h_mm) > 300:
        return 'other_body', w_mm, h_mm

    return 'unknown', w_mm, h_mm


def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_complete.dxf"
    page_num = 2

    print("=" * 60)
    print("Extracting Complete Jazzmaster Body")
    print("=" * 60)

    dpi = 400
    print(f"\nRasterizing PDF at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    img_width_mm = width * mm_per_px
    img_height_mm = height * mm_per_px
    print(f"Image: {width} x {height} px = {img_width_mm:.0f} x {img_height_mm:.0f} mm")

    # Extract dark lines
    print("\nExtracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    # Find ALL contours with hierarchy
    print("Finding all contours (including internal)...")
    contours, hierarchy = cv2.findContours(
        dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )
    print(f"Found {len(contours)} total contours")

    # Classify contours
    classified = {
        'body_outline': [],
        'neck_pocket': [],
        'pickup_route': [],
        'control_cavity': [],
        'bridge_route': [],
        'small_feature': [],
        'text': [],
        'page_border': [],
        'other_body': [],
        'unknown': []
    }

    print("\nClassifying contours...")
    for i, contour in enumerate(contours):
        category, w_mm, h_mm = classify_contour(contour, mm_per_px, img_width_mm, img_height_mm)
        classified[category].append({
            'contour': contour,
            'w_mm': w_mm,
            'h_mm': h_mm,
            'points': len(contour)
        })

    # Print summary
    print("\nContour summary:")
    for cat, items in classified.items():
        if items:
            print(f"  {cat}: {len(items)}")
            for item in items[:3]:
                print(f"    - {item['w_mm']:.1f}x{item['h_mm']:.1f}mm, {item['points']} pts")

    # Prepare for export
    print("\n" + "=" * 60)
    print("Preparing DXF export...")
    print("=" * 60)

    doc = create_document(version='R12')
    msp = doc.modelspace()

    def export_contour(contour_data, layer_name, simplify_epsilon=0.1):
        """Convert and export a single contour."""
        contour = contour_data['contour']
        points = contour.reshape(-1, 2)

        # Convert to mm, flip Y, center
        mm_points = []
        for px, py in points:
            x_mm = px * mm_per_px
            y_mm = (height - py) * mm_per_px
            mm_points.append((x_mm, y_mm))

        # Simplify
        pts_array = np.array(mm_points, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(pts_array, simplify_epsilon, closed=True)
        simplified = simplified.reshape(-1, 2).tolist()

        return simplified

    # Get body outline center for alignment
    body_center_x = 0
    body_center_y = 0

    if classified['body_outline']:
        # Use largest body outline
        body = max(classified['body_outline'], key=lambda x: x['w_mm'] * x['h_mm'])
        body_pts = export_contour(body, 'BODY_OUTLINE', 0.1)
        xs = [p[0] for p in body_pts]
        ys = [p[1] for p in body_pts]
        body_center_x = (min(xs) + max(xs)) / 2
        body_center_y = (min(ys) + max(ys)) / 2

    def center_and_add(points, layer_name):
        """Center points and add to DXF."""
        centered = [(x - body_center_x, y - body_center_y) for x, y in points]
        point_tuples = [(float(x), float(y)) for x, y in centered]
        add_polyline(msp, point_tuples, layer=layer_name, closed=True, version='R12')
        return centered

    exported_count = 0

    # Export body outline
    if classified['body_outline']:
        print("\nExporting body outline...")
        body = max(classified['body_outline'], key=lambda x: x['w_mm'] * x['h_mm'])
        pts = export_contour(body, 'BODY_OUTLINE', 0.1)
        centered = center_and_add(pts, 'BODY_OUTLINE')
        xs = [p[0] for p in centered]
        ys = [p[1] for p in centered]
        print(f"  Body: {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f} mm, {len(pts)} pts")
        exported_count += 1

    # Export neck pocket
    if classified['neck_pocket']:
        print("\nExporting neck pocket(s)...")
        for i, item in enumerate(classified['neck_pocket']):
            pts = export_contour(item, 'NECK_POCKET', 0.1)
            center_and_add(pts, 'NECK_POCKET')
            print(f"  Neck pocket {i+1}: {item['w_mm']:.1f}x{item['h_mm']:.1f}mm")
            exported_count += 1

    # Export pickup routes
    if classified['pickup_route']:
        print("\nExporting pickup route(s)...")
        for i, item in enumerate(classified['pickup_route']):
            pts = export_contour(item, 'PICKUP_ROUTE', 0.1)
            center_and_add(pts, 'PICKUP_ROUTE')
            print(f"  Pickup {i+1}: {item['w_mm']:.1f}x{item['h_mm']:.1f}mm")
            exported_count += 1

    # Export control cavity
    if classified['control_cavity']:
        print("\nExporting control cavit(ies)...")
        for i, item in enumerate(classified['control_cavity']):
            pts = export_contour(item, 'CONTROL_CAVITY', 0.1)
            center_and_add(pts, 'CONTROL_CAVITY')
            print(f"  Control {i+1}: {item['w_mm']:.1f}x{item['h_mm']:.1f}mm")
            exported_count += 1

    # Export bridge routes
    if classified['bridge_route']:
        print("\nExporting bridge route(s)...")
        for i, item in enumerate(classified['bridge_route']):
            pts = export_contour(item, 'BRIDGE_ROUTE', 0.1)
            center_and_add(pts, 'BRIDGE_ROUTE')
            print(f"  Bridge {i+1}: {item['w_mm']:.1f}x{item['h_mm']:.1f}mm")
            exported_count += 1

    # Save
    doc.saveas(output_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Total features exported: {exported_count}")
    print("\nLayers:")
    print("  - BODY_OUTLINE")
    print("  - NECK_POCKET")
    print("  - PICKUP_ROUTE")
    print("  - CONTROL_CAVITY")
    print("  - BRIDGE_ROUTE")

if __name__ == "__main__":
    main()
