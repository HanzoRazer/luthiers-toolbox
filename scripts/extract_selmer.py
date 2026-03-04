#!/usr/bin/env python3
"""
Extract Selmer Maccaferri D-hole guitar
This is an archtop acoustic with a distinctive D-shaped soundhole
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

# Selmer Maccaferri specific feature sizes (mm)
SELMER_FEATURES = {
    'BODY_OUTLINE': {'max': (450, 520), 'min': (350, 420)},
    'D_HOLE': {'max': (180, 220), 'min': (80, 110)},  # D-shaped soundhole
    'SOUNDHOLE_RING': {'max': (60, 80), 'min': (60, 80)},  # Decorative ring
    'NECK_BLOCK': {'max': (80, 120), 'min': (60, 90)},
    'TAIL_BLOCK': {'max': (60, 100), 'min': (40, 70)},
    'BRACING': {'max': (200, 400), 'min': (10, 40)},  # Long thin braces
    'PICKGUARD': {'max': (100, 150), 'min': (50, 80)},  # Floating pickguard
}

def classify_selmer_feature(w_mm, h_mm):
    max_dim = max(w_mm, h_mm)
    min_dim = min(w_mm, h_mm)

    for name, ranges in SELMER_FEATURES.items():
        max_r = ranges['max']
        min_r = ranges['min']
        if max_r[0] <= max_dim <= max_r[1] and min_r[0] <= min_dim <= min_r[1]:
            return name

    if max_dim > 300:
        return 'LARGE_UNKNOWN'
    elif max_dim > 50:
        return 'MEDIUM_FEATURE'
    return 'SMALL_FEATURE'

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf"
    output_path = r"C:\Users\thepr\Downloads\selmer_maccaferri.dxf"

    print("=" * 60)
    print("Extracting Selmer Maccaferri D-hole")
    print("=" * 60)

    dpi = 400
    print(f"\nRasterizing at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    print(f"Image: {width}x{height}px = {width*mm_per_px:.0f}x{height*mm_per_px:.0f}mm")

    print("\nExtracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    print("Finding contours...")
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Classify all contours
    classified = {}
    for c in contours:
        area = cv2.contourArea(c)
        if area < 500:
            continue
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        cat = classify_selmer_feature(w_mm, h_mm)
        if cat not in classified:
            classified[cat] = []
        classified[cat].append({
            'contour': c, 'w_mm': w_mm, 'h_mm': h_mm, 'area': area
        })

    # Sort by area
    for cat in classified:
        classified[cat].sort(key=lambda x: -x['area'])

    print("\nClassified features:")
    for cat, items in classified.items():
        if items and cat != 'SMALL_FEATURE':
            print(f"  {cat}: {len(items)}")
            for item in items[:3]:
                print(f"    - {item['w_mm']:.0f}x{item['h_mm']:.0f}mm")

    # Create DXF
    print("\n" + "=" * 60)
    print("Creating DXF...")
    print("=" * 60)

    doc = create_document(version='R12')
    msp = doc.modelspace()

    # Find body center
    body_cx, body_cy = 0, 0
    if 'BODY_OUTLINE' in classified and classified['BODY_OUTLINE']:
        body = classified['BODY_OUTLINE'][0]
        pts = body['contour'].reshape(-1, 2)
        xs = [p[0] * mm_per_px for p in pts]
        ys = [(height - p[1]) * mm_per_px for p in pts]
        body_cx = (min(xs) + max(xs)) / 2
        body_cy = (min(ys) + max(ys)) / 2

    def export_contour(item, layer_name, epsilon=0.1):
        pts = item['contour'].reshape(-1, 2)
        mm_pts = [(px * mm_per_px - body_cx, (height - py) * mm_per_px - body_cy)
                  for px, py in pts]

        pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(pts_array, epsilon, closed=True)
        simplified = simplified.reshape(-1, 2).tolist()

        point_tuples = [(float(x), float(y)) for x, y in simplified]
        add_polyline(msp, point_tuples, layer=layer_name, closed=True, version='R12')
        return len(simplified)

    exported = 0

    # Export features
    layer_config = {
        'BODY_OUTLINE': 1,
        'D_HOLE': 1,
        'SOUNDHOLE_RING': 2,
        'NECK_BLOCK': 1,
        'TAIL_BLOCK': 1,
        'BRACING': 10,
        'PICKGUARD': 1,
        'MEDIUM_FEATURE': 5,
    }

    for layer, max_count in layer_config.items():
        if layer not in classified:
            continue
        items = classified[layer][:max_count]
        if not items:
            continue

        print(f"\nExporting {layer}...")
        for i, item in enumerate(items):
            pts = export_contour(item, layer, 0.1)
            print(f"  {layer} {i+1}: {item['w_mm']:.0f}x{item['h_mm']:.0f}mm, {pts} pts")
            exported += 1

    doc.saveas(output_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Features exported: {exported}")

if __name__ == "__main__":
    main()
