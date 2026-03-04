#!/usr/bin/env python3
"""
Simple extraction - capture ALL features without complex classification
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
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf"
    output_path = r"C:\Users\thepr\Downloads\selmer_all_features.dxf"

    print("=" * 60)
    print("Simple Extraction - All Features")
    print("=" * 60)

    dpi = 400
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    print(f"Image: {width}x{height}px")

    # Extract with gap closing
    color_filter = ColorFilter(tolerance=30)
    mask = color_filter.extract_dark_lines(image, threshold=120, gap_close_size=5)

    # Find ALL contours
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    print(f"Found {len(contours)} total contours")

    # Filter by minimum size (25mm) and collect
    min_size_mm = 25
    features = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 200:
            continue
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        if max(w_mm, h_mm) >= min_size_mm:
            features.append({
                'contour': c,
                'w_mm': w_mm,
                'h_mm': h_mm,
                'area': area
            })

    features.sort(key=lambda x: -x['area'])
    print(f"Features >= {min_size_mm}mm: {len(features)}")

    # Find body center (largest feature)
    if not features:
        print("No features found!")
        return

    body = features[0]
    pts = body['contour'].reshape(-1, 2)
    xs = [p[0] * mm_per_px for p in pts]
    ys = [(height - p[1]) * mm_per_px for p in pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    # Create DXF
    doc = create_document(version='R12')
    msp = doc.modelspace()

    print("\nExporting features:")
    for i, feat in enumerate(features):
        c = feat['contour']
        pts = c.reshape(-1, 2)

        # Convert to mm, center
        mm_pts = [(px * mm_per_px - cx, (height - py) * mm_per_px - cy) for px, py in pts]

        # Simplify
        pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
        simplified = cv2.approxPolyDP(pts_array, 0.2, closed=True)
        simplified = simplified.reshape(-1, 2).tolist()

        # Assign to layer by size
        max_dim = max(feat['w_mm'], feat['h_mm'])
        if max_dim > 300:
            layer = 'BODY'
        elif max_dim > 100:
            layer = 'LARGE'
        elif max_dim > 50:
            layer = 'MEDIUM'
        else:
            layer = 'SMALL'

        point_tuples = [(float(x), float(y)) for x, y in simplified]
        add_polyline(msp, point_tuples, layer=layer, closed=True, version='R12')

        if i < 20:
            print(f"  {i+1}. {feat['w_mm']:.0f}x{feat['h_mm']:.0f}mm -> {layer} ({len(simplified)} pts)")

    doc.saveas(output_path)

    print(f"\n{'='*60}")
    print(f"SAVED: {output_path}")
    print(f"Total features: {len(features)}")
    print("Layers: BODY, LARGE, MEDIUM, SMALL")

if __name__ == "__main__":
    main()
