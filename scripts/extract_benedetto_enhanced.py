#!/usr/bin/env python3
"""
Enhanced Benedetto extraction - capture ALL detail including fine lines
Separates text from outlines based on contour characteristics
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import load_input, ColorFilter
from dxf_compat import create_document, add_polyline

def extract_all_detail(image_path: str, output_path: str, dpi: int = 300):
    """Extract all detail from blueprint, separating text from outlines"""

    print(f"\nLoading: {Path(image_path).name}")
    image = load_input(image_path)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    print(f"Image: {width}x{height}px ({width*mm_per_px:.0f}x{height*mm_per_px:.0f}mm)")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Analyze image
    cf = ColorFilter()
    analysis = cf.analyze_image(image)
    print(f"Type: {analysis['blueprint_type']}, Dark: {analysis['dark_ratio']*100:.1f}%")

    # Method 1: Adaptive threshold for fine lines
    print("\nExtracting with adaptive threshold...")
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 5
    )

    # Method 2: Also try Canny edge detection for thin lines
    print("Extracting edges with Canny...")
    edges = cv2.Canny(gray, 30, 100)

    # Dilate edges slightly to connect nearby segments
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Combine both methods
    combined = cv2.bitwise_or(adaptive, edges)

    # Light cleanup - don't close gaps too much to preserve detail
    kernel_small = np.ones((2, 2), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_small)

    # Find ALL contours (not just external)
    contours, hierarchy = cv2.findContours(
        combined, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
    )
    print(f"Found {len(contours)} raw contours")

    # Classify contours
    outlines = []  # Large curved shapes (body, bracing, f-holes)
    details = []   # Medium features
    text_boxes = [] # Small rectangular shapes (likely text)

    min_area = 50  # Very low threshold to capture fine lines

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        max_dim = max(w_mm, h_mm)
        min_dim = min(w_mm, h_mm)

        # Calculate shape metrics
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        aspect = max_dim / min_dim if min_dim > 0 else 999

        # Classify based on characteristics
        # Text tends to be: small, rectangular (high aspect), low circularity
        is_text_like = (
            max_dim < 15 and  # Small
            aspect > 2 and    # Elongated
            circularity < 0.3  # Not round
        )

        if is_text_like:
            text_boxes.append({
                'contour': c, 'w_mm': w_mm, 'h_mm': h_mm,
                'area': area, 'type': 'TEXT'
            })
        elif max_dim > 50:  # Significant features
            outlines.append({
                'contour': c, 'w_mm': w_mm, 'h_mm': h_mm,
                'area': area, 'type': 'OUTLINE'
            })
        else:  # Medium/small details
            details.append({
                'contour': c, 'w_mm': w_mm, 'h_mm': h_mm,
                'area': area, 'type': 'DETAIL'
            })

    print(f"\nClassified:")
    print(f"  OUTLINE (>50mm): {len(outlines)}")
    print(f"  DETAIL: {len(details)}")
    print(f"  TEXT: {len(text_boxes)}")

    # Sort by area
    outlines.sort(key=lambda x: -x['area'])
    details.sort(key=lambda x: -x['area'])

    # Find center from largest outline
    if outlines:
        body = outlines[0]
        pts = body['contour'].reshape(-1, 2)
        xs = [p[0] * mm_per_px for p in pts]
        ys = [(height - p[1]) * mm_per_px for p in pts]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
    else:
        cx = width * mm_per_px / 2
        cy = height * mm_per_px / 2

    # Create DXF with separate layers
    doc = create_document(version='R12')
    msp = doc.modelspace()

    def add_contours(items, layer_name, max_count=None):
        count = 0
        for item in items:
            if max_count and count >= max_count:
                break
            c = item['contour']
            pts = c.reshape(-1, 2)

            # Convert to mm, center
            mm_pts = [(px * mm_per_px - cx, (height - py) * mm_per_px - cy)
                      for px, py in pts]

            # Light simplification to preserve detail
            pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
            simplified = cv2.approxPolyDP(pts_array, 0.1, closed=True)  # Very low tolerance
            simplified = simplified.reshape(-1, 2).tolist()

            if len(simplified) >= 3:
                point_tuples = [(float(x), float(y)) for x, y in simplified]
                add_polyline(msp, point_tuples, layer=layer_name, closed=True, version='R12')
                count += 1
        return count

    # Add to DXF
    outline_count = add_contours(outlines, 'OUTLINE')
    detail_count = add_contours(details, 'DETAIL', max_count=200)
    text_count = add_contours(text_boxes, 'TEXT', max_count=100)

    doc.saveas(output_path)

    print(f"\nExported to DXF:")
    print(f"  OUTLINE layer: {outline_count} contours")
    print(f"  DETAIL layer: {detail_count} contours")
    print(f"  TEXT layer: {text_count} contours")
    print(f"\nSaved: {output_path}")

    return {
        'outlines': outline_count,
        'details': detail_count,
        'text': text_count,
        'total': outline_count + detail_count + text_count
    }


def main():
    base_dir = Path(__file__).parent.parent
    output_dir = Path(r"C:\Users\thepr\Downloads")

    for name in ["Benedetto Front.jpg", "Benedetto Back.jpg"]:
        img_path = base_dir / name
        if not img_path.exists():
            print(f"NOT FOUND: {img_path}")
            continue

        output_name = name.replace('.jpg', '_enhanced.dxf')
        output_path = output_dir / output_name

        print("\n" + "=" * 60)
        extract_all_detail(str(img_path), str(output_path), dpi=300)


if __name__ == "__main__":
    main()
