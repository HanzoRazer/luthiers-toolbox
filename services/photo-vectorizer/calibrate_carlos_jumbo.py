#!/usr/bin/env python3
"""
Carlos Jumbo Blueprint Calibration & DXF Generation
====================================================

Uses known reference dimensions to calibrate scale, then extracts
body dimensions and verifies with acoustic body volume calculator.

Known references for Carlos Jumbo (from spec + standard dimensions):
- Scale length: 650mm (standard Spanish jumbo)
- Nut width: 52mm (classical) / 44.5mm (steel-string)
- Soundhole diameter: 102mm (4 inches)
- Body join at 12th fret: scale_length / 2 = 325mm from nut

Calibration approach:
1. Detect soundhole circle in blueprint (most reliable reference)
2. Calculate mm/px from soundhole diameter (102mm)
3. Measure body dimensions using calibrated scale
4. Verify with acoustic body volume calculator
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

try:
    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


# =============================================================================
# KNOWN CARLOS JUMBO DIMENSIONS (reference for calibration)
# =============================================================================

CARLOS_JUMBO_REFS = {
    'scale_length_mm': 650.0,
    'nut_width_mm': 52.0,           # Classical variant
    'nut_width_steel_mm': 44.5,     # Steel-string variant
    'soundhole_diameter_mm': 102.0,  # 4 inches
    'body_join_fret': 12,           # 12th fret = scale/2 = 325mm from nut
    'fret_12_from_nut_mm': 325.0,   # Half scale length

    # Expected body proportions for jumbo (for validation)
    'expected_lower_bout_range_mm': (410, 450),  # Jumbo is wider than dreadnought
    'expected_body_length_range_mm': (500, 550),
    'expected_volume_range_liters': (14.0, 19.0),  # Jumbo > dreadnought (~13L)
}


# =============================================================================
# PDF CONVERSION
# =============================================================================

def pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 300) -> np.ndarray:
    """Convert PDF to image at high DPI."""
    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    doc.close()
    return img


# =============================================================================
# REFERENCE DETECTION (Soundhole, Nut Width, etc.)
# =============================================================================

def detect_soundhole_circle(image: np.ndarray, expected_ratio: float = 0.08) -> tuple:
    """
    Detect the soundhole circle in a guitar blueprint.

    The soundhole is typically ~102mm diameter. On a full body view,
    it's about 8-12% of the body width.

    Returns:
        (center_x, center_y, radius_px) or None if not found
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Enhance edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Estimate expected soundhole radius based on image size
    # For a full guitar view, soundhole is ~8-12% of body width
    min_radius = int(w * 0.03)
    max_radius = int(w * 0.15)

    # Detect circles using Hough transform
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_radius * 2,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is None:
        return None

    # Filter circles - soundhole should be:
    # 1. In the upper-middle portion of the body (not at edges)
    # 2. Approximately circular (we're looking at HoughCircles output)
    # 3. In a reasonable size range

    circles = np.uint16(np.around(circles))
    candidates = []

    for (cx, cy, r) in circles[0]:
        # Check position - soundhole is typically in upper-middle of body
        # For a front view, it should be in the center horizontally
        # and in the upper third of the body
        rel_x = cx / w
        rel_y = cy / h

        # Accept circles in reasonable positions
        if 0.25 < rel_x < 0.75:  # Center third horizontally
            candidates.append((cx, cy, r, abs(rel_x - 0.5)))  # Score by how centered

    if not candidates:
        return None

    # Return most centered circle
    candidates.sort(key=lambda c: c[3])
    cx, cy, r, _ = candidates[0]

    return (int(cx), int(cy), int(r))


def detect_nut_width(image: np.ndarray, headstock_region: tuple = None) -> float:
    """
    Detect nut width from the headstock region.

    The nut is at the junction between neck and headstock.
    For Carlos Jumbo: 52mm (classical) or 44.5mm (steel-string)
    """
    # This requires more sophisticated detection
    # For now, return None - we'll use soundhole as primary reference
    return None


