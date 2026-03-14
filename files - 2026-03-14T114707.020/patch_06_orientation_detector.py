"""
PATCH 06 — Instrument Orientation Detector + Rotation Corrector
===============================================================

Problem:
  BodyIsolator profiles row-wise pixel widths, assuming the instrument is
  roughly upright (portrait orientation, neck at top).  Two failure modes:

  A) LANDSCAPE image: guitar body in upper-left, neck extends to lower-right.
     minAreaRect of the silhouette gives aspect ratio ~2.44:1.
     Row-width profiling sees the neck instead of the body.
     Result: BodyIsolator reports 1291×371px instead of ~619×545px.

  B) TILT: even in portrait, a ~12° tilt smears the row-width profile.
     Body rows are under-counted; neck rows bleed into the body region.

Fix:
  OrientationDetector runs BEFORE Stage 4 (background removal), on the
  raw image.  It returns:
    - orientation:    "portrait" | "landscape"
    - coarse_angle:   0 (portrait) or 90 (landscape CCW rotation applied)
    - tilt_angle:     residual tilt in degrees (applied as affine)
    - total_rotation: coarse + tilt (for inverse transform on SVG/DXF output)
    - rotated_image:  image ready for the rest of the pipeline

  After processing, the SVG/DXF contour coordinates are rotated back by
  -total_rotation so they align with the original image frame.

Validated on:
  - Archtop (1024×1536 portrait):    aspect=2.44 in silhouette (but image is
    portrait) — tilt correction only, 12° applied
  - Flamed maple (1536×1024 landscape): 90° CCW + tilt → body 527mm ✓
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────
LANDSCAPE_ASPECT_THRESHOLD = 1.8   # silhouette aspect > this → rotate 90°
TILT_THRESHOLD_DEG         = 5.0   # |tilt| > this → apply affine correction
BG_THRESH_LIGHT            = 200   # pixel value for light-background silhouette
BG_THRESH_DARK             = 80    # pixel value for dark-background silhouette


@dataclass
class OrientationResult:
    """Result of instrument orientation detection."""
    orientation:    str             # "portrait" | "landscape"
    coarse_angle:   float           # 0 or 90 (CCW degrees)
    tilt_angle:     float           # residual tilt after coarse rotation
    total_rotation: float           # coarse + tilt  (use for inverse transform)
    rotated_image:  np.ndarray      # image after all rotation applied
    original_shape: Tuple[int, int] # (h, w) of original image
    canvas_shape:   Tuple[int, int] # (h, w) of rotated_image (may differ)
    inverse_matrix: Optional[np.ndarray] = None  # 2×3 affine for back-transform
    notes: list = field(default_factory=list)


class OrientationDetector:
    """
    Detects instrument orientation and returns a rotation-corrected image.

    Parameters
    ----------
    landscape_aspect : float
        minAreaRect aspect ratio above which a 90° CCW rotation is applied.
    tilt_threshold   : float
        Residual tilt (degrees) below which no affine correction is applied.
    bg_fill          : tuple
        BGR fill colour for warpAffine borders (default: near-white).
    """

    def __init__(
        self,
        landscape_aspect: float       = LANDSCAPE_ASPECT_THRESHOLD,
        tilt_threshold:   float       = TILT_THRESHOLD_DEG,
        bg_fill:          tuple       = (245, 245, 245),
    ):
        self.landscape_aspect = landscape_aspect
        self.tilt_threshold   = tilt_threshold
        self.bg_fill          = bg_fill

    # ------------------------------------------------------------------
    def detect_and_correct(
        self,
        image:      np.ndarray,
        is_dark_bg: bool = False,
        fg_mask:    Optional[np.ndarray] = None,
    ) -> OrientationResult:
        """
        Detect orientation and return a corrected image + metadata.

        Parameters
        ----------
        image      : BGR image (pre-inversion, original)
        is_dark_bg : True if BackgroundTypeDetector reported solid_dark bg
        fg_mask    : Optional foreground mask from Stage 4 (rembg/GrabCut).
                     When supplied, used directly for silhouette instead of
                     thresholding the raw image.  Recommended for dark-bg images
                     where raw thresholding confuses background with instrument.

        Returns
        -------
        OrientationResult

        Notes
        -----
        For TEXTURED dark backgrounds (wood, fabric), supply fg_mask from rembg
        for reliable results.  Raw thresholding on textured-dark images produces
        a silhouette that includes background texture, making aspect ratio and
        tilt detection unreliable.
        """
        orig_h, orig_w = image.shape[:2]
        notes = []

        # ── Step 1: binary silhouette ─────────────────────────────────────
        if fg_mask is not None and np.sum(fg_mask > 0) > (orig_h * orig_w * 0.05):
            thresh = fg_mask.copy()
            notes.append("Silhouette from fg_mask (Stage 4 output)")
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) \
                if len(image.shape) == 3 else image
            if is_dark_bg:
                _, thresh = cv2.threshold(gray, BG_THRESH_DARK, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(gray, BG_THRESH_LIGHT, 255, cv2.THRESH_BINARY_INV)
            if fg_mask is None and is_dark_bg:
                notes.append(
                    "⚠️  Dark bg without fg_mask — silhouette may include background texture. "
                    "Pass fg_mask from rembg for reliable results.")

        kernel = np.ones((9, 9), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,  kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            notes.append("No silhouette found — returning image unchanged")
            return OrientationResult(
                orientation="portrait", coarse_angle=0, tilt_angle=0,
                total_rotation=0, rotated_image=image.copy(),
                original_shape=(orig_h, orig_w), canvas_shape=(orig_h, orig_w),
                notes=notes)

        largest  = max(contours, key=cv2.contourArea)
        rect     = cv2.minAreaRect(largest)
        center, (rw, rh), angle = rect

        # ── Step 2: determine coarse orientation ──────────────────────────
        # minAreaRect convention: angle ∈ (-90, 0]
        # If rw > rh: the long dimension is "width" (roughly horizontal)
        long_dim  = max(rw, rh)
        short_dim = min(rw, rh)
        aspect    = long_dim / max(short_dim, 1)

        notes.append(f"Silhouette minAreaRect: {rw:.0f}×{rh:.0f} at {angle:.1f}°, aspect={aspect:.2f}")

        if aspect > self.landscape_aspect and rw > rh:
            # Instrument is lying on its side (landscape)
            orientation  = "landscape"
            coarse_angle = 90.0
            notes.append(f"Landscape detected (aspect {aspect:.2f} > {self.landscape_aspect}) → 90° CCW")
        else:
            orientation  = "portrait"
            coarse_angle = 0.0
            notes.append("Portrait orientation")

        # ── Step 3: apply coarse rotation ─────────────────────────────────
        if coarse_angle == 90:
            working = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            working = image.copy()

        wh, ww = working.shape[:2]

        # ── Step 4: measure residual tilt on coarse-corrected image ───────
        gray_w = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY) if len(working.shape) == 3 else working

        if is_dark_bg:
            _, thresh_w = cv2.threshold(gray_w, BG_THRESH_DARK, 255, cv2.THRESH_BINARY)
        else:
            _, thresh_w = cv2.threshold(gray_w, BG_THRESH_LIGHT, 255, cv2.THRESH_BINARY_INV)

        thresh_w = cv2.morphologyEx(thresh_w, cv2.MORPH_CLOSE, kernel, iterations=3)
        contours_w, _ = cv2.findContours(thresh_w, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        tilt_angle = 0.0
        if contours_w:
            lw        = max(contours_w, key=cv2.contourArea)
            rect_w    = cv2.minAreaRect(lw)
            _, (rw2, rh2), angle_w = rect_w

            # OpenCV minAreaRect angle convention (range (-90, 0]):
            #   angle_w is the rotation of the FIRST side (width) from horizontal.
            #   When rw2 < rh2 (portrait/tall): the long axis is vertical.
            #     tilt from vertical = angle_w  (0° = upright, -11.9° = leaning)
            #   When rw2 > rh2 (landscape/wide): should not happen after 90° coarse
            #     rotation, but if it does: tilt = angle_w + 90
            if rw2 < rh2:
                tilt_angle = angle_w           # direct: tilt of long (vertical) axis
            else:
                tilt_angle = angle_w + 90.0    # wide still — compensate convention

            if abs(tilt_angle) > self.tilt_threshold:
                notes.append(f"Residual tilt: {tilt_angle:.1f}° → applying affine correction")
            else:
                notes.append(
                    f"Tilt {tilt_angle:.1f}° below threshold ({self.tilt_threshold}°) — skipped")
                tilt_angle = 0.0

        # ── Step 5: apply tilt correction ─────────────────────────────────
        inv_matrix = None
        if abs(tilt_angle) > self.tilt_threshold:
            cx, cy = ww // 2, wh // 2
            M      = cv2.getRotationMatrix2D((cx, cy), tilt_angle, 1.0)

            # Expand canvas so content isn't cropped
            cos_a  = abs(np.cos(np.radians(tilt_angle)))
            sin_a  = abs(np.sin(np.radians(tilt_angle)))
            new_w  = int(wh * sin_a + ww * cos_a)
            new_h  = int(wh * cos_a + ww * sin_a)
            M[0, 2] += (new_w / 2) - cx
            M[1, 2] += (new_h / 2) - cy

            working    = cv2.warpAffine(
                working, M, (new_w, new_h),
                borderValue=self.bg_fill)

            # Build inverse (for back-projecting output contours)
            M_inv      = cv2.getRotationMatrix2D(
                (new_w / 2, new_h / 2), -tilt_angle, 1.0)
            M_inv[0, 2] += cx - (new_w / 2)
            M_inv[1, 2] += cy - (new_h / 2)
            inv_matrix  = M_inv

        total_rotation = coarse_angle + tilt_angle
        canvas_h, canvas_w = working.shape[:2]
        notes.append(f"Total rotation applied: {total_rotation:.1f}°")

        logger.info(
            f"OrientationDetector: {orientation}, coarse={coarse_angle}°, "
            f"tilt={tilt_angle:.1f}°, total={total_rotation:.1f}°, "
            f"canvas={canvas_w}×{canvas_h}")

        return OrientationResult(
            orientation    = orientation,
            coarse_angle   = coarse_angle,
            tilt_angle     = tilt_angle,
            total_rotation = total_rotation,
            rotated_image  = working,
            original_shape = (orig_h, orig_w),
            canvas_shape   = (canvas_h, canvas_w),
            inverse_matrix = inv_matrix,
            notes          = notes,
        )


# ── Adaptive body threshold helper ──────────────────────────────────────────

def adaptive_body_threshold(row_widths: np.ndarray) -> float:
    """
    Estimate body-row threshold from the row-width profile.

    The neck produces narrow rows; the body produces wide rows.
    Using lower-quartile-of-nonzero * 2.5 separates them robustly,
    replacing the fixed 40%-of-image-width used by BodyIsolator.

    Critical for rotated images: after 90° CCW the image width no longer
    correlates with guitar body width, so any fixed fraction will fail.

    The result is capped at 85% of max row width to prevent the threshold
    from exceeding actual row widths when the silhouette is near-full-width
    (e.g. dark backgrounds where BG and instrument merge in thresholding).

    Parameters
    ----------
    row_widths : 1-D array of per-row instrument pixel counts

    Returns
    -------
    threshold in pixels
    """
    nonzero = row_widths[row_widths > 20]
    if len(nonzero) == 0:
        return float(row_widths.max() * 0.4)
    neck_px = float(np.percentile(nonzero, 25))   # lower quartile ≈ neck width
    raw_threshold = neck_px * 2.5
    cap = float(row_widths.max()) * 0.85           # never exceed 85% of widest row
    return min(raw_threshold, cap)


# ── Contour back-projection ──────────────────────────────────────────────────

def rotate_contours_back(
    contours:        "Dict[str, List[np.ndarray]]",
    orient_result:   OrientationResult,
) -> "Dict[str, List[np.ndarray]]":
    """
    Rotate SVG/DXF contour point arrays back to the original image frame.

    Call this on export_contours just before write_svg() / write_dxf().

    Parameters
    ----------
    contours       : dict of layer_name → list of (N, 2) float arrays (mm coords)
    orient_result  : the OrientationResult from OrientationDetector

    Returns
    -------
    Same structure with coordinates rotated back.

    Notes
    -----
    Since the final contour coordinates are in mm (centred on body),
    this function applies the inverse rotation about the centroid of all
    points.  If you need pixel-frame coordinates, convert mpp first.
    """
    if orient_result.total_rotation == 0:
        return contours

    # Collect all points to find centroid
    all_pts = []
    for pts_list in contours.values():
        for pts in pts_list:
            all_pts.append(pts)
    if not all_pts:
        return contours

    combined = np.vstack(all_pts)
    cx = float(combined[:, 0].mean())
    cy = float(combined[:, 1].mean())

    angle_rad = np.radians(-orient_result.total_rotation)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    rotated: "Dict[str, List[np.ndarray]]" = {}
    for layer, pts_list in contours.items():
        rotated[layer] = []
        for pts in pts_list:
            dx = pts[:, 0] - cx
            dy = pts[:, 1] - cy
            rx = cx + dx * cos_a - dy * sin_a
            ry = cy + dx * sin_a + dy * cos_a
            rotated[layer].append(np.stack([rx, ry], axis=1))

    return rotated


# ── Integration notes ────────────────────────────────────────────────────────

INTEGRATION_NOTES = """
In PhotoVectorizerV2.__init__(), add:
    from patch_06_orientation_detector import OrientationDetector
    self.orientation_detector = OrientationDetector()

