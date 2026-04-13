#!/usr/bin/env python
"""
Blueprint Vectorizer Benchmark Runner
=====================================

Runs benchmark files through multiple modes and produces comparison report.

Usage:
    python scripts/run_blueprint_benchmark.py --file "Guitar Plans/Gibson-Melody-Maker.pdf"
    python scripts/run_blueprint_benchmark.py --manifest benchmark_manifest.json --modes refined baseline restored_baseline

Output:
    benchmark_comparison.md
    benchmark_results.json

Author: Production Shop
Date: 2026-04-13
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

# Add services to path
repo_root = Path(__file__).parents[1]
sys.path.insert(0, str(repo_root / "services" / "api"))
sys.path.insert(0, str(repo_root / "services" / "photo-vectorizer"))


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    file: str
    mode: str
    ok: bool
    stage: str
    error: str
    width_mm: float
    height_mm: float
    entity_count: int
    svg_paths: int
    selection_score: float
    winner_margin: float
    action: str
    fallback_used: bool
    fallback_tier: int
    is_page_like: bool
    is_body_like: bool
    warnings: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def is_page_like_dimensions(width_mm: float, height_mm: float) -> bool:
    """Check if dimensions match common page sizes."""
    page_sizes = [
        (841, 594),  # A1
        (594, 420),  # A2
        (420, 297),  # A3
        (297, 210),  # A4
        (11 * 25.4, 8.5 * 25.4),  # Letter
        (17 * 25.4, 11 * 25.4),   # Tabloid
    ]

    for pw, ph in page_sizes:
        if (abs(width_mm - pw) < 20 and abs(height_mm - ph) < 20) or \
           (abs(width_mm - ph) < 20 and abs(height_mm - pw) < 20):
            return True
    return False


def is_body_like_dimensions(width_mm: float, height_mm: float) -> bool:
    """Check if dimensions are plausible for guitar body."""
    # Guitar bodies typically 200-500mm wide, 300-600mm tall
    if 150 < width_mm < 550 and 250 < height_mm < 650:
        return True
    # Also accept reasonable aspect ratios for scaled output
    aspect = max(width_mm, height_mm) / max(min(width_mm, height_mm), 1)
    if 1.0 < aspect < 2.5:
        return True
    return False


def run_benchmark(file_path: Path, mode: str) -> BenchmarkResult:
    """Run a single benchmark file through the pipeline."""
    from app.services.blueprint_orchestrator import BlueprintOrchestrator
    from app.services.blueprint_clean import CleanupMode

    # Load file
    file_bytes = file_path.read_bytes()

    # Parse mode
    try:
        cleanup_mode = CleanupMode(mode.lower())
    except ValueError:
        cleanup_mode = CleanupMode.REFINED

    # Run orchestrator
    orchestrator = BlueprintOrchestrator()
    result = orchestrator.process_file(
        file_bytes=file_bytes,
        filename=file_path.name,
        page_num=0,
        target_height_mm=500.0,
        mode=cleanup_mode,
        debug=True,
    )

    # Extract metrics
    width_mm = result.dimensions.width_mm
    height_mm = result.dimensions.height_mm

    # Check for fallback in debug
    fallback_used = result.debug.get("fallback_used", False) if result.debug else False
    fallback_tier = result.debug.get("fallback_tier", 0) if result.debug else 0

    return BenchmarkResult(
        file=file_path.name,
        mode=mode,
        ok=result.ok,
        stage=result.stage,
        error=result.error,
        width_mm=width_mm,
        height_mm=height_mm,
        entity_count=result.dxf.entity_count,
        svg_paths=result.svg.path_count,
        selection_score=result.selection.selection_score,
        winner_margin=result.selection.winner_margin,
        action=str(result.recommendation.action),
        fallback_used=fallback_used,
        fallback_tier=fallback_tier,
        is_page_like=is_page_like_dimensions(width_mm, height_mm),
        is_body_like=is_body_like_dimensions(width_mm, height_mm),
        warnings=result.warnings[:5],  # Truncate
    )


def generate_comparison_report(results: List[BenchmarkResult]) -> str:
    """Generate markdown comparison report."""
    lines = [
        "# Blueprint Vectorizer Benchmark Comparison",
        "",
        f"Generated: {Path(__file__).stat().st_mtime if Path(__file__).exists() else 'N/A'}",
        "",
        "## Summary",
        "",
        "| File | Mode | Dims (mm) | Entities | Score | Margin | Action | Page-like | Body-like |",
        "|------|------|-----------|----------|-------|--------|--------|-----------|-----------|",
    ]

    for r in results:
        dims = f"{r.width_mm:.0f}x{r.height_mm:.0f}"
        page_flag = "YES" if r.is_page_like else "-"
        body_flag = "YES" if r.is_body_like else "-"
        lines.append(
            f"| {r.file[:30]} | {r.mode} | {dims} | {r.entity_count:,} | "
            f"{r.selection_score:.2f} | {r.winner_margin:.2f} | {r.action.split('.')[-1]} | "
            f"{page_flag} | {body_flag} |"
        )

    lines.extend([
        "",
        "## Mode Comparison",
        "",
    ])

    # Group by file
    files = sorted(set(r.file for r in results))
    for file in files:
        file_results = [r for r in results if r.file == file]
        lines.append(f"### {file}")
        lines.append("")

        for r in file_results:
            status = "PASS" if r.is_body_like and not r.is_page_like else "FAIL"
            lines.append(f"**{r.mode}**: {status}")
            lines.append(f"- Dimensions: {r.width_mm:.0f} x {r.height_mm:.0f} mm")
            lines.append(f"- Entities: {r.entity_count:,}")
            lines.append(f"- Selection score: {r.selection_score:.3f}")
            lines.append(f"- Winner margin: {r.winner_margin:.3f}")
            lines.append(f"- Action: {r.action}")
            if r.fallback_used:
                lines.append(f"- Fallback tier: {r.fallback_tier}")
            lines.append("")

    lines.extend([
        "## Recommendations",
        "",
        "Based on the benchmark results:",
        "",
    ])

    # Analyze results
    restored_wins = sum(1 for r in results if r.mode == "restored_baseline" and r.is_body_like)
    refined_wins = sum(1 for r in results if r.mode == "refined" and r.is_body_like)

    if restored_wins > refined_wins:
        lines.append("- `restored_baseline` mode produces better results for this benchmark set")
        lines.append("- Consider using `restored_baseline` as default for blueprint PDFs")
    elif refined_wins > restored_wins:
        lines.append("- `refined` mode produces better results for this benchmark set")
    else:
        lines.append("- Results are comparable between modes")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Blueprint vectorizer benchmark runner")
    parser.add_argument("--file", type=str, help="Single file to benchmark")
    parser.add_argument("--manifest", type=str, help="JSON manifest of files to benchmark")
    parser.add_argument("--modes", type=str, nargs="+", default=["refined", "restored_baseline"],
                       help="Modes to test")
    parser.add_argument("--output", type=str, default="benchmark_comparison.md",
                       help="Output report path")
    args = parser.parse_args()

    # Collect files
    files: List[Path] = []
    if args.file:
        files.append(Path(args.file))
    elif args.manifest:
        with open(args.manifest) as f:
            manifest = json.load(f)
        for entry in manifest.get("files", []):
            files.append(Path(entry["path"]))
    else:
        # Default: Melody Maker
        melody_maker = repo_root / "Guitar Plans" / "Gibson-Melody-Maker.pdf"
        if melody_maker.exists():
            files.append(melody_maker)

    if not files:
        print("No files to benchmark")
        return 1

    # Run benchmarks
    results: List[BenchmarkResult] = []
    for file_path in files:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"Benchmarking: {file_path.name}")
        for mode in args.modes:
            print(f"  Mode: {mode}...")
            try:
                result = run_benchmark(file_path, mode)
                results.append(result)
                print(f"    Dims: {result.width_mm:.0f}x{result.height_mm:.0f}mm, "
                      f"Score: {result.selection_score:.2f}, "
                      f"Body-like: {result.is_body_like}")
            except Exception as e:
                print(f"    ERROR: {e}")

    # Generate report
    if results:
        report = generate_comparison_report(results)
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"\nReport written to: {output_path}")

        # Also save JSON
        json_path = output_path.with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        print(f"JSON written to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
