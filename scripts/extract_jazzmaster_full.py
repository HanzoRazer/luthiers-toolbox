#!/usr/bin/env python3
"""
Extract ALL Jazzmaster features with proper classification
Based on detailed scan:
- Body: 351x487mm
- Pickguard: 258x334mm, 240x307mm
- Pickups (93x51mm): 4 instances
- Neck pocket (70x79mm, 57x76mm): 3 instances
- Control (50x114mm): 1 instance
- Rhythm/Lead circuit (98x239mm): 1 instance
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body-Route-Pickguard.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_full.dxf"

    print("=" * 60)
    print("Extracting Complete Jazzmaster - All Features")
    print("=" * 60)

    dpi = 400
    print(f"\nRasterizing at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi

    print("Extracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    print("Finding contours...")
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Collect all features > 30mm
    all_features = []
    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        if max(w_mm, h_mm) > 40 and area > 1000:
            all_features.append({
                'contour': c,
                'w_mm': w_mm,
                'h_mm': h_mm,
                'area': area,
                'pts': len(c)
            })

    all_features.sort(key=lambda x: -x['area'])

    print(f"\nFound {len(all_features)} significant features")

    # Classify based on the scan results
    body = []
    pickguard = []
    pickup = []
    neck_pocket = []
    control = []
    rhythm_circuit = []
    other = []

    for f in all_features:
        w, h = f['w_mm'], f['h_mm']
        max_d, min_d = max(w, h), min(w, h)

        # Body outline: ~350x490mm
        if 300 < max_d < 550 and 300 < min_d < 450:
            body.append(f)
        # Pickguard: 240-260mm x 300-340mm
        elif 230 < max_d < 360 and 200 < min_d < 280:
            pickguard.append(f)
        # Pickup routes: ~93x51mm or ~95x61mm
        elif 85 < max_d < 100 and 45 < min_d < 70:
            pickup.append(f)
        # Neck pocket: ~70x79mm or ~57x76mm
        elif 50 < max_d < 85 and 50 < min_d < 85:
            neck_pocket.append(f)
        # Control cavity: ~50x114mm
        elif 100 < max_d < 130 and 40 < min_d < 60:
            control.append(f)
        # Rhythm/Lead circuit: ~98x239mm
        elif 200 < max_d < 260 and 80 < min_d < 110:
            rhythm_circuit.append(f)
        else:
            other.append(f)

    print("\nClassification:")
    print(f"  Body outlines: {len(body)}")
    print(f"  Pickguards: {len(pickguard)}")
    print(f"  Pickup routes: {len(pickup)}")
    print(f"  Neck pockets: {len(neck_pocket)}")
    print(f"  Control cavities: {len(control)}")
    print(f"  Rhythm circuits: {len(rhythm_circuit)}")
    print(f"  Other: {len(other)}")

    # Create DXF
    print("\n" + "=" * 60)
    print("Creating DXF...")
    print("=" * 60)

    doc = create_document(version='R12')
    msp = doc.modelspace()

    # Find body center for alignment
    body_cx, body_cy = 0, 0
    if body:
        largest_body = max(body, key=lambda x: x['area'])
        pts = largest_body['contour'].reshape(-1, 2)
        xs = [p[0] * mm_per_px for p in pts]
        ys = [(height - p[1]) * mm_per_px for p in pts]
        body_cx = (min(xs) + max(xs)) / 2
        body_cy = (min(ys) + max(ys)) / 2

    def export_feature(feature, layer_name, epsilon=0.1):
        pts = feature['contour'].reshape(-1, 2)
        mm_pts = []
        for px, py in pts:
            x_mm = px * mm_per_px - body_cx
            y_mm = (height - py) * mm_per_px - body_cy
            mm_pts.append((x_mm, y_mm))

        pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(pts_array, epsilon, closed=True)
        simplified = simplified.reshape(-1, 2).tolist()

        point_tuples = [(float(x), float(y)) for x, y in simplified]
        add_polyline(msp, point_tuples, layer=layer_name, closed=True, version='R12')
        return len(simplified)

    exported = 0

    # Export body (largest only)
    if body:
        print("\nExporting body outline...")
        largest = max(body, key=lambda x: x['area'])
        pts = export_feature(largest, 'BODY_OUTLINE', 0.1)
        print(f"  Body: {largest['w_mm']:.0f}x{largest['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Export pickguard (largest only)
    if pickguard:
        print("\nExporting pickguard...")
        largest = max(pickguard, key=lambda x: x['area'])
        pts = export_feature(largest, 'PICKGUARD', 0.1)
        print(f"  Pickguard: {largest['w_mm']:.0f}x{largest['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Export pickups (up to 4)
    if pickup:
        print("\nExporting pickup routes...")
        # Sort by position (x coordinate) to get consistent ordering
        pickup.sort(key=lambda x: cv2.boundingRect(x['contour'])[0])
        for i, f in enumerate(pickup[:4]):
            pts = export_feature(f, 'PICKUP_ROUTE', 0.05)
            print(f"  Pickup {i+1}: {f['w_mm']:.0f}x{f['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export neck pockets (up to 2)
    if neck_pocket:
        print("\nExporting neck pocket(s)...")
        for i, f in enumerate(neck_pocket[:2]):
            pts = export_feature(f, 'NECK_POCKET', 0.05)
            print(f"  Neck {i+1}: {f['w_mm']:.0f}x{f['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    # Export control cavity
    if control:
        print("\nExporting control cavity...")
        largest = max(control, key=lambda x: x['area'])
        pts = export_feature(largest, 'CONTROL_CAVITY', 0.05)
        print(f"  Control: {largest['w_mm']:.0f}x{largest['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Export rhythm circuit
    if rhythm_circuit:
        print("\nExporting rhythm/lead circuit...")
        largest = max(rhythm_circuit, key=lambda x: x['area'])
        pts = export_feature(largest, 'RHYTHM_CIRCUIT', 0.05)
        print(f"  Circuit: {largest['w_mm']:.0f}x{largest['h_mm']:.0f}mm, {pts} pts")
        exported += 1

    # Save
    doc.saveas(output_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Total features: {exported}")
    print("\nLayers created:")
    print("  - BODY_OUTLINE")
    print("  - PICKGUARD")
    print("  - PICKUP_ROUTE")
    print("  - NECK_POCKET")
    print("  - CONTROL_CAVITY")
    print("  - RHYTHM_CIRCUIT")

if __name__ == "__main__":
    main()