In PhotoVectorizerV2._extract_image() / extract(), BEFORE Stage 0:
    # --- NEW: orientation detection (before dark-bg inversion) ---
    orient = self.orientation_detector.detect_and_correct(
        image, is_dark_bg=False)  # pass pre-inversion image
    if orient.total_rotation != 0:
        image = orient.rotated_image
        result.warnings.append(
            f"Orientation corrected: {orient.orientation}, "
            f"{orient.total_rotation:.1f}° rotation applied")
    # -------------------------------------------------------------

Then AFTER Stage 11 (export), before returning result:
    if orient.total_rotation != 0 and export_contours:
        from patch_06_orientation_detector import rotate_contours_back
        export_contours = rotate_contours_back(export_contours, orient)
        # Re-write SVG/DXF with back-projected coordinates
        if export_svg:
            write_svg(export_contours, result.output_svg, svg_w, svg_h)
        if export_dxf:
            write_dxf(export_contours, result.output_dxf, self.dxf_version)

Store on result for downstream use:
    result.orientation        = orient.orientation
    result.rotation_applied   = orient.total_rotation
"""


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    test_cases = [
        ("/mnt/user-data/uploads/Flamed_maple_acoustic_guitar_details.png",
         False, "Flamed maple landscape"),
        ("/mnt/user-data/uploads/Jumbo_Tiger_Maple_Archtop_Guitar_with_a_Florentine_Cutaway.png",
         True, "Archtop dark bg portrait"),
        ("/mnt/user-data/uploads/32c946b6334a.png",
         False, "Two-guitar render"),
    ]
    if len(sys.argv) > 1:
        test_cases = [(p, False, p.split("/")[-1]) for p in sys.argv[1:]]

    detector = OrientationDetector()

    for path, dark_bg, label in test_cases:
        img = cv2.imread(path)
        if img is None:
            print(f"\nCould not load: {path}")
            continue

        h, w = img.shape[:2]
        print(f"\n{'='*60}")
        print(f"{label}  ({w}×{h})")

        result = detector.detect_and_correct(img, is_dark_bg=dark_bg)

        print(f"  Orientation:     {result.orientation}")
        print(f"  Coarse rotation: {result.coarse_angle}°")
        print(f"  Tilt correction: {result.tilt_angle:.1f}°")
        print(f"  Total rotation:  {result.total_rotation:.1f}°")
        rh, rw2 = result.canvas_shape
        print(f"  Canvas:          {rw2}×{rh}")
        for note in result.notes:
            print(f"  Note: {note}")

        # Test BodyIsolator on corrected image
        gray_r  = cv2.cvtColor(result.rotated_image, cv2.COLOR_BGR2GRAY)
        _, thr  = cv2.threshold(gray_r, 200, 255, cv2.THRESH_BINARY_INV)
        rw_arr  = np.sum(thr > 0, axis=1).astype(float)
        k       = np.ones(30) / 30   # wider kernel for rotated images
        sm      = np.convolve(rw_arr, k, mode="same")
        bmin    = adaptive_body_threshold(rw_arr)
        brows   = np.where(sm >= bmin)[0]
        if brows.size:
            bs, be  = brows[0], brows[-1]
            bh_px   = be - bs
            mpp     = 520 / bh_px
            bw_mm   = int(sm[bs:be].max() * mpp)
            print(f"\n  BodyIsolator result:")
            print(f"    rows {bs}–{be} = {bh_px}px")
            print(f"    mpp={mpp:.4f}  body_width={bw_mm}mm  (expected ~400–450mm)")
        else:
            print(f"\n  BodyIsolator: no body rows found at threshold {bmin:.0f}px")

        # Save preview
        out_path = f"/tmp/orientation_{label.replace(' ','_')}.jpg"
        cv2.imwrite(out_path, result.rotated_image)
        print(f"  Preview: {out_path}")
