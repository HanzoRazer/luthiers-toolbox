"""
Photo Pipeline Trial — Black Background Guitar Silhouette
==========================================================

Generates a synthetic white-on-black guitar body outline,
runs it through each stage of the pipeline, and reports
quality metrics at every step.

This answers: "If I give it a clean B&W photo, what comes out?"
"""
import sys
import os
import math
import tempfile
from pathlib import Path

import numpy as np
import cv2

# Ensure blueprint-import is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vectorizer_enhancements import (
    GuitarPhotoProcessor, classify_input_type, InputType
)


# =============================================================================
# Step 1: Generate a realistic Stratocaster body silhouette
# =============================================================================

def generate_strat_silhouette(
    width: int = 1200,
    height: int = 1600,
    body_color: int = 255,
    bg_color: int = 0
) -> np.ndarray:
    """
    Draw a simplified but realistic Stratocaster body outline.

    Uses ellipses and contour points based on actual Strat proportions:
      - Body length ~406mm, width ~325mm
      - Double cutaway
      - Belly cut area (lower bout wider than upper)

    Returns BGR image.
    """
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)

    # Body center
    cx, cy = width // 2, height // 2

    # Scale: ~0.35 mm/px at this resolution
    # Body ~406mm long = ~1160px, ~325mm wide = ~930px
    # We'll draw slightly smaller to leave margin
    scale = 0.85

    # Key body points (approximate Strat outline, clockwise from top-center)
    # Coordinates relative to center, in pixels
    body_points = np.array([
        # Upper bout (neck end)
        [0, -520],
        [60, -515],
        [120, -500],
        [170, -475],
        [200, -440],

        # Treble cutaway (upper horn)
        [210, -400],
        [200, -350],
        [180, -310],
        [155, -275],
        [140, -250],
        [135, -220],
        [140, -190],
        [160, -160],
        [190, -130],
        [230, -100],

        # Treble waist
        [260, -60],
        [275, -20],
        [280, 20],
        [275, 60],

        # Lower bout (treble side)
        [290, 100],
        [320, 150],
        [350, 200],
        [370, 260],
        [380, 320],
        [375, 380],
        [360, 430],
        [330, 470],
        [290, 500],
        [240, 520],
        [180, 530],
        [120, 535],
        [60, 533],

        # Bottom
        [0, 530],
        [-60, 533],
        [-120, 535],
        [-180, 530],
        [-240, 520],

        # Lower bout (bass side)
        [-290, 500],
        [-330, 470],
        [-360, 430],
        [-380, 380],
        [-390, 320],
        [-385, 260],
        [-370, 200],
        [-345, 150],
        [-310, 100],

        # Bass waist
        [-285, 60],
        [-275, 20],
        [-270, -20],
        [-275, -60],

        # Bass cutaway (lower horn — deeper than treble)
        [-260, -100],
        [-240, -140],
        [-210, -180],
        [-175, -220],
        [-155, -260],
        [-150, -300],
        [-160, -340],
        [-180, -370],
        [-210, -400],

        # Upper bout (bass side)
        [-210, -430],
        [-200, -460],
        [-170, -485],
        [-130, -500],
        [-70, -515],
    ], dtype=np.float32)

    # Apply scale and translate to center
    body_points = (body_points * scale).astype(np.int32)
    body_points[:, 0] += cx
    body_points[:, 1] += cy

    # Draw filled body
    cv2.fillPoly(img, [body_points], (body_color, body_color, body_color))

    # Smooth the outline slightly (real photos have smooth curves)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 2)
    _, smoothed = cv2.threshold(blurred, 128, 255, cv2.THRESH_BINARY)
    img = cv2.cvtColor(smoothed, cv2.COLOR_GRAY2BGR)

    return img


def add_neck_pocket(img: np.ndarray, cx: int, cy: int, scale: float = 0.85) -> np.ndarray:
    """Add a neck pocket rectangle to the body."""
    # Neck pocket: ~56mm wide, ~100mm deep, centered at top
    pw = int(56 / 0.35 * scale / 2)
    ph = int(100 / 0.35 * scale)
    top_y = cy - int(520 * scale)

    pocket_pts = np.array([
        [cx - pw, top_y],
        [cx + pw, top_y],
        [cx + pw, top_y + ph],
        [cx - pw, top_y + ph]
    ], dtype=np.int32)
    cv2.fillPoly(img, [pocket_pts], (0, 0, 0))
    return img


