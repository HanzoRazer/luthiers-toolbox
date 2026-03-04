#!/usr/bin/env python3
"""Test auto-threshold on both dark-line and faint-line blueprints"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint, ColorFilter, rasterize_pdf

def test_blueprint(name, pdf_path, instrument_type):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print("=" * 60)

    # Analyze the image
    image = rasterize_pdf(pdf_path, page_num=0, dpi=400)
    color_filter = ColorFilter()
    analysis = color_filter.analyze_image(image)

    print(f"\nImage Analysis:")
    print(f"  Blueprint type: {analysis['blueprint_type']}")
    print(f"  Recommended method: {analysis['recommended_method']}")
    print(f"  White ratio: {analysis['white_ratio']*100:.1f}%")
    print(f"  Dark ratio: {analysis['dark_ratio']*100:.1f}%")
    print(f"  Min pixel: {analysis['min_pixel']}")
    print(f"  Max pixel: {analysis['max_pixel']}")

    # Extract with auto-threshold
    results = extract_guitar_blueprint(
        source_path=pdf_path,
        output_dir=r"C:\Users\thepr\Downloads",
        instrument_type=instrument_type,
        dpi=400,
        dark_threshold='auto',
        gap_close_size=5
    )

    print(f"\nExtraction Results:")
    for layer, stats in results['layers'].items():
        print(f"  {layer}: {stats['contours']} contour(s)")
    print(f"Total: {results['total_contours']} contours")

    return results['total_contours']

def main():
    # Test 1: Gibson 335 (faint lines)
    gibson_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Gibson-335-Full-1.pdf"

    # Test 2: Selmer Maccaferri (dark lines)
    selmer_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf"

    print("AUTO-THRESHOLD DETECTION TEST")
    print("=" * 60)

    gibson_count = test_blueprint("Gibson ES-335 (faint lines)", gibson_path, 'electric')
    selmer_count = test_blueprint("Selmer Maccaferri (dark lines)", selmer_path, 'acoustic')

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Gibson ES-335: {gibson_count} contours extracted")
    print(f"Selmer Maccaferri: {selmer_count} contours extracted")

    if gibson_count > 0 and selmer_count > 0:
        print("\n[PASS] Auto-threshold works on both blueprint types!")
    else:
        print("\n[FAIL] Auto-threshold failed on one or more blueprints")

if __name__ == "__main__":
    main()
