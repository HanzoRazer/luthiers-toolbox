#!/usr/bin/env python3
"""Extract Benedetto archtop front and back - ultimate sanity check"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import extract_guitar_blueprint, ColorFilter, load_input

def main():
    output_dir = r"C:\Users\thepr\Downloads"
    base_dir = Path(__file__).parent.parent

    for name in ["Benedetto Front.jpg", "Benedetto Back.jpg"]:
        img_path = base_dir / name

        if not img_path.exists():
            print(f"NOT FOUND: {img_path}")
            continue

        print("\n" + "=" * 60)
        print(name)
        print("=" * 60)

        # Analyze
        image = load_input(str(img_path))
        print(f"Image: {image.shape[1]}x{image.shape[0]}px")

        analysis = ColorFilter().analyze_image(image)
        print(f"Type: {analysis['blueprint_type']}")
        print(f"Method: {analysis['recommended_method']}")
        print(f"White: {analysis['white_ratio']*100:.1f}%, Dark: {analysis['dark_ratio']*100:.1f}%")

        # Extract
        results = extract_guitar_blueprint(
            source_path=str(img_path),
            output_dir=output_dir,
            instrument_type='acoustic',
            dpi=300,
            dark_threshold='auto',
            gap_close_size=5
        )

        print(f"\nContours: {results['total_contours']}")
        for layer, stats in results['layers'].items():
            print(f"  {layer}: {stats['contours']}")
        print(f"DXF: {Path(results['dxf']).name}")

if __name__ == "__main__":
    main()
