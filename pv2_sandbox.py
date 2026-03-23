#!/usr/bin/env python3
"""
Photo-Vectorizer v2 — Standalone Sandbox
=========================================
Runs the pipeline on any image with full control over parameters.
No FastAPI, no Vue, no Blueprint Lab — just the Python pipeline.

Usage:
    python pv2_sandbox.py <image_path> [options]

Examples:
    python pv2_sandbox.py "Smart Guitar_1_00_original.jpg"
    python pv2_sandbox.py "ChatGPT Image Mar 9.png" --spec stratocaster
    python pv2_sandbox.py "Jumbo Tiger.jpg" --bg-method grabcut --tolerance 20
    python pv2_sandbox.py --batch "Guitar Plans/"
    python pv2_sandbox.py "problem_image.jpg" --cognitive --spec dreadnought

Options:
    --spec          Instrument spec name (smart_guitar, stratocaster, dreadnought, etc.)
    --source-type   Image source: auto, ai, photo (default: auto)
                    - auto:  detect AI vs photo automatically
                    - ai:    force simpler AI extraction path (requires --spec)
                    - photo: force traditional 12-stage photo pipeline
    --bg-method     Background removal: auto, grabcut, rembg, threshold (default: auto)
    --tolerance     Accuracy tolerance % for pass/fail gate (default: 30)
    --output-dir    Where to write DXF/SVG outputs (default: ./sandbox_output)
    --no-dxf        Skip DXF export
    --no-svg        Skip SVG export
    --debug         Save intermediate pipeline images
    --batch         Run on all images in a directory
    --compare       Compare against baseline results (reads sandbox_baseline.json)
    --save-baseline Save current results as new baseline
    --cognitive     Enable cognitive extraction engine as fallback
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

# ── Path setup ─────────────────────────────────────────────────────────────────
THIS_DIR = Path(__file__).parent
VECTORIZER_DIR = THIS_DIR / "services" / "photo-vectorizer"
sys.path.insert(0, str(VECTORIZER_DIR))

# ── Check dependencies ─────────────────────────────────────────────────────────
def check_deps():
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import rembg
    except ImportError:
        missing.append("rembg  # pip install rembg")
    if missing:
        print("Missing dependencies:")
        for m in missing:
            print(f"  pip install {m}")
        print()
        print("rembg is optional — pipeline falls back to GrabCut if not installed.")
        print("Install with: pip install rembg")

check_deps()

from photo_vectorizer_v2 import (
    BGRemovalMethod,
    PhotoExtractionResult,
    PhotoVectorizerV2,
    INSTRUMENT_SPECS,
)


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    image_name: str
    spec: Optional[str]
    bg_method: str
    success: bool
    error: Optional[str]

    # Dimensions
    body_h_mm: float
    body_w_mm: float
    expected_h_mm: Optional[float]
    expected_w_mm: Optional[float]
    h_error_pct: Optional[float]
    w_error_pct: Optional[float]
    passed_tolerance: Optional[bool]

    # Pipeline details
    calibration_source: str
    calibration_confidence: float
    dark_background: bool
    input_type: str
    processing_time_s: float
    total_features: int
    feature_breakdown: Dict[str, int]
    warnings: List[str]

    # Output files
    dxf_path: Optional[str]
    svg_path: Optional[str]

    # Cognitive extraction
    cognitive_used: bool = False
    cognitive_iterations: int = 0


def _pct_error(measured: float, expected: float) -> float:
    if expected <= 0:
        return 0.0
    return abs(measured - expected) / expected * 100


def _bg_method(name: str) -> BGRemovalMethod:
    mapping = {
        "auto": BGRemovalMethod.AUTO,
        "grabcut": BGRemovalMethod.GRABCUT,
        "rembg": BGRemovalMethod.REMBG,
        "threshold": BGRemovalMethod.THRESHOLD,
    }
    return mapping.get(name.lower(), BGRemovalMethod.AUTO)


def _try_cognitive_extraction(
    image_path: str,
    spec: Optional[str],
    source_type: str,
    debug: bool,
) -> Optional[dict]:
    """
    Attempt cognitive extraction as fallback.
    Returns dict with 'contour' and metadata, or None on failure.
    """
    try:
        from cognitive_extraction_engine import CognitiveExtractionEngine
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            return None

        engine = CognitiveExtractionEngine(
            grid_size=16,
            max_iterations=5,
            source_type=source_type,
            spec_name=spec,
        )
        result = engine.run(img)

        if result.get('bypassed'):
            print(f"  [cognitive] Bypassed: {result.get('bypassed_reason', 'unknown')}")
            return None

        if result.get('contour') is not None:
            return result

        return None
    except ImportError:
        print("  [cognitive] CognitiveExtractionEngine not available")
        return None
    except Exception as e:
        print(f"  [cognitive] Error: {e}")
        return None


def run_single(
    image_path: str,
    spec: Optional[str] = None,
    bg_method: str = "auto",
    output_dir: str = "sandbox_output",
    export_dxf: bool = True,
    export_svg: bool = True,
    debug: bool = False,
    tolerance_pct: float = 30.0,
    source_type: str = "auto",
    use_cognitive: bool = False,
) -> SandboxResult:
    """Run the full pipeline on one image and return a structured result."""

    image_path = str(Path(image_path).resolve())
    image_name = Path(image_path).name
    out_dir = str(Path(output_dir).resolve())
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    result = SandboxResult(
        image_name=image_name,
        spec=spec,
        bg_method=bg_method,
        success=False,
        error=None,
        body_h_mm=0.0, body_w_mm=0.0,
        expected_h_mm=None, expected_w_mm=None,
        h_error_pct=None, w_error_pct=None,
        passed_tolerance=None,
        calibration_source="", calibration_confidence=0.0,
        dark_background=False, input_type="",
        processing_time_s=0.0, total_features=0,
        feature_breakdown={}, warnings=[],
        dxf_path=None, svg_path=None,
        cognitive_used=False, cognitive_iterations=0,
    )

    # Pull expected dimensions from INSTRUMENT_SPECS if spec given
    if spec and spec in INSTRUMENT_SPECS:
        spec_data = INSTRUMENT_SPECS[spec]
        body = spec_data.get("body", (None, None))
        result.expected_h_mm = body[0]
        result.expected_w_mm = body[1]

    t0 = time.time()
    extraction = None

    try:
        v = PhotoVectorizerV2(bg_method=_bg_method(bg_method))
        extraction = v.extract(
            image_path,
            output_dir=out_dir,
            spec_name=spec,
            export_dxf=export_dxf,
            export_svg=export_svg,
            export_json=False,
            debug_images=debug,
            source_type=source_type,
        )

        # Handle multi-instrument list
        if isinstance(extraction, list):
            extraction = extraction[0] if extraction else None

    except Exception as e:
        result.error = str(e)
        extraction = None

    # Try cognitive fallback if enabled and standard pipeline failed
    if extraction is None and use_cognitive:
        print("  [cognitive] Standard pipeline failed, trying cognitive extraction...")
        cog_result = _try_cognitive_extraction(image_path, spec, source_type, debug)
        if cog_result and cog_result.get('contour') is not None:
            result.cognitive_used = True
            result.cognitive_iterations = cog_result.get('iterations', 0)
            result.warnings.append("Extracted via cognitive fallback")

            # Cognitive extraction doesn't produce full PhotoExtractionResult
            # Just mark as partial success for now
            result.success = True
            result.input_type = "cognitive"
            result.processing_time_s = time.time() - t0
            result.total_features = 1  # body contour
            result.feature_breakdown = {"body": 1}

            # Try to get body dimensions from contour
            contour = cog_result.get('contour')
            if contour is not None:
                import cv2
                x, y, w, h = cv2.boundingRect(contour)
                # Assume 96 DPI for pixel-to-mm conversion without calibration
                px_per_mm = 96 / 25.4
                result.body_h_mm = h / px_per_mm
                result.body_w_mm = w / px_per_mm
                if result.body_w_mm > result.body_h_mm:
                    result.body_h_mm, result.body_w_mm = result.body_w_mm, result.body_h_mm

            return result

    if extraction is None:
        if result.error is None:
            result.error = "Pipeline returned None"
        result.processing_time_s = time.time() - t0
        return result

    result.success = True
    result.processing_time_s = time.time() - t0

    h, w = extraction.body_dimensions_mm
    # Normalize: height > width for guitar bodies
    if w > h:
        h, w = w, h
    result.body_h_mm = h
    result.body_w_mm = w

    result.input_type = extraction.input_type.value if hasattr(extraction.input_type, 'value') else str(extraction.input_type)
    result.dark_background = extraction.dark_background_detected
    result.warnings = list(extraction.warnings or [])

    if extraction.calibration:
        cal = extraction.calibration
        result.calibration_source = cal.source.value if hasattr(cal.source, 'value') else str(cal.source)
        result.calibration_confidence = cal.confidence

    result.feature_breakdown = {
        ft.value if hasattr(ft, 'value') else str(ft): len(contours)
        for ft, contours in extraction.features.items()
        if contours
    }
    result.total_features = sum(result.feature_breakdown.values())

    # Accuracy check
    if result.expected_h_mm and h > 0:
        result.h_error_pct = _pct_error(h, result.expected_h_mm)
    if result.expected_w_mm and w > 0:
        result.w_error_pct = _pct_error(w, result.expected_w_mm)

    if result.h_error_pct is not None and result.w_error_pct is not None:
        result.passed_tolerance = (
            result.h_error_pct < tolerance_pct and
            result.w_error_pct < tolerance_pct
        )

    # Find output files
    stem = Path(image_path).stem
    for f in Path(out_dir).iterdir():
        if stem in f.name or "photo_v2" in f.name:
            if f.suffix == ".dxf":
                result.dxf_path = str(f)
            elif f.suffix == ".svg":
                result.svg_path = str(f)

    return result


# ── Report printing ─────────────────────────────────────────────────────────────

def print_result(r: SandboxResult, verbose: bool = True):
    status = "PASS" if r.success else "FAIL"
    gate = ""
    if r.passed_tolerance is True:
        gate = " [ACCURATE]"
    elif r.passed_tolerance is False:
        gate = " [INACCURATE]"

    print(f"\n{'='*70}")
    print(f"  {r.image_name}")
    print(f"  Status: {status}{gate}  |  {r.processing_time_s:.1f}s  |  spec={r.spec or 'none'}")
    print(f"{'='*70}")

    if not r.success:
        print(f"  ERROR: {r.error}")
        return

    print(f"  Background:    {r.bg_method} (dark={r.dark_background})")
    print(f"  Input type:    {r.input_type}")
    print(f"  Calibration:   {r.calibration_source} (confidence={r.calibration_confidence:.2f})")
    print(f"  Body dims:     {r.body_h_mm:.1f} x {r.body_w_mm:.1f} mm  (H x W)")

    if r.cognitive_used:
        print(f"  Cognitive:     YES ({r.cognitive_iterations} iterations)")

    if r.expected_h_mm:
        h_err = f"{r.h_error_pct:.1f}%" if r.h_error_pct is not None else "N/A"
        w_err = f"{r.w_error_pct:.1f}%" if r.w_error_pct is not None else "N/A"
        print(f"  Expected:      {r.expected_h_mm:.1f} x {r.expected_w_mm:.1f} mm")
        print(f"  Error:         H={h_err}  W={w_err}")

    print(f"  Features:      {r.total_features} total")
    for ft, count in sorted(r.feature_breakdown.items()):
        print(f"                 {ft}: {count}")

    if r.dxf_path:
        print(f"  DXF:           {r.dxf_path}")
    if r.svg_path:
        print(f"  SVG:           {r.svg_path}")

    if r.warnings and verbose:
        print(f"  Warnings ({len(r.warnings)}):")
        for w in r.warnings[:5]:
            print(f"    - {w}")
        if len(r.warnings) > 5:
            print(f"    ... and {len(r.warnings)-5} more")


def print_summary(results: List[SandboxResult], tolerance_pct: float):
    passed = sum(1 for r in results if r.success)
    accurate = sum(1 for r in results if r.passed_tolerance is True)
    failed = sum(1 for r in results if not r.success)

    print(f"\n{'='*70}")
    print(f"  SANDBOX SUMMARY")
    print(f"{'='*70}")
    print(f"  Images processed: {len(results)}")
    print(f"  Extracted OK:     {passed}/{len(results)}")
    print(f"  Within {tolerance_pct:.0f}% tolerance: {accurate}/{passed}")
    print(f"  Failed:           {failed}")
    print()

    # Table
    print(f"  {'Image':<40} {'HxW mm':<22} {'H err':>7} {'W err':>7} {'Gate':>8}")
    print(f"  {'-'*40} {'-'*22} {'-'*7} {'-'*7} {'-'*8}")
    for r in results:
        if not r.success:
            print(f"  {r.image_name[:40]:<40} {'FAILED':<22}")
            continue
        body = f"{r.body_h_mm:.1f}x{r.body_w_mm:.1f}"
        if r.cognitive_used:
            body += "*"
        h_err = f"{r.h_error_pct:.1f}%" if r.h_error_pct is not None else "  N/A"
        w_err = f"{r.w_error_pct:.1f}%" if r.w_error_pct is not None else "  N/A"
        gate = "PASS" if r.passed_tolerance else ("FAIL" if r.passed_tolerance is False else "  ---")
        print(f"  {r.image_name[:40]:<40} {body:<22} {h_err:>7} {w_err:>7} {gate:>8}")
    print()


# ── Baseline compare/save ──────────────────────────────────────────────────────

BASELINE_FILE = Path(__file__).parent / "sandbox_baseline.json"

def save_baseline(results: List[SandboxResult]):
    data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "results": [asdict(r) for r in results]
    }
    BASELINE_FILE.write_text(json.dumps(data, indent=2))
    print(f"Baseline saved to {BASELINE_FILE}")


def compare_baseline(results: List[SandboxResult]):
    if not BASELINE_FILE.exists():
        print("No baseline found. Run with --save-baseline first.")
        return

    baseline = json.loads(BASELINE_FILE.read_text())
    baseline_map = {r["image_name"]: r for r in baseline["results"]}

    print(f"\nComparison vs baseline ({baseline['timestamp']}):")
    print(f"  {'Image':<35} {'H err':<20} {'W err':<20}")
    print(f"  {'-'*35} {'-'*20} {'-'*20}")

    for r in results:
        b = baseline_map.get(r.image_name)
        if not b:
            print(f"  {r.image_name[:35]:<35} (no baseline)")
            continue

        h_now = f"{r.h_error_pct:.1f}%" if r.h_error_pct is not None else "N/A"
        h_was = f"{b.get('h_error_pct', 'N/A')}"
        w_now = f"{r.w_error_pct:.1f}%" if r.w_error_pct is not None else "N/A"
        w_was = f"{b.get('w_error_pct', 'N/A')}"

        h_delta = ""
        if r.h_error_pct is not None and b.get("h_error_pct") is not None:
            delta = r.h_error_pct - b["h_error_pct"]
            h_delta = f" ({'improved' if delta < -0.5 else 'worse' if delta > 0.5 else 'same'})"

        print(f"  {r.image_name[:35]:<35} {h_was}→{h_now}{h_delta:<12} {w_was}→{w_now}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Photo-Vectorizer v2 Standalone Sandbox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("image", nargs="?", help="Image file or directory (with --batch)")
    parser.add_argument("--spec", default=None,
        help=f"Instrument spec. Available: {', '.join(INSTRUMENT_SPECS.keys())}")
    parser.add_argument("--bg-method", default="auto",
        choices=["auto", "grabcut", "rembg", "threshold"])
    parser.add_argument("--tolerance", type=float, default=30.0,
        help="Accuracy tolerance %% (default 30)")
    parser.add_argument("--output-dir", default="sandbox_output")
    parser.add_argument("--no-dxf", action="store_true")
    parser.add_argument("--no-svg", action="store_true")
    parser.add_argument("--debug", action="store_true",
        help="Save intermediate pipeline images")
    parser.add_argument("--batch", action="store_true",
        help="Run on all .jpg/.png in the image path (treated as directory)")
    parser.add_argument("--compare", action="store_true",
        help="Compare results against saved baseline")
    parser.add_argument("--save-baseline", action="store_true",
        help="Save current results as new baseline")
    parser.add_argument("--list-specs", action="store_true",
        help="List all available instrument specs and exit")
    parser.add_argument("--source-type", default="auto",
        choices=["auto", "ai", "photo"],
        help="Image source: auto=detect, ai=force AI path, photo=force photo path")
    parser.add_argument("--cognitive", action="store_true",
        help="Enable cognitive extraction engine as fallback when standard pipeline fails")

    args = parser.parse_args()

    if args.list_specs:
        print("\nAvailable instrument specs:")
        for name, data in INSTRUMENT_SPECS.items():
            body = data.get("body", ("?", "?"))
            print(f"  {name:<25} {body[0]}mm x {body[1]}mm")
        return

    if not args.image:
        parser.print_help()
        return

    image_path = Path(args.image)
    results = []

    if args.batch or image_path.is_dir():
        # Batch mode — run on all images in directory
        images = sorted(
            list(image_path.glob("*.jpg")) +
            list(image_path.glob("*.jpeg")) +
            list(image_path.glob("*.png"))
        )
        # Skip intermediate pipeline outputs
        images = [i for i in images if not any(
            tag in i.stem for tag in
            ["_02_foreground", "_03_alpha", "_04_edges", "_05_grid"]
        )]
        print(f"\nBatch mode: {len(images)} images in {image_path}")

        for img in images:
            print(f"\n  Processing: {img.name} ...", end="", flush=True)
            r = run_single(
                str(img),
                spec=args.spec,
                bg_method=args.bg_method,
                output_dir=args.output_dir,
                export_dxf=not args.no_dxf,
                export_svg=not args.no_svg,
                debug=args.debug,
                tolerance_pct=args.tolerance,
                source_type=args.source_type,
                use_cognitive=args.cognitive,
            )
            results.append(r)
            status = "OK" if r.success else f"FAIL: {r.error}"
            if r.cognitive_used:
                status += " [cognitive]"
            print(f" {status}")

        for r in results:
            print_result(r, verbose=False)
        print_summary(results, args.tolerance)

    else:
        # Single image mode
        if not image_path.exists():
            print(f"Image not found: {image_path}")
            sys.exit(1)

        r = run_single(
            str(image_path),
            spec=args.spec,
            bg_method=args.bg_method,
            output_dir=args.output_dir,
            export_dxf=not args.no_dxf,
            export_svg=not args.no_svg,
            debug=args.debug,
            tolerance_pct=args.tolerance,
            source_type=args.source_type,
            use_cognitive=args.cognitive,
        )
        results.append(r)
        print_result(r)

    if args.compare:
        compare_baseline(results)

    if args.save_baseline:
        save_baseline(results)


if __name__ == "__main__":
    main()
