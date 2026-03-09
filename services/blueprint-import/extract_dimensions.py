"""
Blueprint Dimension Extractor
=============================

Extracts dimensional information from guitar blueprint PDFs using:
1. OCR text detection for dimension annotations
2. Contour measurement with scale detection
3. Common guitar dimension pattern matching

Author: The Production Shop
Version: 4.0.0
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import json
import re
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Try imports
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


@dataclass
class GuitarDimensions:
    """Extracted guitar dimensions."""
    name: str
    file: str

    # Scale length
    scale_length_inches: Optional[float] = None
    scale_length_mm: Optional[float] = None

    # Body dimensions
    body_length_inches: Optional[float] = None
    body_width_inches: Optional[float] = None
    body_thickness_inches: Optional[float] = None

    # Derived measurements
    upper_bout_width: Optional[float] = None
    lower_bout_width: Optional[float] = None
    waist_width: Optional[float] = None

    # Neck dimensions
    nut_width_inches: Optional[float] = None
    neck_width_at_12th: Optional[float] = None

    # Detection metadata
    dimensions_found: int = 0
    raw_text_matches: List[str] = field(default_factory=list)
    pixel_measurements: Dict[str, float] = field(default_factory=dict)
    confidence: str = "low"
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# Common scale lengths for detection/validation
COMMON_SCALE_LENGTHS = {
    24.75: "Gibson",
    25.0: "PRS",
    25.5: "Fender",
    24.0: "Jaguar/Mustang",
    26.5: "Baritone",
    27.0: "Baritone",
    30.0: "Bass VI",
    34.0: "Bass",
}

# Regex patterns for dimension extraction
DIMENSION_PATTERNS = [
    # Scale length patterns
    (r'(?:scale\s*(?:length)?[:\s]*)?(\d{2}(?:\.\d+)?)\s*["\']?\s*(?:scale)?', 'scale_length'),
    (r'(\d{2}\.\d+)\s*["\']', 'inches'),
    (r'(\d{3,4})\s*mm', 'mm'),

    # Body dimension patterns
    (r'body\s*(?:length)?[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'body_length'),
    (r'(?:body\s*)?width[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'body_width'),
    (r'thickness[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'thickness'),

    # Bout patterns
    (r'(?:upper\s*)?bout[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'upper_bout'),
    (r'lower\s*bout[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'lower_bout'),
    (r'waist[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'waist'),

    # Nut width
    (r'nut\s*(?:width)?[:\s]*(\d+(?:\.\d+)?)\s*["\']?', 'nut_width'),
    (r'(\d+(?:\.\d+)?)\s*(?:mm|")?\s*(?:at\s*)?nut', 'nut_width'),

    # Generic measurements (inches with fraction)
    (r'(\d+)\s*(\d+)/(\d+)\s*["\']', 'fraction_inches'),

    # Decimal inches
    (r'(\d{1,2}\.\d{1,3})\s*["\']', 'decimal_inches'),
]


def pdf_to_image(pdf_path: Path, dpi: int = 200) -> np.ndarray:
    """Convert first page of PDF to OpenCV image at higher DPI for OCR."""
    if not HAS_FITZ:
        raise ImportError("PyMuPDF required")

    doc = fitz.open(str(pdf_path))
    page = doc[0]

    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()
    return img


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text directly from PDF (faster than OCR if text is embedded)."""
    if not HAS_FITZ:
        return ""

    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception:
        return ""


def ocr_image(img: np.ndarray) -> str:
    """Run OCR on image to extract text."""
    if not HAS_TESSERACT:
        return ""

    try:
        # Preprocess for better OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # Threshold
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR
        text = pytesseract.image_to_string(thresh)
        return text
    except Exception as e:
        return f"OCR Error: {e}"


def parse_fraction(whole: str, num: str, denom: str) -> float:
    """Convert fractional inches to decimal."""
    return float(whole) + float(num) / float(denom)


def extract_dimensions_from_text(text: str) -> Dict[str, List[float]]:
    """Extract dimension values from text using regex patterns."""
    results = {
        'scale_length': [],
        'body_length': [],
        'body_width': [],
        'thickness': [],
        'upper_bout': [],
        'lower_bout': [],
        'waist': [],
        'nut_width': [],
        'generic_inches': [],
        'generic_mm': [],
    }

    text_lower = text.lower()

    # Find all measurements
    for pattern, dim_type in DIMENSION_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            try:
                if dim_type == 'fraction_inches':
                    # Handle fractional inches (e.g., "1 3/4")
                    if isinstance(match, tuple) and len(match) == 3:
                        value = parse_fraction(match[0], match[1], match[2])
                        results['generic_inches'].append(value)
                elif dim_type == 'mm':
                    value = float(match)
                    results['generic_mm'].append(value)
                elif dim_type == 'decimal_inches' or dim_type == 'inches':
                    value = float(match) if isinstance(match, str) else float(match[0])
                    results['generic_inches'].append(value)
                else:
                    value = float(match) if isinstance(match, str) else float(match[0])
                    if dim_type in results:
                        results[dim_type].append(value)
            except (ValueError, IndexError):
                continue

    return results


