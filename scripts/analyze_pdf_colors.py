#!/usr/bin/env python3
"""
Analyze colors in a PDF page to identify the dominant colors.
"""
import sys
from pathlib import Path
import numpy as np
import cv2

# Add blueprint-import to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import rasterize_pdf

def analyze_colors(image: np.ndarray, min_area_ratio: float = 0.0001):
    """Find unique colors and their pixel counts."""
    height, width = image.shape[:2]
    total_pixels = height * width
    min_pixels = int(total_pixels * min_area_ratio)

    # Reshape to list of BGR tuples
    pixels = image.reshape(-1, 3)

    # Find unique colors
    unique, counts = np.unique(pixels, axis=0, return_counts=True)

    # Filter out near-white and sort by count
    results = []
    for color, count in zip(unique, counts):
        if count < min_pixels:
            continue
        # Skip near-white (all channels > 240)
        if all(c > 240 for c in color):
            continue
        results.append((color, count))

    results.sort(key=lambda x: -x[1])
    return results


def classify_color(bgr):
    """Classify a BGR color into human-readable name."""
    b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])

    # Check for near-black
    if max(b, g, r) < 30:
        return "black"

    # Check for grayscale
    if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20:
        avg = (r + g + b) / 3
        if avg < 80:
            return "dark_gray"
        elif avg < 180:
            return "gray"
        else:
            return "light_gray"

    # Color classification
    if r > max(g, b) + 30:
        if r > 150:
            return "RED" if g < 100 else "orange"
        return "dark_red"
    if b > max(r, g) + 30:
        return "BLUE"
    if g > max(r, b) + 30:
        return "GREEN"

    # Mixed colors
    if r > 150 and g > 100 and b < 100:
        return "yellow/orange"
    if r > 150 and b > 150 and g < 100:
        return "purple"
    if g > 150 and b > 150 and r < 100:
        return "cyan"

    return "other"


def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    page_num = 2  # Page 3 (0-indexed)

    print("=" * 60)
    print("PDF Color Analysis")
    print("=" * 60)
    print(f"\nPDF: {Path(pdf_path).name}")
    print(f"Page: {page_num + 1}")

    print("\nRasterizing PDF at 300 DPI...")
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=300)

    print(f"Image size: {image.shape[1]} x {image.shape[0]} pixels")

    print("\nAnalyzing colors...")
    colors = analyze_colors(image)

    print(f"\nFound {len(colors)} significant colors (min 0.01% of image):")
    print("-" * 60)
    print(f"{'BGR':<20} {'Pixels':>10} {'%':>8}  {'Classification':<15}")
    print("-" * 60)

    for bgr, count in colors[:20]:
        pct = 100 * count / (image.shape[0] * image.shape[1])
        classification = classify_color(bgr)
        print(f"({bgr[0]:3}, {bgr[1]:3}, {bgr[2]:3})  {count:10,}  {pct:7.3f}%  {classification}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Key colors for extraction")
    print("=" * 60)

    key_colors = []
    for bgr, count in colors:
        cls = classify_color(bgr)
        if "RED" in cls or "BLUE" in cls or cls in ["black", "dark_red"]:
            key_colors.append((bgr, count, cls))

    if key_colors:
        print("\nPotential outline colors:")
        for bgr, count, cls in key_colors[:5]:
            print(f"  {cls}: BGR({bgr[0]}, {bgr[1]}, {bgr[2]})")
    else:
        print("\nNo obvious outline colors found. May need manual inspection.")


if __name__ == "__main__":
    main()
