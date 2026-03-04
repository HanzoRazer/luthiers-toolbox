#!/usr/bin/env python3
"""Test auto-threshold on Jazzmaster blueprint"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint, ColorFilter, rasterize_pdf

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body.pdf"
    output_dir = r"C:\Users\thepr\Downloads"

    print("=" * 60)
    print("Jazzmaster Auto-Threshold Test")
    print("=" * 60)

    # Analyze the image first
    image = rasterize_pdf(pdf_path, page_num=0, dpi=400)
    color_filter = ColorFilter()
    analysis = color_filter.analyze_image(image)

    print(f"\nImage Analysis:")
    print(f"  Blueprint type: {analysis['blueprint_type']}")
    print(f"  Recommended method: {analysis['recommended_method']}")
    print(f"  Recommended threshold: {analysis['recommended_threshold']}")
    print(f"  White ratio: {analysis['white_ratio']*100:.1f}%")
    print(f"  Dark ratio: {analysis['dark_ratio']*100:.1f}%")
    print(f"  Min pixel: {analysis['min_pixel']}")
    print(f"  Max pixel: {analysis['max_pixel']}")

    # Extract with auto-threshold
    print("\nExtracting with auto-threshold...")
    results = extract_guitar_blueprint(
        source_path=pdf_path,
        output_dir=output_dir,
        instrument_type='electric',
        dpi=400,
        dark_threshold='auto',
        gap_close_size=5
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nDXF: {results['dxf']}")

    print("\nExtracted layers:")
    for layer, stats in results['layers'].items():
        print(f"  {layer}: {stats['contours']} contour(s)")

    print(f"\nTotal: {results['total_contours']} contours")

if __name__ == "__main__":
    main()
