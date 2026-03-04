#!/usr/bin/env python3
"""Scan Selmer Maccaferri PDFs"""
import sys
from pathlib import Path
import numpy as np
import cv2
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
from vectorizer_phase2 import rasterize_pdf, ColorFilter

def scan_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    print(f"\n{'='*60}")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Pages: {len(doc)}")
    print("="*60)

    dpi = 200
    mm_per_px = 25.4 / dpi

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        height, width = img.shape[:2]
        print(f"\nPage {page_num + 1}: {width*mm_per_px:.0f}x{height*mm_per_px:.0f}mm")

        color_filter = ColorFilter(tolerance=30)
        dark_mask = color_filter.extract_dark_lines(img, threshold=100)
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Collect significant features
        features = []
        for c in contours:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            w_mm = w * mm_per_px
            h_mm = h * mm_per_px
            if max(w_mm, h_mm) > 30 and area > 500:
                features.append((w_mm, h_mm, area))

        features.sort(key=lambda x: -x[2])
        print(f"  Significant features: {len(features)}")
        for w, h, area in features[:10]:
            print(f"    {w:.0f}x{h:.0f}mm")

    doc.close()

# Scan both PDFs
scan_pdf(r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf")
scan_pdf(r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-02.pdf")
