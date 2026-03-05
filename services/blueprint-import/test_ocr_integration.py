#!/usr/bin/env python3
"""Test OCR integration with Phase 3.5 vectorizer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vectorizer_phase3 import Phase3Vectorizer, InstrumentType

def main():
    # Test blueprint
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Gibson-Melody-Maker.pdf"

    print(f"Testing OCR integration on: {Path(pdf_path).name}")
    print("=" * 60)

    # Initialize with OCR enabled
    vectorizer = Phase3Vectorizer(
        dpi=300,
        enable_ocr=True,
        enable_primitives=True,
        enable_scale_detection=True
    )

    # Extract
    result = vectorizer.extract(
        pdf_path,
        instrument_type=InstrumentType.ELECTRIC_GUITAR,
        validate=False  # Skip validation for test
    )

    # Print summary
    summary = result.summary()
    print(f"\nExtraction Summary:")
    print(f"  Body dimensions: {summary['body_size_mm'][0]:.1f} x {summary['body_size_mm'][1]:.1f} mm")
    print(f"  Features: {summary['features']}")
    print(f"  Primitives: {summary['primitives_count']}")
    print(f"  Processing time: {summary['processing_time_ms']:.0f}ms")

    print(f"\nOCR Results:")
    print(f"  Raw texts detected: {summary['ocr_raw_texts_count']}")
    print(f"  Dimensions parsed: {summary['ocr_dimensions_count']}")

    if result.ocr_dimensions:
        print(f"\n  Top 15 dimensions:")
        for dim in result.ocr_dimensions[:15]:
            context = f" ({dim['context']})" if dim['context'] else ""
            print(f"    '{dim['raw_text']}' -> {dim['value_mm']:.2f}mm ({dim['unit']}){context}")

    print(f"\n  Output DXF: {result.output_dxf}")


if __name__ == "__main__":
    main()
