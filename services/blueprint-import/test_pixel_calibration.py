"""
Test Pixel Calibration on Blueprint Collection
===============================================

Tests the CalibratedDimensionExtractor on all guitar blueprints.

Author: Luthier's Toolbox
"""

import sys
import json
from pathlib import Path

# Add calibration module to path
sys.path.insert(0, str(Path(__file__).parent))

import fitz  # PyMuPDF
import cv2
import numpy as np

from calibration import (
    CalibratedDimensionExtractor,
    PixelCalibrator,
    ScaleReferenceDetector,
)

# Blueprint collection - (filename, display_name, known_scale_length)
BLUEPRINTS = [
    # Electric - Classic Fender
    ("Charvel - 5150.pdf", "Charvel 5150", 25.5),
    ("Fender-Stratocaster-62.pdf", "Fender Stratocaster 62", 25.5),
    ("Fender-Telecaster.pdf", "Fender Telecaster", 25.5),
    ("Fender-Jazzmaster-Body.pdf", "Fender Jazzmaster", 25.5),
    ("Fender-Mustang-Body-V1.pdf", "Fender Mustang", 24.0),

    # Electric - Gibson Style
    ("Gibson-Les-Paul-59-Complete.pdf", "Gibson Les Paul 59", 24.75),
    ("00-Gibson-1963-SG-JR.pdf", "Gibson SG JR 63", 24.75),
    ("Gibson-335-Dot-Complete.pdf", "Gibson 335", 24.75),
    ("Gibson-Explorer-01.pdf", "Gibson Explorer", 24.75),
    ("Gibson58FlyingV.pdf", "Gibson Flying V 58", 24.75),
    ("Gibson-Melody-Maker.pdf", "Gibson Melody Maker", 24.75),

    # Electric - Gretsch
    ("Gretsch - Astro Jet.pdf", "Gretsch Astro Jet", 24.6),
    ("Gretsch - Billy Bo Jupiter Thunderbird.pdf", "Gretsch Billy Bo", 24.75),
    ("Gretsch - Duo Jet.pdf", "Gretsch Duo Jet", 24.6),

    # Electric - Other brands
    ("Danelectro-DC-59.pdf", "Danelectro DC 59", 25.0),
    ("Dano-Double-Cut.pdf", "Danelectro Double Cut", 25.0),
    ("1957-Harmony-H44-Stratotone.pdf", "Harmony H44 Stratotone", 24.0),
    ("Epiphone-Coronet-66.pdf", "Epiphone Coronet 66", 24.75),
    ("DBZ-Bird-Of-Prey.pdf", "DBZ Bird of Prey", 25.5),
    ("Washburn-N4.pdf", "Washburn N4", 25.5),
    ("MosriteVenturesIIGuitarBody-1.pdf", "Mosrite Ventures II", 24.75),
    ("Squier-Hypersonic-Supersonic.pdf", "Squier Hypersonic", 25.5),
    ("Rick-Turner-Model-1.pdf", "Rick Turner Model 1", 24.75),

    # Electric - Modern/Extended Range
    ("Blackmachine-B6.pdf", "Blackmachine B6", 25.5),
    ("Blackmachine-B7-26.5in-Scale-Template.pdf", "Blackmachine B7", 26.5),
    ("Strandberg-boden-6-NX-2022-Full-Rockar.pdf", "Strandberg Boden 6", 25.5),
    ("Music-Man-John-Petrucci-6.pdf", "Music Man Petrucci", 25.5),

    # Electric - Unique
    ("RedSpecial.pdf", "Brian May Red Special", 24.0),
    ("Klein-Guitar-Plan.pdf", "Klein Guitar", 25.5),
    ("MSK-Guitars--MK1HH24.pdf", "MSK MK1HH24", 24.0),
    ("First Act - Rick Nielsens Bettie.pdf", "First Act Rick Nielsen", 25.5),
    ("Zambon-Template.pdf", "Zambon Template", None),
    ("Gretsch-Electromatic-Lap-Steel.pdf", "Gretsch Lap Steel", 22.5),
]


