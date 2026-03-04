#!/usr/bin/env python3
"""
Extract complete Jazzmaster body from the routing PDF
which contains all cavities: neck pocket, pickups, control, etc.
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

def classify_feature(w_mm, h_mm, area):
    """Classify a contour based on dimensions."""
    max_dim = max(w_mm, h_mm)
    min_dim = min(w_mm, h_mm)

    # Body outline: ~500mm x ~350mm
    if 450 < max_dim < 600 and 300 < min_dim < 400:
        return 'BODY_OUTLINE'

    # Pickguard: similar to body but usually slightly smaller
    if 300 < max_dim < 500 and 200 < min_dim < 400:
        return 'PICKGUARD'

    # Neck pocket: ~55-60mm wide, ~90-100mm long
    if 50 < max_dim < 120 and 40 < min_dim < 90:
        aspect = max_dim / min_dim if min_dim > 0 else 0
        if 1.2 < aspect < 2.5:  # Rectangular
            return 'NECK_POCKET'

    # Pickup routes: ~90mm x ~50mm for Jazzmaster
    if 80 < max_dim < 110 and 40 < min_dim < 65:
        return 'PICKUP_ROUTE'

    # Control cavity: ~100mm long
    if 80 < max_dim < 130 and 40 < min_dim < 80:
        return 'CONTROL_CAVITY'

    # Bridge route: ~60-70mm
    if 55 < max_dim < 85 and 30 < min_dim < 60:
        return 'BRIDGE_ROUTE'

    # Jack route: ~50mm
    if 40 < max_dim < 60 and 25 < min_dim < 45:
        return 'JACK_ROUTE'

    # Small features
    if max_dim < 30:
        return 'SMALL'

    return 'UNKNOWN'


def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body-Route-Pickguard.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_routed.dxf"

    print("=" * 60)
    print("Extracting Jazzmaster Body with All Routes")
    print("=" * 60)
    print(f"PDF: {Path(pdf_path).name}")

    dpi = 400
    print(f"\nRasterizing at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    print(f"Image: {width}x{height}px = {width*mm_per_px:.0f}x{height*mm_per_px:.0f}mm")

    # Extract dark lines
    print("\nExtracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    # Find all contours
    print("Finding contours...")
    contours, hierarchy = cv2.findContours(
        dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )
    print(f"Found {len(contours)} contours")

    # Classify and collect
    features = {
        'BODY_OUTLINE': [],
        'PICKGUARD': [],
        'NECK_POCKET': [],
        'PICKUP_ROUTE': [],
        'CONTROL_CAVITY': [],
        'BRIDGE_ROUTE': [],
        'JACK_ROUTE': [],
        'UNKNOWN': [],
        'SMALL': []
    }

    print("\nClassifying features...")
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if area < 500:  # Skip tiny contours
            continue

        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        category = classify_feature(w_mm, h_mm, area)
        features[category].append({
            'contour': c,
            'w_mm': w_mm,
            'h_mm': h_mm,
            'area': area,
            'points': len(c)
        })

    # Print summary
    print("\nFeature summary:")
    for cat, items in features.items():
        if items and cat not in ['SMALL', 'UNKNOWN']:
            print(f"  {cat}: {len(items)}")
            for item in items[:3]:
                print(f"    - {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {item['points']} pts")

    # Prepare DXF
    print("\n" + "=" * 60)
    print("Creating DXF...")
    print("=" * 60)

    doc = create_document(version='R12')
    msp = doc.modelspace()

    # Find body outline center for alignment
    body_cx, body_cy = 0, 0
    if features['BODY_OUTLINE']:
        body = max(features['BODY_OUTLINE'], key=lambda x: x['area'])
        pts = body['contour'].reshape(-1, 2)
        xs = [p[0] * mm_per_px for p in pts]
        ys = [(height - p[1]) * mm_per_px for p in pts]
        body_cx = (min(xs) + max(xs)) / 2
        body_cy = (min(ys) + max(ys)) / 2

    def export_contour(item, layer_name, epsilon=0.1):
        """Export a contour to DXF."""
        pts = item['contour'].reshape(-1, 2)

        # Convert to mm, flip Y
        mm_pts = []
        for px, py in pts:
            x_mm = px * mm_per_px - body_cx
            y_mm = (height - py) * mm_per_px - body_cy
            mm_pts.append((x_mm, y_mm))

        # Simplify
        pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(pts_array, epsilon, closed=True)
        simplified = simplified.reshape(-1, 2).tolist()

        # Add to DXF
        point_tuples = [(float(x), float(y)) for x, y in simplified]
        add_polyline(msp, point_tuples, layer=layer_name, closed=True, version='R12')

        return len(simplified)

    exported = 0

    # Export body outline (largest one)
    if features['BODY_OUTLINE']:
        print("\nExporting body outline...")
        body = max(features['BODY_OUTLINE'], key=lambda x: x['area'])
        pts = export_contour(body, 'BODY_OUTLINE', 0.1)
        print(f"  Body: {body['w_mm']:.0f}x{body['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Export neck pockets
    if features['NECK_POCKET']:
        print("\nExporting neck pocket(s)...")
        for i, item in enumerate(features['NECK_POCKET'][:2]):  # Max 2
            pts = export_contour(item, 'NECK_POCKET', 0.05)
            print(f"  Neck {i+1}: {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export pickup routes
    if features['PICKUP_ROUTE']:
        print("\nExporting pickup routes...")
        for i, item in enumerate(features['PICKUP_ROUTE'][:4]):  # Max 4
            pts = export_contour(item, 'PICKUP_ROUTE', 0.05)
            print(f"  Pickup {i+1}: {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export control cavity
    if features['CONTROL_CAVITY']:
        print("\nExporting control cavities...")
        for i, item in enumerate(features['CONTROL_CAVITY'][:3]):  # Max 3
            pts = export_contour(item, 'CONTROL_CAVITY', 0.05)
            print(f"  Control {i+1}: {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export bridge routes
    if features['BRIDGE_ROUTE']:
        print("\nExporting bridge routes...")
        for i, item in enumerate(features['BRIDGE_ROUTE'][:2]):
            pts = export_contour(item, 'BRIDGE_ROUTE', 0.05)
            print(f"  Bridge {i+1}: {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export pickguard (if found)
    if features['PICKGUARD']:
        print("\nExporting pickguard...")
        pg = max(features['PICKGUARD'], key=lambda x: x['area'])
        pts = export_contour(pg, 'PICKGUARD', 0.1)
        print(f"  Pickguard: {pg['w_mm']:.0f}x{pg['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Save
    doc.saveas(output_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Features exported: {exported}")

if __name__ == "__main__":
    main()
