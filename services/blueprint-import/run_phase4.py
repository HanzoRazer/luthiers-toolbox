#!/usr/bin/env python3
"""
Phase 4.0 CLI - Run dimension linking pipeline
===============================================

Usage:
    python run_phase4.py <blueprint.pdf>
    python run_phase4.py <blueprint.pdf> --debug
    python run_phase4.py <blueprint.pdf> --json

Author: Luthier's Toolbox
Version: 4.0.0
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from phase4.pipeline import BlueprintPipeline, process_blueprint


def main():
    parser = argparse.ArgumentParser(
        description="Process blueprint with Phase 4.0 dimension linking"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF blueprint"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for rendering (default: 300)"
    )
    parser.add_argument(
        "--instrument",
        type=str,
        help="Instrument type hint (e.g., electric_guitar)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with mock arrows"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for JSON"
    )

    args = parser.parse_args()

    # Validate path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    print(f"Processing: {pdf_path.name}")
    print("=" * 60)

    try:
        # Run pipeline
        result = process_blueprint(
            str(pdf_path),
            dpi=args.dpi,
            instrument_type=args.instrument,
            debug_mode=args.debug
        )

        if args.json:
            output = json.dumps(result.to_dict(), indent=2)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Output written to: {args.output}")
            else:
                print(output)
        else:
            # Human-readable output
            print(result.summary())

            if result.linked_dimensions and result.linked_dimensions.dimensions:
                print(f"\nLinked Dimensions:")
                print("-" * 40)
                for dim in result.linked_dimensions.dimensions[:20]:
                    text = dim.text_region.text
                    method = dim.association_method
                    score = getattr(dim, 'ranking_score', 0.0)
                    target = dim.target_feature.category if dim.target_feature else "?"
                    print(f"  '{text}' -> {target} ({method}, score={score:.1f})")

                if len(result.linked_dimensions.dimensions) > 20:
                    print(f"  ... and {len(result.linked_dimensions.dimensions) - 20} more")

            if result.linked_dimensions and result.linked_dimensions.unmatched_texts:
                print(f"\nUnmatched Texts:")
                print("-" * 40)
                for text in result.linked_dimensions.unmatched_texts[:10]:
                    print(f"  '{text.text}' ({text.parsed_value} {text.unit})")

                if len(result.linked_dimensions.unmatched_texts) > 10:
                    print(f"  ... and {len(result.linked_dimensions.unmatched_texts) - 10} more")

    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
