"""
Batch Blueprint Classification Test
====================================

Tests the GridZoneClassifier on a diverse collection of electric guitar blueprints.

Author: The Production Shop
Version: 4.0.0
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from classifiers.grid_zone import (
    GridZoneClassifier,
    ELECTRIC_GUITAR_GRID
)

# Try to import PyMuPDF for PDF processing
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    print("WARNING: PyMuPDF not installed. Install with: pip install PyMuPDF")


# Blueprint collection to test
BLUEPRINTS = [
    ("Charvel - 5150.pdf", "Charvel 5150"),
    ("Gretsch - Astro Jet.pdf", "Gretsch Astro Jet"),
    ("Gretsch - Billy Bo Jupiter Thunderbird.pdf", "Gretsch Billy Bo"),
    ("Gretsch - Duo Jet.pdf", "Gretsch Duo Jet"),
    ("Gretsch - Duo Jet pt 2.pdf", "Gretsch Duo Jet pt 2"),
    ("Epiphone-Coronet-66.pdf", "Epiphone Coronet 66"),
    ("Danelectro - Double Cutaway 59.pdf", "Danelectro DC 59"),
    ("Danelectro-DC-59.pdf", "Danelectro DC 59 v2"),
    ("Dano-Double-Cut.pdf", "Danelectro Double Cut"),
    ("1957-Harmony-H44-Stratotone.pdf", "Harmony H44 Stratotone"),
    ("Blackmachine-B6.pdf", "Blackmachine B6"),
    ("Blackmachine-B7-26.5in-Scale-Template.pdf", "Blackmachine B7"),
    ("Blackmachine-B7-Complete-Alternate-Headstock.pdf", "Blackmachine B7 Alt"),
    ("Blackmachine-B7-Headstock-Detail.pdf", "Blackmachine B7 Headstock"),
    ("Strandberg-boden-6-NX-2022-Full-Rockar.pdf", "Strandberg Boden 6"),
    ("DBZ-Bird-Of-Prey.pdf", "DBZ Bird of Prey"),
    ("Washburn-N4.pdf", "Washburn N4"),
    ("Washburn-N4-Neck-Detail.pdf", "Washburn N4 Neck"),
    ("RedSpecial.pdf", "Brian May Red Special"),
    ("Klein-Guitar-Plan.pdf", "Klein Guitar"),
    ("Klein-Guitar-Template.pdf", "Klein Template"),
    ("Rick-Turner-Model-1.pdf", "Rick Turner Model 1"),
    ("MosriteVenturesIIGuitarBody-1.pdf", "Mosrite Ventures II"),
    ("MSK-Guitars--MK1HH24.pdf", "MSK MK1HH24"),
    ("Squier-Hypersonic-Supersonic.pdf", "Squier Hypersonic"),
    ("First Act - Rick Nielsens Bettie.pdf", "First Act Rick Nielsen"),
    ("Zambon-Template.pdf", "Zambon"),
    ("Gretsch-Electromatic-Lap-Steel.pdf", "Gretsch Lap Steel"),
]

PDF_DIR = Path(r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans")


def pdf_to_image(pdf_path: Path, dpi: int = 150) -> np.ndarray:
    """Convert first page of PDF to OpenCV image."""
    if not HAS_FITZ:
        raise ImportError("PyMuPDF required for PDF processing")

    doc = fitz.open(str(pdf_path))
    page = doc[0]

    # Render at specified DPI
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    # Convert RGB to BGR for OpenCV
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:  # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()
    return img


def extract_body_contour(img: np.ndarray):
    """Extract the main guitar body contour from a blueprint image."""
    height, width = img.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply threshold to find dark lines on light background
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Morphological operations to clean up
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        # Try edge detection as fallback
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort by area, get largest contours
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    return contours, width, height


def classify_blueprint(pdf_path: Path, name: str, classifier: GridZoneClassifier) -> dict:
    """Classify a single blueprint and return results."""
    result = {
        "name": name,
        "file": pdf_path.name,
        "status": "error",
        "primary_category": None,
        "symmetry_score": None,
        "wing_extend_left": None,
        "wing_extend_right": None,
        "is_confident": None,
        "zone_count": None,
        "contour_count": None,
        "notes": []
    }

    try:
        # Convert PDF to image
        img = pdf_to_image(pdf_path)

        # Extract contours
        contours, width, height = extract_body_contour(img)

        if not contours:
            result["status"] = "no_contours"
            result["notes"].append("No contours detected")
            return result

        result["contour_count"] = len(contours)

        # Find the largest contour that looks like a guitar body
        # Filter by area (should be significant portion of image)
        min_area = (width * height) * 0.05  # At least 5% of image
        body_candidates = [c for c in contours if cv2.contourArea(c) > min_area]

        if not body_candidates:
            # Use largest contour anyway
            body_candidates = contours[:1]

        # Classify the best candidate
        best_contour = body_candidates[0]
        x, y, w, h = cv2.boundingRect(best_contour)

        # Normalize to 0-1 range
        x_min = x / width
        y_min = y / height
        x_max = (x + w) / width
        y_max = (y + h) / height

        classification = classifier.classify_bbox(x_min, y_min, x_max, y_max)

        result["status"] = "success"
        result["primary_category"] = classification.primary_category
        result["symmetry_score"] = round(classification.symmetry_score, 3)
        result["wing_extend_left"] = round(classification.wing_extend_left, 3)
        result["wing_extend_right"] = round(classification.wing_extend_right, 3)
        result["is_confident"] = classification.is_confident
        result["zone_count"] = len(classification.all_zones)
        result["notes"] = classification.notes

        # Add ML features summary
        result["ml_features"] = {
            "center_x": round(classification.ml_features.get("center_x_norm", 0), 3),
            "center_y": round(classification.ml_features.get("center_y_norm", 0), 3),
            "aspect_ratio": round(classification.ml_features.get("aspect_ratio", 0), 3),
            "area_norm": round(classification.ml_features.get("area_norm", 0), 3),
        }

    except Exception as e:
        result["status"] = "error"
        result["notes"].append(str(e))

    return result


def print_result_row(result: dict, index: int):
    """Print a single result row."""
    status_icon = {
        "success": "[OK]",
        "no_contours": "[--]",
        "error": "[!!]"
    }.get(result["status"], "[??]")

    sym = f"{result['symmetry_score']:.2f}" if result["symmetry_score"] else "N/A"
    cat = result["primary_category"] or "N/A"
    conf = "Y" if result["is_confident"] else "N" if result["is_confident"] is not None else "-"

    print(f"{index:2}. {status_icon} {result['name'][:24]:<24} | {cat:<15} | Sym: {sym:<5} | Conf: {conf}")


def main():
    """Run batch classification on all blueprints."""
    print("=" * 80)
    print("BATCH BLUEPRINT CLASSIFICATION TEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Blueprint directory: {PDF_DIR}")
    print(f"Total blueprints: {len(BLUEPRINTS)}")
    print()

    if not HAS_FITZ:
        print("ERROR: PyMuPDF not installed. Cannot process PDFs.")
        print("Install with: pip install PyMuPDF")
        return

    classifier = GridZoneClassifier()
    results = []

    print("-" * 80)
    print(f"{'#':>2}  {'Status':<1} {'Blueprint':<28} | {'Category':<15} | {'Symmetry':<6} | {'Conf'}")
    print("-" * 80)

    for i, (filename, name) in enumerate(BLUEPRINTS, 1):
        pdf_path = PDF_DIR / filename

        if not pdf_path.exists():
            result = {
                "name": name,
                "file": filename,
                "status": "not_found",
                "notes": ["File not found"]
            }
            print(f"{i:2}. ? {name[:28]:<28} | FILE NOT FOUND")
        else:
            result = classify_blueprint(pdf_path, name, classifier)
            print_result_row(result, i)

        results.append(result)

    # Summary statistics
    print("-" * 80)
    print("\nSUMMARY STATISTICS")
    print("-" * 40)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] in ("error", "no_contours")]
    not_found = [r for r in results if r["status"] == "not_found"]

    print(f"Total processed:    {len(results)}")
    print(f"Successful:         {len(successful)} ({len(successful)/len(results)*100:.0f}%)")
    print(f"Failed:             {len(failed)}")
    print(f"Not found:          {len(not_found)}")

    if successful:
        avg_symmetry = sum(r["symmetry_score"] for r in successful) / len(successful)
        confident_count = sum(1 for r in successful if r["is_confident"])

        print(f"\nClassification Results:")
        print(f"  Average symmetry:    {avg_symmetry:.3f}")
        print(f"  Confident matches:   {confident_count}/{len(successful)} ({confident_count/len(successful)*100:.0f}%)")

        # Category breakdown
        categories = {}
        for r in successful:
            cat = r["primary_category"]
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n  Categories detected:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {count}")

    # Body shape analysis
    print("\n" + "=" * 80)
    print("BODY SHAPE ANALYSIS (by symmetry)")
    print("-" * 80)

    if successful:
        # Sort by symmetry
        sorted_results = sorted(successful, key=lambda x: x["symmetry_score"], reverse=True)

        print("\nMost Symmetric (traditional double-cutaway shapes):")
        for r in sorted_results[:5]:
            print(f"  {r['symmetry_score']:.3f} - {r['name']}")

        print("\nLeast Symmetric (offset/asymmetric shapes):")
        for r in sorted_results[-5:]:
            print(f"  {r['symmetry_score']:.3f} - {r['name']}")

        # Wing analysis
        print("\n" + "-" * 40)
        print("WING EXTENSION ANALYSIS")
        print("-" * 40)

        left_heavy = [r for r in successful if r["wing_extend_left"] > r["wing_extend_right"] + 0.05]
        right_heavy = [r for r in successful if r["wing_extend_right"] > r["wing_extend_left"] + 0.05]
        balanced = [r for r in successful if abs(r["wing_extend_left"] - r["wing_extend_right"]) <= 0.05]

        print(f"Left-heavy bodies:  {len(left_heavy)}")
        print(f"Right-heavy bodies: {len(right_heavy)}")
        print(f"Balanced bodies:    {len(balanced)}")

    # Save results to JSON
    output_path = Path(__file__).parent / "batch_classification_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total": len(results),
            "successful": len(successful),
            "results": results
        }, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
