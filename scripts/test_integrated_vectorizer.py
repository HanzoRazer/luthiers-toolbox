#!/usr/bin/env python3
"""
Test the integrated vectorizer with guitar feature extraction
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint

def main():
    # Test with the Jazzmaster routing PDF
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body-Route-Pickguard.pdf"
    output_dir = r"C:\Users\thepr\Downloads"

    print("=" * 60)
    print("Testing Integrated Vectorizer")
    print("=" * 60)
    print(f"\nInput: {Path(pdf_path).name}")
    print(f"Output: {output_dir}")

    print("\n" + "-" * 60)
    print("Running extract_guitar_blueprint()...")
    print("-" * 60)

    results = extract_guitar_blueprint(
        source_path=pdf_path,
        output_dir=output_dir,
        page_num=0,
        instrument_type='electric',
        dpi=400,
        dark_threshold=100,
        simplify_tolerance=0.1
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nSVG: {results['svg']}")
    print(f"DXF: {results['dxf']}")

    print("\nExtracted layers:")
    for layer_name, stats in results['layers'].items():
        print(f"  {layer_name}:")
        print(f"    Contours: {stats['contours']}")

    print(f"\nTotal contours: {results['total_contours']}")

    print("\n" + "=" * 60)
    print("Test complete! Check the DXF in TrueView.")
    print("=" * 60)

if __name__ == "__main__":
    main()