def measure_contour_dimensions(img: np.ndarray) -> Dict[str, float]:
    """Measure the largest contour in pixels."""
    height, width = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return {}

    # Get largest contour
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    # Measure at different points for bout widths
    # Convert to Python native types for JSON serialization
    measurements = {
        'bbox_width_px': int(w),
        'bbox_height_px': int(h),
        'bbox_area_px': int(w * h),
        'contour_area_px': float(cv2.contourArea(largest)),
        'aspect_ratio': float(w / h) if h > 0 else 0.0,
        'image_width_px': int(width),
        'image_height_px': int(height),
        'body_width_ratio': float(w / width),
        'body_height_ratio': float(h / height),
    }

    # Try to measure upper/lower bout widths
    # Upper bout: measure width at 25% from top
    # Lower bout: measure width at 75% from top
    # Waist: measure width at 50%

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(mask, [largest], -1, 255, -1)

    y_positions = {
        'upper_bout_y': int(y + h * 0.25),
        'waist_y': int(y + h * 0.50),
        'lower_bout_y': int(y + h * 0.75),
    }

    for name, y_pos in y_positions.items():
        if 0 <= y_pos < height:
            row = mask[y_pos, :]
            nonzero = np.where(row > 0)[0]
            if len(nonzero) > 0:
                width_at_y = int(nonzero[-1] - nonzero[0])
                measurements[name.replace('_y', '_width_px')] = width_at_y

    return measurements


def infer_scale_from_measurements(measurements: Dict[str, float], text_dims: Dict) -> Optional[float]:
    """Try to infer scale length from pixel measurements and known ratios."""
    # Valid scale length range: 22" (short scale) to 36" (extended range)
    MIN_SCALE = 22.0
    MAX_SCALE = 36.0

    # Filter all candidates to valid range
    scale_candidates = [
        v for v in text_dims.get('scale_length', [])
        if MIN_SCALE <= v <= MAX_SCALE
    ] + [
        v for v in text_dims.get('generic_inches', [])
        if MIN_SCALE <= v <= MAX_SCALE
    ]

    if scale_candidates:
        # Prefer common scale lengths
        for sl in COMMON_SCALE_LENGTHS:
            for candidate in scale_candidates:
                if abs(candidate - sl) < 0.5:
                    return sl
        # Return first valid candidate
        return scale_candidates[0]

    return None


def extract_blueprint_dimensions(pdf_path: Path, name: str) -> GuitarDimensions:
    """Extract all dimensions from a blueprint PDF."""
    dims = GuitarDimensions(name=name, file=pdf_path.name)

    try:
        # Method 1: Extract embedded text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)

        # Method 2: OCR the rendered image
        img = pdf_to_image(pdf_path, dpi=200)
        ocr_text = ""
        if HAS_TESSERACT:
            ocr_text = ocr_image(img)

        # Combine text sources
        all_text = pdf_text + "\n" + ocr_text

        # Extract dimensions from text
        text_dims = extract_dimensions_from_text(all_text)

        # Store raw matches
        for dim_type, values in text_dims.items():
            for v in values:
                dims.raw_text_matches.append(f"{dim_type}: {v}")

        dims.dimensions_found = sum(len(v) for v in text_dims.values())

        # Assign specific dimensions (with validation)
        # Scale length: 22-36" for guitars (22" short scale to 36" bass)
        valid_scales = [s for s in text_dims['scale_length'] if 22 <= s <= 36]
        if valid_scales:
            dims.scale_length_inches = valid_scales[0]
            dims.scale_length_mm = dims.scale_length_inches * 25.4

        # Body length: 12-22" for electric guitars
        valid_body_lengths = [b for b in text_dims['body_length'] if 12 <= b <= 22]
        if valid_body_lengths:
            dims.body_length_inches = valid_body_lengths[0]

        # Body width: 10-18" for electric guitars
        valid_body_widths = [w for w in text_dims['body_width'] if 10 <= w <= 18]
        if valid_body_widths:
            dims.body_width_inches = valid_body_widths[0]

        if text_dims['thickness']:
            dims.body_thickness_inches = text_dims['thickness'][0]

        if text_dims['upper_bout']:
            dims.upper_bout_width = text_dims['upper_bout'][0]

        if text_dims['lower_bout']:
            dims.lower_bout_width = text_dims['lower_bout'][0]

        if text_dims['waist']:
            dims.waist_width = text_dims['waist'][0]

        if text_dims['nut_width']:
            dims.nut_width_inches = text_dims['nut_width'][0]

        # Try to infer scale length if not found
        if not dims.scale_length_inches:
            inferred = infer_scale_from_measurements({}, text_dims)
            if inferred:
                dims.scale_length_inches = inferred
                dims.scale_length_mm = inferred * 25.4
                dims.notes.append(f"Scale length inferred: {inferred}\"")

        # Measure contours for pixel-based dimensions
        pixel_dims = measure_contour_dimensions(img)
        dims.pixel_measurements = pixel_dims

        # Confidence assessment
        if dims.dimensions_found >= 5:
            dims.confidence = "high"
        elif dims.dimensions_found >= 2:
            dims.confidence = "medium"
        else:
            dims.confidence = "low"

        # Add scale length validation note
        if dims.scale_length_inches:
            for sl, brand in COMMON_SCALE_LENGTHS.items():
                if abs(dims.scale_length_inches - sl) < 0.25:
                    dims.notes.append(f"Scale matches {brand} ({sl}\")")
                    break

    except Exception as e:
        dims.notes.append(f"Error: {str(e)}")
        dims.confidence = "error"

    return dims


