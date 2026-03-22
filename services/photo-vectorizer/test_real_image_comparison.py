"""
Photo Vectorizer V2 — Real-Image Performance Comparison Test
==============================================================

Runs the full pipeline on three real guitar photos and reports:
  1. Dimensional accuracy (measured vs expected body dimensions)
  2. Feature detection quality (contour count, types found)
  3. Calibration method and confidence
  4. BOM generation from extracted contours

Images:
  - Smart Guitar_1_00_original.jpg      (expected: 444.5 x 368.3 mm)
  - Black and White Benedetto_00_original.jpg  (expected: 482.6 x 431.8 mm, from benedetto_17.json)
  - Jumbo Tiger Maple Archtop…_00_original.jpg (expected: 520 x 430 mm)

Usage:
    cd services/photo-vectorizer
    python -m pytest test_real_image_comparison.py -v -s
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))

from photo_vectorizer_v2 import (
    BGRemovalMethod,
    FeatureType,
    PhotoExtractionResult,
    PhotoVectorizerV2,
    INSTRUMENT_SPECS,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GUITAR_PLANS_DIR = Path(__file__).resolve().parent.parent.parent / "Guitar Plans"

# Test subjects: (filename, spec_name_or_None, expected_body_h_mm, expected_body_w_mm, tolerance_pct)
# tolerance_pct: how close measured must be to expected (as % of expected dimension)
TEST_IMAGES = [
    {
        "name": "Smart Guitar",
        "file": "Smart Guitar_1_00_original.jpg",
        "spec": "smart_guitar",
        "expected_h_mm": 444.5,
        "expected_w_mm": 368.3,
        "tolerance_pct": 50,  # generous — photo vectorizer may measure body contour differently
    },
    {
        "name": "Black & White Benedetto",
        "file": "Black and White Benedetto_00_original.jpg",
        "spec": None,  # no v2 INSTRUMENT_SPECS entry — uses ref object calibration
        "expected_h_mm": 482.6,   # body_length_mm from benedetto_17.json
        "expected_w_mm": 431.8,   # lower_bout_mm from benedetto_17.json
        "tolerance_pct": 50,
    },
    {
        "name": "Jumbo Tiger Maple Archtop",
        "file": "Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_00_original.jpg",
        "spec": "jumbo_archtop",
        "expected_h_mm": 520.0,
        "expected_w_mm": 430.0,
        "tolerance_pct": 50,
    },
]


@dataclass
class ImageTestResult:
    """Structured result for one image test run."""
    name: str
    image_path: str
    success: bool
    error: Optional[str] = None
    input_type: str = ""
    bg_method: str = ""
    dark_bg: bool = False
    calibration_source: str = ""
    calibration_confidence: float = 0.0
    body_h_mm: float = 0.0
    body_w_mm: float = 0.0
    expected_h_mm: Optional[float] = None
    expected_w_mm: Optional[float] = None
    h_error_pct: Optional[float] = None
    w_error_pct: Optional[float] = None
    feature_counts: Dict[str, int] = None
    total_contours: int = 0
    warnings: List[str] = None
    processing_time_ms: float = 0.0
    bom_total_usd: Optional[float] = None
    bom_line_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_extraction(image_path: str, spec: Optional[str], output_dir: str) -> PhotoExtractionResult:
    """Run the full v2 pipeline on one image."""
    v = PhotoVectorizerV2(bg_method=BGRemovalMethod.AUTO)
    result = v.extract(
        image_path,
        output_dir=output_dir,
        spec_name=spec,
        export_dxf=True,
        export_svg=True,
        export_json=False,
        debug_images=False,
    )
    # Multi-instrument: take first result
    if isinstance(result, list):
        return result[0] if result else None
    return result


def _run_bom(result: PhotoExtractionResult) -> Tuple[Optional[float], int]:
    """Generate BOM from extraction result, return (total_cost, line_count)."""
    try:
        from material_bom import MaterialBOMGenerator
        gen = MaterialBOMGenerator()
        bom = gen.generate(result)
        return bom.total_cost_usd, len(bom.lines)
    except Exception:
        return None, 0


def _pct_error(measured: float, expected: float) -> float:
    """Percentage error: |measured - expected| / expected * 100."""
    if expected == 0:
        return 0.0
    return abs(measured - expected) / expected * 100


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def output_dir():
    """Shared temp output directory for all test images."""
    with tempfile.TemporaryDirectory(prefix="pv2_comparison_") as d:
        yield d


@pytest.fixture(scope="module")
def all_results(output_dir) -> List[ImageTestResult]:
    """Run extraction on all three images and collect results."""
    results = []

    for img_cfg in TEST_IMAGES:
        img_path = str(GUITAR_PLANS_DIR / img_cfg["file"])
        tr = ImageTestResult(
            name=img_cfg["name"],
            image_path=img_path,
            success=False,
            expected_h_mm=img_cfg["expected_h_mm"],
            expected_w_mm=img_cfg["expected_w_mm"],
            feature_counts={},
            warnings=[],
        )

        if not os.path.exists(img_path):
            tr.error = f"Image not found: {img_path}"
            results.append(tr)
            continue

        try:
            extraction = _run_extraction(img_path, img_cfg["spec"], output_dir)
            if extraction is None:
                tr.error = "Extraction returned None"
                results.append(tr)
                continue

            tr.success = True
            tr.input_type = extraction.input_type.value
            tr.bg_method = extraction.bg_method_used
            tr.dark_bg = extraction.dark_background_detected
            tr.body_h_mm = extraction.body_dimensions_mm[0]
            tr.body_w_mm = extraction.body_dimensions_mm[1]
            tr.processing_time_ms = extraction.processing_time_ms
            tr.warnings = extraction.warnings

            if extraction.calibration:
                tr.calibration_source = extraction.calibration.source.value
                tr.calibration_confidence = extraction.calibration.confidence

            tr.feature_counts = {
                ft.value: len(contours)
                for ft, contours in extraction.features.items()
                if contours
            }
            tr.total_contours = sum(tr.feature_counts.values())

            if img_cfg["expected_h_mm"] is not None and tr.body_h_mm > 0:
                tr.h_error_pct = _pct_error(tr.body_h_mm, img_cfg["expected_h_mm"])
            if img_cfg["expected_w_mm"] is not None and tr.body_w_mm > 0:
                tr.w_error_pct = _pct_error(tr.body_w_mm, img_cfg["expected_w_mm"])

            # BOM
            bom_cost, bom_lines = _run_bom(extraction)
            tr.bom_total_usd = bom_cost
            tr.bom_line_count = bom_lines

        except Exception as e:
            tr.error = str(e)

        results.append(tr)

    return results


# ---------------------------------------------------------------------------
# Report (printed during test)
# ---------------------------------------------------------------------------

def _print_comparison_report(results: List[ImageTestResult]):
    """Print a human-readable comparison table."""
    print("\n")
    print("=" * 100)
    print("  PHOTO VECTORIZER V2 — REAL-IMAGE PERFORMANCE COMPARISON")
    print("=" * 100)

    for tr in results:
        print(f"\n{'-' * 80}")
        print(f"  {tr.name}")
        print(f"  File: {Path(tr.image_path).name}")
        print(f"{'-' * 80}")

        if not tr.success:
            print(f"  FAILED: {tr.error}")
            continue

        print(f"  Input type:    {tr.input_type}")
        print(f"  Background:    {tr.bg_method} (dark={tr.dark_bg})")
        print(f"  Calibration:   {tr.calibration_source} (confidence={tr.calibration_confidence:.2f})")
        print(f"  Processing:    {tr.processing_time_ms:.0f}ms")

        # Dimensions
        print(f"\n  Body dimensions (measured):  {tr.body_h_mm:.1f} x {tr.body_w_mm:.1f} mm")
        if tr.expected_h_mm is not None:
            print(f"  Body dimensions (expected):  {tr.expected_h_mm:.1f} x {tr.expected_w_mm:.1f} mm")
            h_tag = f"  {tr.h_error_pct:.1f}% error" if tr.h_error_pct is not None else "  N/A"
            w_tag = f"  {tr.w_error_pct:.1f}% error" if tr.w_error_pct is not None else "  N/A"
            print(f"  Height error: {h_tag}")
            print(f"  Width error:  {w_tag}")
        else:
            print(f"  (no expected dimensions — reference-only)")

        # Features
        print(f"\n  Features ({tr.total_contours} total):")
        for ft_name, count in sorted(tr.feature_counts.items()):
            print(f"    {ft_name}: {count}")

        # BOM
        if tr.bom_total_usd is not None:
            print(f"\n  BOM: {tr.bom_line_count} lines, ${tr.bom_total_usd:.2f} estimated")

        # Warnings
        if tr.warnings:
            print(f"\n  Warnings ({len(tr.warnings)}):")
            for w in tr.warnings:
                print(f"    - {w}")

    # Summary table
    print(f"\n{'=' * 100}")
    print(f"  {'Image':<35} {'Status':<8} {'Body mm':<20} {'H err%':>8} {'W err%':>8} {'Features':>10} {'BOM $':>10}")
    print(f"  {'-'*35} {'-'*8} {'-'*20} {'-'*8} {'-'*8} {'-'*10} {'-'*10}")
    for tr in results:
        status = "OK" if tr.success else "FAIL"
        body = f"{tr.body_h_mm:.1f}x{tr.body_w_mm:.1f}" if tr.success else "---"
        h_err = f"{tr.h_error_pct:.1f}%" if tr.h_error_pct is not None else "---"
        w_err = f"{tr.w_error_pct:.1f}%" if tr.w_error_pct is not None else "---"
        feats = str(tr.total_contours) if tr.success else "---"
        bom = f"${tr.bom_total_usd:.2f}" if tr.bom_total_usd is not None else "---"
        print(f"  {tr.name:<35} {status:<8} {body:<20} {h_err:>8} {w_err:>8} {feats:>10} {bom:>10}")
    print(f"{'=' * 100}\n")


# ===================================================================
# Tests
# ===================================================================

class TestRealImageComparison:
    """Run and validate real-image extractions."""

    def test_all_images_load(self, all_results):
        """All three test images should be found on disk."""
        for tr in all_results:
            assert tr.error is None or "not found" not in (tr.error or ""), \
                f"Image missing: {tr.name} — {tr.error}"

    def test_all_extractions_succeed(self, all_results):
        """Each image should extract without crashing."""
        for tr in all_results:
            if tr.error and "not found" in tr.error:
                pytest.skip(f"Image not available: {tr.name}")
            assert tr.success, f"{tr.name} failed: {tr.error}"

    def test_all_produce_features(self, all_results):
        """Each successful extraction should detect at least 1 feature contour."""
        for tr in all_results:
            if not tr.success:
                continue
            assert tr.total_contours >= 1, \
                f"{tr.name}: no features detected"

    def test_all_have_body_outline(self, all_results):
        """Each successful extraction should include at least one body_outline."""
        for tr in all_results:
            if not tr.success:
                continue
            assert tr.feature_counts.get("body_outline", 0) >= 1, \
                f"{tr.name}: missing body_outline"

    def test_calibration_present(self, all_results):
        """Each successful result should have a calibration source."""
        for tr in all_results:
            if not tr.success:
                continue
            assert tr.calibration_source != "", \
                f"{tr.name}: no calibration source"

    def test_body_dimensions_nonzero(self, all_results):
        """Body dimensions should be > 0 for all successful extractions."""
        for tr in all_results:
            if not tr.success:
                continue
            assert tr.body_h_mm > 0, f"{tr.name}: body height = 0"
            assert tr.body_w_mm > 0, f"{tr.name}: body width = 0"

    def test_smart_guitar_dimensional_accuracy(self, all_results):
        """Smart Guitar: measured dimensions should be within tolerance of spec."""
        tr = next((r for r in all_results if r.name == "Smart Guitar"), None)
        if tr is None or not tr.success:
            pytest.skip("Smart Guitar extraction not available")

        # Expected: 444.5 x 368.3 mm — allow 50% tolerance for photo-based extraction
        tolerance = 50
        if tr.h_error_pct is not None:
            assert tr.h_error_pct < tolerance, \
                f"Smart Guitar height error {tr.h_error_pct:.1f}% exceeds {tolerance}%"
        if tr.w_error_pct is not None:
            assert tr.w_error_pct < tolerance, \
                f"Smart Guitar width error {tr.w_error_pct:.1f}% exceeds {tolerance}%"

    def test_archtop_dimensional_accuracy(self, all_results):
        """Jumbo Archtop: measured dimensions should be within tolerance of spec."""
        tr = next((r for r in all_results if "Archtop" in r.name), None)
        if tr is None or not tr.success:
            pytest.skip("Archtop extraction not available")

        tolerance = 50
        if tr.h_error_pct is not None:
            assert tr.h_error_pct < tolerance, \
                f"Archtop height error {tr.h_error_pct:.1f}% exceeds {tolerance}%"
        if tr.w_error_pct is not None:
            assert tr.w_error_pct < tolerance, \
                f"Archtop width error {tr.w_error_pct:.1f}% exceeds {tolerance}%"

    def test_benedetto_dimensional_accuracy(self, all_results):
        """Benedetto 17": measured dimensions should be within tolerance of benedetto_17.json spec."""
        tr = next((r for r in all_results if "Benedetto" in r.name), None)
        if tr is None or not tr.success:
            pytest.skip("Benedetto extraction not available")

        # Expected: 482.6 x 431.8 mm (body_length x lower_bout from benedetto_17.json)
        tolerance = 50
        if tr.h_error_pct is not None:
            assert tr.h_error_pct < tolerance, \
                f"Benedetto height error {tr.h_error_pct:.1f}% exceeds {tolerance}%"
        if tr.w_error_pct is not None:
            assert tr.w_error_pct < tolerance, \
                f"Benedetto width error {tr.w_error_pct:.1f}% exceeds {tolerance}%"

    def test_bom_generated_for_all(self, all_results):
        """BOM should generate for all successful extractions with features."""
        for tr in all_results:
            if not tr.success or tr.total_contours == 0:
                continue
            assert tr.bom_line_count > 0, \
                f"{tr.name}: BOM generated 0 lines despite having {tr.total_contours} features"

    def test_print_report(self, all_results):
        """Print the full comparison report (always passes)."""
        _print_comparison_report(all_results)
