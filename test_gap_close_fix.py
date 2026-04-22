#!/usr/bin/env python3
"""
Test script to verify morphological gap closing fix in enhanced mode.
Compares output to March 6 baseline.
"""

import sys
import os
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))
sys.path.insert(0, str(Path(__file__).parent / "services" / "photo-vectorizer"))

from app.services.blueprint_orchestrator import BlueprintOrchestrator
from app.services.blueprint_clean import CleanupMode


def test_file(source_path: Path, output_dir: Path, name: str):
    """Process a single file and output DXF + SVG."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Source: {source_path}")
    print(f"{'='*60}")

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        return None

    # Read file bytes
    with open(source_path, "rb") as f:
        file_bytes = f.read()

    # Create orchestrator and process
    orchestrator = BlueprintOrchestrator()
    result = orchestrator.process_file(
        file_bytes=file_bytes,
        filename=source_path.name,
        target_height_mm=500.0,
        mode=CleanupMode.ENHANCED,
        gap_close_size=7,  # The fix - morphological closing
        debug=True,
    )

    # Report results
    print(f"\nResult: ok={result.ok}, stage={result.stage}")
    if result.error:
        print(f"Error: {result.error}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")

    print(f"\nDimensions: {result.dimensions.width_mm:.1f} x {result.dimensions.height_mm:.1f} mm")
    print(f"DXF entities: {result.dxf.entity_count}")
    print(f"DXF closed contours: {result.dxf.closed_contours}")

    # Save DXF
    if result.dxf.present and result.dxf.base64:
        import base64
        dxf_path = output_dir / f"{name}_gapclose7.dxf"
        dxf_bytes = base64.b64decode(result.dxf.base64)
        with open(dxf_path, "wb") as f:
            f.write(dxf_bytes)
        print(f"\nDXF saved: {dxf_path}")
        print(f"DXF size: {len(dxf_bytes):,} bytes")

    # Save SVG
    if result.svg.present and result.svg.content:
        svg_path = output_dir / f"{name}_gapclose7.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(result.svg.content)
        print(f"SVG saved: {svg_path}")
        print(f"SVG path count: {result.svg.path_count}")

    return result


def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / "benchmark_outputs"
    output_dir.mkdir(exist_ok=True)

    # Test files
    test_cases = [
        (
            base_dir / "Guitar Plans" / "El Cuatro" / "cuatro puertoriqueño.pdf",
            "cuatro_puertoriqueno"
        ),
        (
            base_dir / "Guitar Plans" / "Gibson-Melody-Maker.pdf",
            "gibson_melody_maker"
        ),
    ]

    results = {}
    for source_path, name in test_cases:
        result = test_file(source_path, output_dir, name)
        results[name] = result

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    # Compare to March 6 baseline
    march6_baseline = base_dir / "Guitar Plans" / "El Cuatro" / "cuatro_puertoriqueño_simple.dxf"
    if march6_baseline.exists():
        baseline_size = march6_baseline.stat().st_size
        print(f"\nMarch 6 baseline (cuatro): {baseline_size:,} bytes")

        if "cuatro_puertoriqueno" in results and results["cuatro_puertoriqueno"]:
            new_dxf = output_dir / "cuatro_puertoriqueno_gapclose7.dxf"
            if new_dxf.exists():
                new_size = new_dxf.stat().st_size
                ratio = new_size / baseline_size
                print(f"New output:                {new_size:,} bytes")
                print(f"Ratio (new/baseline):      {ratio:.2f}x")

                if ratio > 0.8:
                    print("✓ Output size is comparable to March 6 breakthrough")
                else:
                    print("✗ Output size is significantly smaller than baseline")

    print("\nDone.")


if __name__ == "__main__":
    main()
