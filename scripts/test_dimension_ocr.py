#!/usr/bin/env python3
"""Test dimension extraction on Benedetto blueprints"""
import sys
import os
import json
from pathlib import Path

# Fix encoding for Windows console
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from dimension_extractor import DimensionExtractor

def main():
    base_dir = Path(__file__).parent.parent
    output_dir = Path(r"C:\Users\thepr\Downloads")

    # Initialize extractor (model already downloaded)
    print("Initializing dimension extractor...")
    extractor = DimensionExtractor()
    print("Ready!\n")

    for name in ["Benedetto Front.jpg", "Benedetto Back.jpg"]:
        img_path = base_dir / name
        if not img_path.exists():
            print(f"NOT FOUND: {img_path}")
            continue

        print("=" * 60)
        print(f"Extracting: {name}")
        print("=" * 60)

        result = extractor.extract_with_context(str(img_path))

        # Save to JSON
        output_json = output_dir / name.replace('.jpg', '_dimensions.json')
        with open(output_json, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        print(f"\nFound {len(result.raw_texts)} text regions")
        print(f"Extracted {len(result.dimensions)} valid dimensions\n")

        # Show top dimensions
        print("Top dimensions by confidence:")
        for dim in result.dimensions[:15]:
            ctx = f" [{dim.context[:30]}...]" if dim.context else ""
            print(f"  {dim.raw_text:15} -> {dim.value_mm:8.2f}mm  (conf={dim.confidence:.2f}){ctx}")

        print(f"\nSaved to: {output_json}")

if __name__ == "__main__":
    main()
