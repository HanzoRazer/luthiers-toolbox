#!/usr/bin/env python3
"""
Live test: Multi-view detection on Carlos Jumbo blueprints.

This script:
1. Converts Carlos Jumbo PDF pages to images
2. Runs multi-view detection via GeometryCoachV2
3. Reports detected views and segmentation quality
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure we can import from the photo-vectorizer directory
sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

# Try to import PyMuPDF for PDF conversion
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("WARNING: PyMuPDF not available. Install with: pip install PyMuPDF")

from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


def pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 150) -> np.ndarray:
    """Convert a PDF page to a numpy array (BGR format for OpenCV)."""
    if not FITZ_AVAILABLE:
        raise ImportError("PyMuPDF required for PDF conversion")

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # Render at specified DPI
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    # Convert RGB to BGR for OpenCV
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:  # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()
    return img


def test_carlos_jumbo():
    """Test multi-view detection on Carlos Jumbo blueprints."""

    # Find the Carlos Jumbo PDFs
    repo_root = Path(__file__).parent.parent.parent
    jumbo_dir = repo_root / "Guitar Plans" / "Jumbo Carlos"

    if not jumbo_dir.exists():
        print(f"ERROR: Directory not found: {jumbo_dir}")
        return

    pdfs = sorted(jumbo_dir.glob("JUMBO-CARLOS-*.pdf"))
    if not pdfs:
        print(f"ERROR: No Carlos Jumbo PDFs found in {jumbo_dir}")
        return

    print(f"Found {len(pdfs)} Carlos Jumbo PDFs")
    print("=" * 60)

    # Create coach with default config
    config = CoachV2Config(
        enable_multi_view_detection=True,
        multi_view_min_area_ratio=0.05,
        multi_view_score_threshold=0.50,
    )
    coach = GeometryCoachV2(config)

    # Output directory for debug images
    output_dir = Path(__file__).parent / "live_test_output" / "carlos_jumbo"
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdfs:
        print(f"\n📄 {pdf_path.name}")
        print("-" * 40)

        try:
            # Convert PDF to image
            if not FITZ_AVAILABLE:
                print("  ⚠️  Skipping - PyMuPDF not installed")
                continue

            image = pdf_page_to_image(pdf_path, page_num=0, dpi=150)
            h, w = image.shape[:2]
            print(f"  Image size: {w} x {h} px")

            # Save the converted image for reference
            img_path = output_dir / f"{pdf_path.stem}.png"
            cv2.imwrite(str(img_path), image)
            print(f"  Saved: {img_path.name}")

            # Run multi-view detection
            is_multi, seg_result = coach.is_multi_view_blueprint(image)

            if seg_result is None:
                print("  ⚠️  Segmentation returned None")
                continue

            print(f"  Multi-view detected: {is_multi}")
            print(f"  Views found: {seg_result.view_count}")

            if seg_result.views:
                print("\n  View Details:")
                for i, view in enumerate(seg_result.views):
                    x, y, vw, vh = view.bbox
                    area_pct = (view.area_ratio or 0) * 100
                    vtype = view.view_type.value if view.view_type else "unknown"
                    print(f"    [{i}] {view.label or 'unlabeled'}: "
                          f"{vw}x{vh} at ({x},{y}), "
                          f"area={area_pct:.1f}%, type={vtype}")

                # Save annotated image showing detected views
                annotated = image.copy()
                colors = [
                    (0, 255, 0),    # Green
                    (255, 0, 0),    # Blue
                    (0, 0, 255),    # Red
                    (255, 255, 0),  # Cyan
                    (255, 0, 255),  # Magenta
                    (0, 255, 255),  # Yellow
                ]

                for i, view in enumerate(seg_result.views):
                    x, y, vw, vh = view.bbox
                    color = colors[i % len(colors)]
                    cv2.rectangle(annotated, (x, y), (x + vw, y + vh), color, 3)

                    label = f"{i}: {view.label or 'view'}"
                    cv2.putText(annotated, label, (x + 5, y + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                annotated_path = output_dir / f"{pdf_path.stem}_views.png"
                cv2.imwrite(str(annotated_path), annotated)
                print(f"\n  Saved annotated: {annotated_path.name}")

            if seg_result.warnings:
                print(f"\n  Warnings: {seg_result.warnings}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Output saved to: {output_dir}")


if __name__ == "__main__":
    test_carlos_jumbo()
