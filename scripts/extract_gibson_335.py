#!/usr/bin/env python3
"""Extract Gibson ES-335 using auto-threshold detection"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Gibson-335-Full-1.pdf"
    output_dir = r"C:\Users\thepr\Downloads"

    print("=" * 60)
    print("Gibson ES-335 Extraction - Auto-Threshold")
    print("=" * 60)

    # Use auto-threshold (the new default)
    results = extract_guitar_blueprint(
        source_path=pdf_path,
        output_dir=output_dir,
        instrument_type='electric',
        dpi=400,
        dark_threshold='auto',  # NEW: auto-detect best threshold
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
