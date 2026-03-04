#!/usr/bin/env python3
"""Test integrated gap closing on Selmer Maccaferri"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf"
    output_dir = r"C:\Users\thepr\Downloads"

    print("=" * 60)
    print("Testing Gap Closing Integration")
    print("=" * 60)
    print(f"\nInput: {Path(pdf_path).name}")

    print("\nExtracting with gap_close_size=5...")
    results = extract_guitar_blueprint(
        source_path=pdf_path,
        output_dir=output_dir,
        page_num=0,
        instrument_type='acoustic',
        dpi=400,
        dark_threshold=120,
        simplify_tolerance=0.3,
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
