#!/usr/bin/env python3
"""
Scan the route/pickguard PDF for features
"""
import sys
from pathlib import Path
import numpy as np
import cv2
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
from vectorizer_phase2 import rasterize_pdf, ColorFilter

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body-Route-Pickguard.pdf"

    doc = fitz.open(pdf_path)
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Total pages: {len(doc)}")
    print("=" * 70)

    dpi = 300
    mm_per_px = 25.4 / dpi

    for page_num in range(len(doc)):
        print(f"\nPage {page_num + 1}:")

        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        height, width = img.shape[:2]
        print(f"  Size: {width}x{height}px = {width*mm_per_px:.0f}x{height*mm_per_px:.0f}mm")

        color_filter = ColorFilter(tolerance=30)
        dark_mask = color_filter.extract_dark_lines(img, threshold=100)

        contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Collect all significant contours
        features = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            w_mm = w * mm_per_px
            h_mm = h * mm_per_px
            area = cv2.contourArea(c)

            if max(w_mm, h_mm) > 20 and area > 100:
                features.append({
                    'w': w_mm, 'h': h_mm, 'area': area, 'pts': len(c)
                })

        features.sort(key=lambda x: -x['area'])

        print(f"  Significant features ({len(features)}):")
        for f in features[:15]:
            print(f"    {f['w']:.0f}x{f['h']:.0f}mm, area={f['area']:.0f}")

    doc.close()

if __name__ == "__main__":
    main()
