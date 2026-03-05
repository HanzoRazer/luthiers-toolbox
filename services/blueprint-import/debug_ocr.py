#!/usr/bin/env python3
"""Debug OCR output to see what texts are being detected."""
import sys
from pathlib import Path
import cv2
import re

# PDF rendering
try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install PyMuPDF")
    sys.exit(1)

try:
    import easyocr
except ImportError:
    print("ERROR: EasyOCR required. Install with: pip install easyocr")
    sys.exit(1)


def pdf_to_image(pdf_path: str, dpi: int = 300):
    """Convert first page of PDF to image."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    import numpy as np
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 1:  # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    doc.close()
    return img


def analyze_text(text: str) -> dict:
    """Analyze why a text might be filtered."""
    info = {
        'text': text,
        'is_dimension': False,
        'filter_reason': None,
        'parsed_value': None,
        'contextual_dims': []
    }

    text_clean = text.strip().lower()

    # Check if it's a year
    if re.match(r'^\d{4}$', text_clean):
        try:
            year = int(text_clean)
            if 1800 <= year <= 2100:
                info['filter_reason'] = f'year ({year})'
                return info
        except:
            pass

    # Check if it's a single digit
    if re.match(r'^\d$', text_clean):
        info['filter_reason'] = 'single digit'
        return info

    # Check if it's a serial number (5+ digits)
    if re.match(r'^\d{5,}$', text_clean):
        info['filter_reason'] = 'serial number (5+ digits)'
        return info

    # Try dimension patterns
    patterns = [
        (r'(\d+)\s*[-\s]\s*(\d+)/(\d+)\s*(["\']|mm|cm|in)?', 'fraction_mixed'),
        (r'^(\d+)/(\d+)\s*(["\']|mm|cm|in)?$', 'fraction'),
        (r'^(\d+\.?\d*)\s*(mm|cm|in|inch|inches|"|\')?\s*$', 'decimal'),
    ]

    for pattern, ptype in patterns:
        match = re.match(pattern, text_clean)
        if match:
            info['is_dimension'] = True
            info['pattern_matched'] = ptype

            # Parse value
            if ptype == 'fraction_mixed':
                whole = int(match.group(1))
                num = int(match.group(2))
                denom = int(match.group(3))
                value = whole + (num / denom)
                unit = match.group(4) or 'unknown'
            elif ptype == 'fraction':
                num = int(match.group(1))
                denom = int(match.group(2))
                value = num / denom
                unit = match.group(3) or 'unknown'
            else:  # decimal
                value = float(match.group(1))
                unit = match.group(2) or 'unknown'

            info['parsed_value'] = value
            info['unit'] = unit
            return info

    # Try contextual/labeled patterns
    label_patterns = [
        (r'(?:scale\s*length|body\s*length|width|girth|waist|depth|thickness|radius|diameter|height|length|nut|bridge|fret|bout)\s*[:\s]+(\d+\.?\d*)', 'labeled'),
        (r'(?:scale\s*length|body\s*length|width|girth|waist|depth|thickness|radius|diameter|height|length)\s+is\s+(\d+\.?\d*)', 'labeled_is'),
        (r'(?:nut\s+to\s+bridge|scale)\s*[:\s]+(\d+\.?\d*)', 'labeled_scale'),
        (r'(\d+)/(\d+)\s*(["\'])', 'inline_fraction'),
    ]

    for pattern, ptype in label_patterns:
        match = re.search(pattern, text_clean)
        if match:
            info['is_dimension'] = True
            info['pattern_matched'] = f'contextual:{ptype}'

            if ptype == 'inline_fraction':
                num = int(match.group(1))
                denom = int(match.group(2))
                value = num / denom
            else:
                value = float(match.group(1))

            info['parsed_value'] = value
            info['contextual_dims'].append({
                'value': value,
                'pattern': ptype,
                'match': match.group(0)
            })
            return info

    # No pattern matched - check if it contains any numbers
    if re.search(r'\d', text):
        info['filter_reason'] = 'has numbers but no dimension pattern'
    else:
        info['filter_reason'] = 'no numbers'

    return info


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_ocr.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"Analyzing: {pdf_path}\n")

    # Convert PDF to image
    print("Converting PDF to image (300 DPI)...")
    image = pdf_to_image(pdf_path, dpi=300)
    print(f"Image size: {image.shape[1]} x {image.shape[0]}\n")

    # Run OCR
    print("Running EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(image)

    print(f"\n{'='*60}")
    print(f"Found {len(results)} text regions")
    print(f"{'='*60}\n")

    # Categorize results
    dimensions = []
    filtered = []
    non_numeric = []

    for bbox, text, confidence in results:
        analysis = analyze_text(text)
        analysis['confidence'] = confidence

        if analysis['is_dimension']:
            dimensions.append(analysis)
        elif analysis['filter_reason']:
            if analysis['filter_reason'] == 'no numbers':
                non_numeric.append(analysis)
            else:
                filtered.append(analysis)
        else:
            filtered.append(analysis)

    # Print dimensions found
    print(f"VALID DIMENSIONS: {len(dimensions)}")
    print("-" * 40)
    for d in dimensions:
        print(f"  '{d['text']}' -> {d['parsed_value']} {d.get('unit', '')} (conf={d['confidence']:.2f})")

    # Print filtered numeric texts
    print(f"\nFILTERED NUMERIC TEXTS: {len(filtered)}")
    print("-" * 40)
    for f in filtered:
        print(f"  '{f['text']}' - {f['filter_reason']} (conf={f['confidence']:.2f})")

    # Print non-numeric texts (abbreviated)
    print(f"\nNON-NUMERIC TEXTS: {len(non_numeric)}")
    print("-" * 40)
    for n in non_numeric[:20]:  # First 20
        text_preview = n['text'][:40] + '...' if len(n['text']) > 40 else n['text']
        print(f"  '{text_preview}' (conf={n['confidence']:.2f})")
    if len(non_numeric) > 20:
        print(f"  ... and {len(non_numeric) - 20} more")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total texts:    {len(results)}")
    print(f"Dimensions:     {len(dimensions)}")
    print(f"Filtered:       {len(filtered)}")
    print(f"Non-numeric:    {len(non_numeric)}")


if __name__ == "__main__":
    main()
