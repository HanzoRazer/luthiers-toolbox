#!/usr/bin/env python3
"""
Test the enhanced Phase 2 Vectorizer on Jazzmaster PDF
"""
import sys
from pathlib import Path

# Add blueprint-import to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import create_phase2_vectorizer

def main():
    # Paths
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    output_dir = r"C:\Users\thepr\Downloads"

    print("=" * 60)
    print("Testing Enhanced Vectorizer on Jazzmaster PDF")
    print("=" * 60)
    print(f"\nInput PDF: {pdf_path}")
    print(f"Page: 3 (index 2) - Clean Jazzmaster outline")
    print(f"Output directory: {output_dir}")

    # Create vectorizer with color tolerance
    print("\nCreating vectorizer with color_tolerance=30...")
    vectorizer = create_phase2_vectorizer(color_tolerance=30)

    # Run the vectorization
    print("\n" + "-" * 60)
    print("Running vectorization with color filtering...")
    print("Colors to extract: red, black")
    print("-" * 60)

    try:
        results = vectorizer.analyze_and_vectorize(
            source_path=pdf_path,
            page_num=2,  # Page 3 = index 2 (Jazzmaster in red/black)
            output_dir=output_dir,
            colors_to_extract=['red', 'black'],
            select_largest=True
        )

        # Print results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        print(f"\nSVG saved to: {results['svg']}")
        print(f"DXF saved to: {results['dxf']}")
        print(f"Source page: {results['page'] + 1}")
        print(f"Image size: {results['image_size'][0]} x {results['image_size'][1]} pixels")

        print("\nLayer statistics:")
        for layer_name, stats in results['layers'].items():
            print(f"  {layer_name}:")
            print(f"    Contours: {stats['contours']}")
            print(f"    Lines: {stats['lines']}")
            print(f"    Circles: {stats['circles']}")

        print(f"\nTotal contours: {results['total_contours']}")
        print(f"Total lines: {results['total_lines']}")

        print("\n" + "=" * 60)
        print("Please check the DXF in DWG TrueView to verify the output.")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