def measure_body_dimensions(image: np.ndarray, mm_per_px: float) -> dict:
    """
    Measure body dimensions from a calibrated image.

    Detects:
    - Lower bout (widest point)
    - Upper bout
    - Waist (narrowest point)
    - Body length
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Edge detection
    edges = cv2.Canny(gray, 30, 100)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Get largest contour (body outline)
    body_contour = max(contours, key=cv2.contourArea)

    # Get bounding rect
    x, y, bw, bh = cv2.boundingRect(body_contour)

    # Analyze width at different heights to find bouts and waist
    # Sample widths along the body
    widths = []
    for row in range(y, y + bh, 5):
        # Find leftmost and rightmost points at this row
        row_mask = np.zeros_like(gray)
        cv2.drawContours(row_mask, [body_contour], -1, 255, -1)

        row_pixels = np.where(row_mask[row, :] > 0)[0]
        if len(row_pixels) > 0:
            width_px = row_pixels[-1] - row_pixels[0]
            widths.append((row, width_px))

    if not widths:
        return {
            'body_width_px': bw,
            'body_height_px': bh,
            'body_width_mm': bw * mm_per_px,
            'body_height_mm': bh * mm_per_px,
        }

    # Find max width (lower bout) and min width (waist)
    widths.sort(key=lambda x: x[1], reverse=True)
    lower_bout_px = widths[0][1]

    # Find waist (minimum width in middle portion)
    middle_widths = [(r, w) for r, w in widths if y + bh * 0.3 < r < y + bh * 0.7]
    if middle_widths:
        middle_widths.sort(key=lambda x: x[1])
        waist_px = middle_widths[0][1]
    else:
        waist_px = min(w for _, w in widths)

    # Upper bout (max width in upper portion)
    upper_widths = [(r, w) for r, w in widths if r < y + bh * 0.4]
    if upper_widths:
        upper_widths.sort(key=lambda x: x[1], reverse=True)
        upper_bout_px = upper_widths[0][1]
    else:
        upper_bout_px = lower_bout_px * 0.75  # Estimate

    return {
        'lower_bout_px': lower_bout_px,
        'upper_bout_px': upper_bout_px,
        'waist_px': waist_px,
        'body_length_px': bh,
        'body_width_px': bw,

        'lower_bout_mm': lower_bout_px * mm_per_px,
        'upper_bout_mm': upper_bout_px * mm_per_px,
        'waist_mm': waist_px * mm_per_px,
        'body_length_mm': bh * mm_per_px,
        'body_width_mm': bw * mm_per_px,
    }


# =============================================================================
# VOLUME CALCULATION (from acoustic_body_volume.py)
# =============================================================================

def calculate_body_volume(lower_bout_mm: float, upper_bout_mm: float, waist_mm: float,
                          body_length_mm: float, depth_endblock_mm: float = 125.0,
                          depth_neck_mm: float = 105.0, shape_factor: float = 0.85) -> dict:
    """
    Calculate guitar body volume using elliptical cross-section integration.

    Default depths from Carlos Jumbo spec:
    - depth_endblock: 125mm
    - depth_neck: 105mm
    """
    L = body_length_mm

    # Section lengths (empirical proportions)
    lower_len = L * 0.40
    waist_len = L * 0.25
    upper_len = L * 0.35

    avg_depth = (depth_endblock_mm + depth_neck_mm) / 2

    # Cross-sectional areas (ellipse formula with shape factor)
    lower_area = math.pi * (lower_bout_mm / 2) * (depth_endblock_mm / 2) * shape_factor
    waist_area = math.pi * (waist_mm / 2) * (avg_depth / 2) * shape_factor
    upper_area = math.pi * (upper_bout_mm / 2) * (depth_neck_mm / 2) * shape_factor

    # Volume of each section
    V_lower = (lower_area + waist_area) / 2 * lower_len
    V_waist = waist_area * waist_len
    V_upper = (waist_area + upper_area) / 2 * upper_len

    total_mm3 = V_lower + V_waist + V_upper

    return {
        'volume_mm3': total_mm3,
        'volume_liters': total_mm3 / 1e6,
        'volume_cubic_inches': total_mm3 / 16387.064,
    }


def calculate_helmholtz_freq(volume_liters: float, soundhole_mm: float = 102.0) -> float:
    """Calculate Helmholtz resonance frequency."""
    c = 343000  # mm/s
    A = math.pi * (soundhole_mm / 2) ** 2
    top_thickness = 2.8
    L_eff = 1.7 * top_thickness + 0.85 * soundhole_mm
    V_mm3 = volume_liters * 1e6
    return (c / (2 * math.pi)) * math.sqrt(A / (V_mm3 * L_eff))


# =============================================================================
# MAIN CALIBRATION WORKFLOW
# =============================================================================

def calibrate_and_extract(pdf_path: Path, page_num: int = 0) -> dict:
    """
    Full calibration and extraction workflow.

    1. Convert PDF to image
    2. Detect soundhole for calibration
    3. Calculate mm/px ratio
    4. Measure body dimensions
    5. Calculate volume and verify
    """
    print(f"\n{'='*60}")
    print(f"CALIBRATING: {pdf_path.name} (page {page_num + 1})")
    print('='*60)

    # Convert PDF
    image = pdf_page_to_image(pdf_path, page_num, dpi=300)
    h, w = image.shape[:2]
    print(f"Image: {w} x {h} px (300 DPI)")

    # Detect soundhole
    soundhole = detect_soundhole_circle(image)

    if soundhole:
        cx, cy, radius_px = soundhole
        diameter_px = radius_px * 2

        # Calculate scale from soundhole (102mm diameter)
        soundhole_mm = CARLOS_JUMBO_REFS['soundhole_diameter_mm']
        mm_per_px = soundhole_mm / diameter_px

        print(f"\nSoundhole detected:")
        print(f"  Center: ({cx}, {cy})")
        print(f"  Diameter: {diameter_px} px")
        print(f"  Reference: {soundhole_mm} mm")
        print(f"  Scale: {mm_per_px:.4f} mm/px")

        calibration_source = 'soundhole'
    else:
        # Fallback: estimate from expected body proportions
        # Assume body takes up ~60-70% of image height
        # And Carlos Jumbo body length is ~520mm
        estimated_body_height_px = h * 0.65
        mm_per_px = 520.0 / estimated_body_height_px

        print(f"\nNo soundhole detected - using estimated scale:")
        print(f"  Estimated body height: {estimated_body_height_px:.0f} px")
        print(f"  Assumed body length: 520 mm")
        print(f"  Scale: {mm_per_px:.4f} mm/px (ESTIMATED)")

        calibration_source = 'estimated'

    # Measure body dimensions
    dims = measure_body_dimensions(image, mm_per_px)

    if dims:
        print(f"\nMeasured dimensions:")
        print(f"  Lower bout:  {dims.get('lower_bout_mm', 0):.1f} mm")
        print(f"  Upper bout:  {dims.get('upper_bout_mm', 0):.1f} mm")
        print(f"  Waist:       {dims.get('waist_mm', 0):.1f} mm")
        print(f"  Body length: {dims.get('body_length_mm', 0):.1f} mm")

        # Calculate volume
        volume = calculate_body_volume(
            dims.get('lower_bout_mm', 430),
            dims.get('upper_bout_mm', 310),
            dims.get('waist_mm', 270),
            dims.get('body_length_mm', 520),
        )

        hz = calculate_helmholtz_freq(volume['volume_liters'])

        print(f"\nCalculated volume:")
        print(f"  Volume: {volume['volume_liters']:.2f} liters ({volume['volume_cubic_inches']:.1f} in³)")
        print(f"  Helmholtz: {hz:.1f} Hz")

        # Validate against expected ranges
        expected_vol = CARLOS_JUMBO_REFS['expected_volume_range_liters']
        if expected_vol[0] <= volume['volume_liters'] <= expected_vol[1]:
            print(f"  ✓ Volume within expected jumbo range ({expected_vol[0]}-{expected_vol[1]} L)")
        else:
            print(f"  ⚠ Volume outside expected range ({expected_vol[0]}-{expected_vol[1]} L)")

    return {
        'pdf': str(pdf_path),
        'page': page_num,
        'image_size': (w, h),
        'mm_per_px': mm_per_px,
        'calibration_source': calibration_source,
        'soundhole': soundhole,
        'dimensions': dims,
        'volume': volume if dims else None,
    }


def main():
    """Run calibration on Carlos Jumbo blueprints."""

    if not FITZ_AVAILABLE:
        print("ERROR: PyMuPDF required - pip install PyMuPDF")
        return

    repo_root = Path(__file__).parent.parent.parent
    jumbo_dir = repo_root / "Guitar Plans" / "Jumbo Carlos"

    if not jumbo_dir.exists():
        print(f"ERROR: Directory not found: {jumbo_dir}")
        return

    pdfs = sorted(jumbo_dir.glob("JUMBO-CARLOS-*.pdf"))
    print(f"Found {len(pdfs)} Carlos Jumbo PDFs")

    results = []
    for pdf_path in pdfs:
        result = calibrate_and_extract(pdf_path, page_num=0)
        results.append(result)

    # Summary
    print("\n" + "="*60)
    print("CALIBRATION SUMMARY")
    print("="*60)

    for r in results:
        pdf_name = Path(r['pdf']).name
        dims = r.get('dimensions', {})
        vol = r.get('volume', {})

        print(f"\n{pdf_name}:")
        print(f"  Scale: {r['mm_per_px']:.4f} mm/px ({r['calibration_source']})")
        if dims:
            print(f"  Body: {dims.get('body_length_mm', 0):.0f} x {dims.get('lower_bout_mm', 0):.0f} mm")
        if vol:
            print(f"  Volume: {vol.get('volume_liters', 0):.2f} L")


if __name__ == "__main__":
    main()