# Blueprint collection
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


def main():
    """Extract dimensions from all blueprints."""
    print("=" * 90)
    print("GUITAR BLUEPRINT DIMENSION EXTRACTION")
    print("=" * 90)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PDF Directory: {PDF_DIR}")
    print(f"OCR Available: {HAS_TESSERACT}")
    print(f"Total Blueprints: {len(BLUEPRINTS)}")
    print()

    if not HAS_FITZ:
        print("ERROR: PyMuPDF required. Install with: pip install PyMuPDF")
        return

    results = []

    print("-" * 90)
    print(f"{'#':>2} {'Blueprint':<26} | {'Scale':<8} | {'Body L':<7} | {'Body W':<7} | {'Dims':<4} | {'Conf':<6}")
    print("-" * 90)

    for i, (filename, name) in enumerate(BLUEPRINTS, 1):
        pdf_path = PDF_DIR / filename

        if not pdf_path.exists():
            print(f"{i:2}. {name[:26]:<26} | FILE NOT FOUND")
            continue

        dims = extract_blueprint_dimensions(pdf_path, name)
        results.append(dims)

        scale = f"{dims.scale_length_inches:.2f}\"" if dims.scale_length_inches else "---"
        body_l = f"{dims.body_length_inches:.1f}\"" if dims.body_length_inches else "---"
        body_w = f"{dims.body_width_inches:.1f}\"" if dims.body_width_inches else "---"

        print(f"{i:2}. {name[:26]:<26} | {scale:<8} | {body_l:<7} | {body_w:<7} | {dims.dimensions_found:<4} | {dims.confidence:<6}")

    # Summary
    print("-" * 90)
    print("\nSUMMARY")
    print("-" * 40)

    with_scale = [r for r in results if r.scale_length_inches]
    with_body = [r for r in results if r.body_length_inches or r.body_width_inches]
    high_conf = [r for r in results if r.confidence == "high"]

    print(f"Total processed:        {len(results)}")
    print(f"With scale length:      {len(with_scale)}")
    print(f"With body dimensions:   {len(with_body)}")
    print(f"High confidence:        {len(high_conf)}")

    # Scale length distribution
    if with_scale:
        print("\nScale Lengths Found:")
        scale_counts = {}
        for r in with_scale:
            sl = r.scale_length_inches
            # Round to nearest common scale
            for common_sl in COMMON_SCALE_LENGTHS:
                if abs(sl - common_sl) < 0.5:
                    sl = common_sl
                    break
            scale_counts[sl] = scale_counts.get(sl, 0) + 1

        for sl, count in sorted(scale_counts.items()):
            brand = COMMON_SCALE_LENGTHS.get(sl, "Custom")
            print(f"  {sl:.2f}\" ({brand}): {count}")

    # Pixel measurements summary
    print("\nPixel Measurement Ranges:")
    widths = [r.pixel_measurements.get('bbox_width_px', 0) for r in results if r.pixel_measurements]
    heights = [r.pixel_measurements.get('bbox_height_px', 0) for r in results if r.pixel_measurements]

    if widths:
        print(f"  Body width (px):  {min(widths):.0f} - {max(widths):.0f}")
    if heights:
        print(f"  Body height (px): {min(heights):.0f} - {max(heights):.0f}")

    # Save results
    output_path = Path(__file__).parent / "blueprint_dimensions.json"
    with open(output_path, "w") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total": len(results),
            "with_scale_length": len(with_scale),
            "results": [r.to_dict() for r in results]
        }, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("=" * 90)

    # Detailed output for blueprints with dimensions
    if with_scale or with_body:
        print("\nDETAILED DIMENSIONS")
        print("=" * 90)

        for r in results:
            if r.scale_length_inches or r.body_length_inches or r.dimensions_found > 2:
                print(f"\n{r.name}")
                print("-" * 40)
                if r.scale_length_inches:
                    print(f"  Scale Length: {r.scale_length_inches:.2f}\" ({r.scale_length_mm:.1f}mm)")
                if r.body_length_inches:
                    print(f"  Body Length:  {r.body_length_inches:.1f}\"")
                if r.body_width_inches:
                    print(f"  Body Width:   {r.body_width_inches:.1f}\"")
                if r.upper_bout_width:
                    print(f"  Upper Bout:   {r.upper_bout_width:.1f}\"")
                if r.lower_bout_width:
                    print(f"  Lower Bout:   {r.lower_bout_width:.1f}\"")
                if r.nut_width_inches:
                    print(f"  Nut Width:    {r.nut_width_inches:.3f}\"")
                if r.notes:
                    for note in r.notes:
                        print(f"  Note: {note}")


if __name__ == "__main__":
    main()
