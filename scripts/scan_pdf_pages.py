#!/usr/bin/env python3
"""
Scan all pages of the PDF to find features
"""
import sys
from pathlib import Path
import numpy as np
import cv2
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
from vectorizer_phase2 import rasterize_pdf, ColorFilter

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"

    doc = fitz.open(pdf_path)
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Total pages: {len(doc)}")
    print("=" * 70)

    dpi = 200  # Lower DPI for quick scan
    mm_per_px = 25.4 / dpi

    for page_num in range(len(doc)):
        print(f"\nPage {page_num + 1}:")

        # Rasterize
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        height, width = img.shape[:2]

        # Extract dark lines
        color_filter = ColorFilter(tolerance=30)
        dark_mask = color_filter.extract_dark_lines(img, threshold=100)

        # Find contours
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Categorize by size
        body_sized = []  # 400-600mm
        medium = []      # 50-200mm (cavities)
        small = []       # 20-50mm (small features)

        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            w_mm = w * mm_per_px
            h_mm = h * mm_per_px
            max_dim = max(w_mm, h_mm)

            if 400 < max_dim < 700:
                body_sized.append((w_mm, h_mm))
            elif 50 < max_dim < 200:
                medium.append((w_mm, h_mm))
            elif 20 < max_dim < 50:
                small.append((w_mm, h_mm))

        print(f"  Body-sized (400-700mm): {len(body_sized)}")
        for w, h in body_sized[:3]:
            print(f"    - {w:.0f}x{h:.0f}mm")

        print(f"  Medium (50-200mm): {len(medium)}")
        for w, h in medium[:5]:
            print(f"    - {w:.0f}x{h:.0f}mm")

        print(f"  Small (20-50mm): {len(small)}")

    doc.close()

if __name__ == "__main__":
    main()