def add_pickup_routes(img: np.ndarray, cx: int, cy: int, scale: float = 0.85) -> np.ndarray:
    """Add pickup route rectangles."""
    # Bridge pickup: ~72mm x 18mm
    # Middle pickup: ~72mm x 18mm
    # Neck pickup: ~72mm x 18mm
    pw = int(72 / 0.35 * scale / 2)
    ph = int(18 / 0.35 * scale / 2)

    positions_y = [
        cy + int(120 * scale),   # Bridge
        cy + int(10 * scale),    # Middle
        cy - int(100 * scale),   # Neck
    ]
    for py in positions_y:
        pts = np.array([
            [cx - pw, py - ph],
            [cx + pw, py - ph],
            [cx + pw, py + ph],
            [cx - pw, py + ph]
        ], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))

    return img


def add_control_cavity(img: np.ndarray, cx: int, cy: int, scale: float = 0.85) -> np.ndarray:
    """Add a control cavity outline."""
    # Offset to bass side, lower bout
    cavity_cx = cx + int(150 * scale)
    cavity_cy = cy + int(300 * scale)
    w = int(60 / 0.35 * scale / 2)
    h = int(40 / 0.35 * scale / 2)
    cv2.ellipse(img, (cavity_cx, cavity_cy), (w, h), 30, 0, 360, (0, 0, 0), -1)
    return img


# =============================================================================
# Step 2: Run through each stage and measure
# =============================================================================

def measure_contour_quality(binary: np.ndarray, label: str) -> dict:
    """Measure what the contour finder would get from this binary image."""
    contours, hierarchy = cv2.findContours(
        binary if len(binary.shape) == 2 else cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY),
        cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    areas = [cv2.contourArea(c) for c in contours]
    large = [a for a in areas if a > 1000]

    # Find body candidate (largest contour)
    body_idx = np.argmax(areas) if areas else -1
    body_area = areas[body_idx] if body_idx >= 0 else 0
    body_perimeter = cv2.arcLength(contours[body_idx], True) if body_idx >= 0 else 0
    body_points = len(contours[body_idx]) if body_idx >= 0 else 0

    # Noise ratio: how much of the total contour area is NOT the body
    total_area = sum(areas)
    noise_area = total_area - body_area
    noise_ratio = noise_area / max(total_area, 1)

    return {
        'label': label,
        'total_contours': len(contours),
        'large_contours_gt_1000px': len(large),
        'body_area_px': int(body_area),
        'body_perimeter_px': int(body_perimeter),
        'body_points': body_points,
        'noise_ratio': round(noise_ratio, 4),
        'noise_contours': len(contours) - 1 if contours else 0,
    }