def pdf_to_image(pdf_path: Path, dpi: int = 150) -> np.ndarray:
    """Convert first page of PDF to OpenCV image."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Render at specified DPI
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

    # Convert RGB to BGR for OpenCV
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:  # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()
    return img


def test_calibration_on_blueprints():
    """Test pixel calibration on all blueprints."""
    blueprint_dir = Path(r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans")

    extractor = CalibratedDimensionExtractor()
    results = []

    print("=" * 70)
    print("PIXEL CALIBRATION TEST - Guitar Blueprint Collection")
    print("=" * 70)
    print()

    for filename, name, known_scale in BLUEPRINTS:
        pdf_path = blueprint_dir / filename

        if not pdf_path.exists():
            print(f"[SKIP] {name}: File not found")
            continue

        print(f"Processing: {name}...")

        try:
            # Convert PDF to image
            img = pdf_to_image(pdf_path)

            # Extract dimensions with calibration
            # Use paper_size method for consistent results across different PDFs
            # The body_heuristic method doesn't work well with varying PDF resolutions
            dims = extractor.extract(
                img,
                name=name,
                source_file=filename,
                known_scale_length=known_scale,
                paper_size="letter",  # Assume most blueprints are letter-size
                calibration_method="paper"  # Paper size gives most consistent calibration
            )

            # Build result
            result = {
                "name": name,
                "filename": filename,
                "known_scale": known_scale,
                "extracted": dims.to_dict(),
                "success": dims.body_length_inches is not None,
            }
            results.append(result)

            # Print summary
            if dims.body_length_inches:
                px_w = dims.pixel_measurements.get('body_width_px', 0)
                px_h = dims.pixel_measurements.get('body_height_px', 0)
                print(f"  [OK] Body: {dims.body_length_inches:.2f}\" x {dims.body_width_inches:.2f}\" ({px_h:.0f}x{px_w:.0f}px)")
                if dims.upper_bout_width_inches:
                    print(f"       Upper Bout: {dims.upper_bout_width_inches:.2f}\"")
                if dims.lower_bout_width_inches:
                    print(f"       Lower Bout: {dims.lower_bout_width_inches:.2f}\"")
                if dims.waist_width_inches:
                    print(f"       Waist: {dims.waist_width_inches:.2f}\"")
                print(f"       Calibration: {dims.calibration_method} (PPI: {dims.ppi:.0f}, conf: {dims.calibration_confidence:.0%})")
            else:
                print(f"  [!!] Could not extract body dimensions")
                if dims.warnings:
                    for w in dims.warnings:
                        print(f"       Warning: {w}")

        except Exception as e:
            print(f"  [ERR] {e}")
            results.append({
                "name": name,
                "filename": filename,
                "error": str(e),
                "success": False,
            })

        print()

    # Summary statistics
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"Total blueprints: {len(results)}")
    print(f"Successful extractions: {len(successful)} ({len(successful)/len(results)*100:.0f}%)")
    print(f"Failed extractions: {len(failed)}")
    print()

    # Dimension statistics
    if successful:
        body_lengths = [r["extracted"]["body"]["length_inches"] for r in successful if r["extracted"]["body"]["length_inches"]]
        body_widths = [r["extracted"]["body"]["width_inches"] for r in successful if r["extracted"]["body"]["width_inches"]]

        if body_lengths:
            print(f"Body Length Range: {min(body_lengths):.2f}\" - {max(body_lengths):.2f}\"")
            print(f"Body Length Mean: {sum(body_lengths)/len(body_lengths):.2f}\"")

        if body_widths:
            print(f"Body Width Range: {min(body_widths):.2f}\" - {max(body_widths):.2f}\"")
            print(f"Body Width Mean: {sum(body_widths)/len(body_widths):.2f}\"")

    # Save results
    output_path = Path(__file__).parent / "pixel_calibration_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Generate report
    generate_report(results)

    return results


def classify_result(result: dict) -> str:
    """Classify result quality based on pixel measurements and dimensions."""
    if not result.get("success"):
        return "FAILED"

    dims = result.get("extracted", {})
    px = dims.get("pixel_measurements", {})
    body_len = dims.get("body", {}).get("length_inches")
    body_wid = dims.get("body", {}).get("width_inches")
    px_w = px.get("body_width_px", 0)
    px_h = px.get("body_height_px", 0)

    # Check pixel dimensions - if too small, detection probably failed
    if max(px_w, px_h) < 200:
        return "SMALL_CONTOUR"  # Found a tiny element, not the body

    # Check if dimensions are in reasonable range for guitar bodies
    if body_len and body_wid:
        # Electric guitar bodies are typically 14-22" long, 10-16" wide
        if 12 <= body_len <= 24 and 8 <= body_wid <= 18:
            return "GOOD"
        elif body_len > 24 or body_wid > 18:
            return "OVERSIZED"  # PPI too low
        else:
            return "UNDERSIZED"  # PPI too high

    return "UNKNOWN"


def generate_report(results: list):
    """Generate markdown report of calibration results."""
    report_path = Path(__file__).parent / "CALIBRATION_REPORT.md"

    # Classify results
    for r in results:
        r["quality"] = classify_result(r)

    good = [r for r in results if r["quality"] == "GOOD"]
    small = [r for r in results if r["quality"] == "SMALL_CONTOUR"]
    oversized = [r for r in results if r["quality"] == "OVERSIZED"]
    undersized = [r for r in results if r["quality"] == "UNDERSIZED"]
    failed = [r for r in results if r["quality"] == "FAILED"]

    lines = [
        "# Pixel Calibration Results Report",
        "",
        f"**Date:** 2026-03-06",
        f"**Method:** Pixel-to-inch calibration with contour analysis",
        f"**Total Blueprints:** {len(results)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]

    successful = [r for r in results if r.get("success")]

    lines.extend([
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Processed | {len(results)} |",
        f"| Good (reasonable dims) | {len(good)} |",
        f"| Small contour (detection issue) | {len(small)} |",
        f"| Oversized (PPI too low) | {len(oversized)} |",
        f"| Undersized (PPI too high) | {len(undersized)} |",
        f"| Failed | {len(failed)} |",
        "",
        "**Note:** Most calibration issues are due to unknown paper size or multi-view PDF layouts.",
        "",
        "---",
        "",
        "## Results by Quality",
        "",
        "### Good Detections (Reasonable Dimensions)",
        "",
        "| Blueprint | Body (in) | Pixels | PPI | Confidence |",
        "|-----------|-----------|--------|-----|------------|",
    ])

    for r in good:
        dims = r["extracted"]
        px = dims["pixel_measurements"]
        px_size = f"{px.get('body_height_px', 0):.0f}x{px.get('body_width_px', 0):.0f}"
        body = f"{dims['body']['length_inches']:.1f}x{dims['body']['width_inches']:.1f}"
        ppi = dims['calibration']['ppi']
        conf = dims['calibration']['confidence']
        lines.append(f"| {r['name']} | {body} | {px_size} | {ppi:.0f} | {conf:.0%} |")

    if not good:
        lines.append("| *No good detections* | - | - | - | - |")

    lines.extend([
        "",
        "### Small Contour Detections (Wrong element found)",
        "",
        "These blueprints have very small pixel measurements, indicating the detector",
        "found a small element (legend, logo, thumbnail) instead of the guitar body.",
        "",
    ])

    for r in small:
        dims = r["extracted"]
        px = dims["pixel_measurements"]
        px_size = f"{px.get('body_height_px', 0):.0f}x{px.get('body_width_px', 0):.0f}px"
        lines.append(f"- **{r['name']}**: {px_size} detected")

    if not small:
        lines.append("*None*")

    lines.extend([
        "",
        "### Undersized/Oversized Results",
        "",
        "These blueprints have reasonable pixel measurements but incorrect PPI estimation.",
        "",
    ])

    for r in undersized + oversized:
        dims = r["extracted"]
        px = dims["pixel_measurements"]
        px_size = f"{px.get('body_height_px', 0):.0f}x{px.get('body_width_px', 0):.0f}px"
        body = f"{dims['body']['length_inches']:.1f}x{dims['body']['width_inches']:.1f}\""
        ppi = dims['calibration']['ppi']
        lines.append(f"- **{r['name']}**: {px_size} -> {body} (PPI: {ppi:.0f})")

    lines.extend([
        "",
        "---",
        "",
        "## All Extracted Dimensions",
        "",
        "| Blueprint | Body Length | Body Width | Pixels | PPI | Quality |",
        "|-----------|-------------|------------|--------|-----|---------|",
    ])

    for r in results:
        if not r.get("success"):
            continue
        dims = r["extracted"]
        px = dims["pixel_measurements"]
        body_len = f"{dims['body']['length_inches']:.2f}\"" if dims['body']['length_inches'] else "-"
        body_wid = f"{dims['body']['width_inches']:.2f}\"" if dims['body']['width_inches'] else "-"
        px_size = f"{px.get('body_height_px', 0):.0f}x{px.get('body_width_px', 0):.0f}"
        ppi = f"{dims['calibration']['ppi']:.0f}"
        quality = r.get("quality", "?")

        lines.append(f"| {r['name']} | {body_len} | {body_wid} | {px_size} | {ppi} | {quality} |")

    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "For accurate dimension extraction from blueprints:",
        "",
        "1. **Best approach**: Use a known scale length or ruler marking for calibration",
        "2. **For PDFs with dimensions**: Extract text annotations (requires OCR for scanned blueprints)",
        "3. **For multi-view PDFs**: Manually select the body view for measurement",
        "",
        "### Blueprints Needing Manual Calibration",
        "",
    ])

    needs_manual = [r for r in results if r.get("quality") in ["SMALL_CONTOUR", "UNDERSIZED", "OVERSIZED"]]
    if needs_manual:
        for r in needs_manual:
            known_scale = r.get("known_scale")
            scale_str = f" (scale: {known_scale}\")" if known_scale else ""
            lines.append(f"- {r['name']}{scale_str}")
    else:
        lines.append("*All blueprints have reasonable dimensions*")

    lines.extend([
        "",
        "---",
        "",
        "*Generated by Luthier's Toolbox Pixel Calibration System v4.0.0*",
    ])

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    test_calibration_on_blueprints()