def run_trial():
    """Run the full trial and print results."""
    print("=" * 70)
    print("PHOTO PIPELINE TRIAL — Black Background Stratocaster")
    print("=" * 70)

    # --- Generate test image ---
    print("\n[1] Generating synthetic Strat silhouette (white on black)...")
    img = generate_strat_silhouette(1200, 1600, body_color=255, bg_color=0)
    cx, cy = 600, 800

    # Add internal features
    img = add_neck_pocket(img, cx, cy)
    img = add_pickup_routes(img, cx, cy)
    img = add_control_cavity(img, cx, cy)

    print(f"    Image size: {img.shape[1]}x{img.shape[0]}")
    print(f"    White pixels: {np.sum(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) > 128)}")
    print(f"    Total pixels: {img.shape[0] * img.shape[1]}")

    # Save input
    trial_dir = Path(tempfile.mkdtemp(prefix="photo_trial_"))
    input_path = trial_dir / "01_input_bw_strat.png"
    cv2.imwrite(str(input_path), img)
    print(f"    Saved: {input_path}")

    # --- Classify input ---
    print("\n[2] Input classification...")
    input_type = classify_input_type(img)
    print(f"    Detected type: {input_type.value}")
    if input_type == InputType.BLUEPRINT:
        print("    ⚠ Classified as BLUEPRINT — photo processor would be SKIPPED")
        print("    This is actually correct behavior for a clean B&W image!")
    elif input_type == InputType.PHOTO:
        print("    Classified as PHOTO — will go through photo processor")

    # --- Measure BEFORE photo processing (direct contour extraction) ---
    print("\n[3] Direct contour extraction (no photo processing)...")
    gray_direct = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary_direct = cv2.threshold(gray_direct, 128, 255, cv2.THRESH_BINARY)
    metrics_direct = measure_contour_quality(binary_direct, "DIRECT (no photo proc)")
    print_metrics(metrics_direct)

    # --- Run through GuitarPhotoProcessor ---
    print("\n[4] Running GuitarPhotoProcessor pipeline...")
    processor = GuitarPhotoProcessor(use_rembg=False)  # Skip rembg for reproducibility

    stages = {}
    def capture(name, image):
        stages[name] = image.copy()

    result_binary, metadata = processor.preprocess_for_extraction(img, debug_callback=capture)
    print(f"    Metadata: {metadata}")

    # Save all intermediate stages
    for name, stage_img in sorted(stages.items()):
        path = trial_dir / f"{name}.png"
        cv2.imwrite(str(path), stage_img)
        print(f"    Stage saved: {name} ({stage_img.shape})")

    result_path = trial_dir / "07_photo_processor_output.png"
    cv2.imwrite(str(result_path), result_binary)

    # --- Measure AFTER photo processing ---
    print("\n[5] Contour extraction from photo processor output...")
    metrics_photo = measure_contour_quality(result_binary, "AFTER photo processor")
    print_metrics(metrics_photo)

    # --- Compare ---
    print("\n[6] COMPARISON")
    print("-" * 70)
    print(f"  {'Metric':<35} {'Direct':>12} {'Photo Proc':>12}")
    print("-" * 70)
    for key in ['total_contours', 'large_contours_gt_1000px', 'body_area_px',
                'body_points', 'noise_ratio', 'noise_contours']:
        v1 = metrics_direct[key]
        v2 = metrics_photo[key]
        flag = ""
        if key == 'noise_ratio':
            if v2 > v1 * 1.5:
                flag = " ← WORSE"
            elif v2 < v1:
                flag = " ← better"
        elif key == 'total_contours':
            if v2 > v1 * 3:
                flag = " ← WAY MORE NOISE"
            elif v2 > v1 * 1.5:
                flag = " ← more noise"
        print(f"  {key:<35} {str(v1):>12} {str(v2):>12}{flag}")
    print("-" * 70)

    # --- Verdict ---
    print("\n[7] VERDICT")
    if metrics_photo['total_contours'] > metrics_direct['total_contours'] * 3:
        print("  ❌ Photo processor ADDED significant noise to a clean input.")
        print("     The direct path produces better contours for B&W images.")
    elif metrics_photo['noise_ratio'] > 0.1:
        print("  ⚠ Photo processor introduced some noise (>10% non-body area).")
    else:
        print("  ✓ Photo processor maintained reasonable contour quality.")

    if metrics_direct['noise_ratio'] < 0.05 and metrics_direct['total_contours'] < 20:
        print("  ✓ Direct extraction is CLEAN — confirms B&W input is viable.")
        print("  → Recommendation: skip photo processor for B&W/black-bg inputs.")

    # --- Also test as a grayscale scan (more realistic) ---
    print("\n[8] BONUS: Simulated phone photo (added noise + slight blur)...")
    noisy = img.copy().astype(np.float32)
    noisy += np.random.normal(0, 12, noisy.shape)  # Gaussian noise
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    noisy = cv2.GaussianBlur(noisy, (3, 3), 0.8)  # Slight defocus

    noisy_path = trial_dir / "08_noisy_phone_sim.png"
    cv2.imwrite(str(noisy_path), noisy)

    input_type_noisy = classify_input_type(noisy)
    print(f"    Classified as: {input_type_noisy.value}")

    gray_noisy = cv2.cvtColor(noisy, cv2.COLOR_BGR2GRAY)
    _, binary_noisy = cv2.threshold(gray_noisy, 128, 255, cv2.THRESH_BINARY)
    metrics_noisy_direct = measure_contour_quality(binary_noisy, "NOISY direct")
    print_metrics(metrics_noisy_direct)

    result_noisy, meta_noisy = processor.preprocess_for_extraction(noisy, debug_callback=None)
    metrics_noisy_proc = measure_contour_quality(result_noisy, "NOISY after photo proc")
    print_metrics(metrics_noisy_proc)

    print(f"\n    All trial artifacts saved to: {trial_dir}")

    # --- Full vectorizer pipeline with dark_background support ---
    print("\n[9] FULL VECTORIZER PIPELINE (dark_background=None → auto-detect)...")
    from vectorizer_phase3 import Phase3Vectorizer, InstrumentType

    # Save a clean PNG for the vectorizer to load
    full_test_img = generate_strat_silhouette(1200, 1600, body_color=255, bg_color=0)
    full_test_img = add_neck_pocket(full_test_img, 600, 800)
    full_test_img = add_pickup_routes(full_test_img, 600, 800)
    full_test_img = add_control_cavity(full_test_img, 600, 800)
    full_input = trial_dir / "09_vectorizer_input.png"
    cv2.imwrite(str(full_input), full_test_img)

    dxf_output = trial_dir / "09_vectorizer_output.dxf"
    vec = Phase3Vectorizer(dpi=150)
    result = vec.extract(
        str(full_input),
        output_path=str(dxf_output),
        instrument_type=InstrumentType.ELECTRIC_GUITAR,
        dual_pass=True,
        cam_ready=True,
        dark_background=None  # auto-detect
    )

    print(f"    DXF output: {dxf_output}")
    print(f"    Sheet type: {result.sheet_type}")
    print(f"    Body size (mm): {result.dimensions_mm}")
    if hasattr(result, 'features_found'):
        print(f"    Features found: {result.features_found}")
    if hasattr(result, 'contours_by_category'):
        cats = {cat: len(items) for cat, items in result.contours_by_category.items()}
        print(f"    Feature counts: {cats}")

    # Verify body was detected
    bw, bh = result.dimensions_mm
    if bw > 100 and bh > 100:
        print("  OK BODY DETECTED -- dark background support working!")
        print(f"    Body: {bw:.1f} x {bh:.1f} mm")
    else:
        print("  FAIL BODY NOT DETECTED -- dark background fix failed")
        print(f"    Body: {bw:.1f} x {bh:.1f} mm (expected ~325 x 406)")

    # Also run WITHOUT dark_background to confirm it would fail
    print("\n[10] CONTROL: Same image with dark_background=False (should fail)...")
    dxf_control = trial_dir / "10_control_no_darkbg.dxf"
    result_control = vec.extract(
        str(full_input),
        output_path=str(dxf_control),
        instrument_type=InstrumentType.ELECTRIC_GUITAR,
        dual_pass=True,
        cam_ready=True,
        dark_background=False  # force OFF
    )
    bw_c, bh_c = result_control.dimensions_mm
    if bw_c < 10 and bh_c < 10:
        print(f"  OK Correctly FAILS without dark-bg support (body={bw_c:.1f}x{bh_c:.1f}mm)")
    else:
        print(f"  NOTE Unexpectedly succeeded (body={bw_c:.1f}x{bh_c:.1f}mm)")

    print("=" * 70)

    return trial_dir


def print_metrics(m: dict):
    print(f"    [{m['label']}]")
    print(f"      Total contours:  {m['total_contours']}")
    print(f"      Large (>1000px): {m['large_contours_gt_1000px']}")
    print(f"      Body area:       {m['body_area_px']} px")
    print(f"      Body points:     {m['body_points']}")
    print(f"      Noise ratio:     {m['noise_ratio']:.1%}")
    print(f"      Noise contours:  {m['noise_contours']}")


if __name__ == "__main__":
    run_trial()
