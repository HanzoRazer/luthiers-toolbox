"""
PATCH 03 — Body Isolator: Separate Body from Neck + Headstock
=============================================================

Problem (discovered during calibration testing):
  - spec-based calibration uses body_height_px from the full instrument contour
  - For guitars, this includes neck + headstock, inflating height by ~2x
  - Calibration using full contour: 1003px → 0.518 mm/px → body width 225mm (wrong)
  - Calibration using body-only:     476px → 1.092 mm/px → body width 338mm (much closer)

Fix:
  BodyIsolator uses row-width profiling to find the transition point where
  the narrow neck widens into the body.  Returns the bounding box of the
  body-only region for use in spec calibration.

  This is a pre-calibration step that runs after Stage 4 (BG removal) but
  before Stage 7 (scale calibration).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BodyRegion:
    """Bounding box of the isolated instrument body (excludes neck/headstock)."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    neck_end_row: int          # Row where neck transitions to body
    max_body_width_px: int     # Widest point of the body
    notes: list

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    @property
    def height_px(self) -> int:
        return self.height

    @property
    def width_px(self) -> int:
        return self.width


class BodyIsolator:
    """
    Identifies the body region of a guitar/instrument image by profiling
    row-wise instrument pixel width.

    The neck is narrow and roughly constant width.
    The body is wide and increases then decreases.
    The transition is where width jumps past a threshold.

    Parameters
    ----------
    dark_threshold : int
        Pixel value below which a pixel is considered "instrument" (not background).
    body_width_min_pct : float
        Minimum fraction of image width for a row to be considered "body".
        Default 0.40 = at least 40% of the crop width must be instrument.
    smooth_window : int
        Rolling average window for row-width profile smoothing.
    """

    def __init__(
        self,
        dark_threshold: int      = 150,
        body_width_min_pct: float = 0.40,
        smooth_window: int        = 15,
    ):
        self.dark_thresh      = dark_threshold
        self.body_width_min   = body_width_min_pct
        self.smooth_window    = smooth_window

    def isolate(self, image: np.ndarray,
                fg_mask: Optional[np.ndarray] = None) -> BodyRegion:
        """
        Analyse the image and return a BodyRegion for the guitar body.

        If fg_mask is provided (from Stage 4), uses that instead of
        thresholding the raw image.
        """
        h, w = image.shape[:2]
        notes = []

        # Build row-width profile
        if fg_mask is not None:
            row_widths = np.sum(fg_mask > 0, axis=1).astype(float)
            notes.append("Row widths from fg_mask")
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            binary = (gray < self.dark_thresh).astype(np.uint8)
            row_widths = np.sum(binary, axis=1).astype(float)
            notes.append(f"Row widths from threshold (<{self.dark_thresh})")

        # Smooth the profile to suppress noise
        kernel = np.ones(self.smooth_window) / self.smooth_window
        smoothed = np.convolve(row_widths, kernel, mode='same')

        # Body threshold: rows where instrument is at least body_width_min_pct wide
        body_min_px = w * self.body_width_min
        is_body_row = smoothed >= body_min_px

        # Find the first and last body row
        body_rows = np.where(is_body_row)[0]

        if len(body_rows) == 0:
            # Fallback: use bottom 55% of image as body estimate
            body_start = int(h * 0.45)
            body_end   = int(h * 0.97)
            confidence = 0.30
            notes.append(f"No body rows found at {body_min_px:.0f}px threshold → fallback to bottom 55%")
        else:
            body_start = int(body_rows[0])
            body_end   = int(body_rows[-1])
            confidence = min(1.0, 0.50 + 0.005 * len(body_rows))
            notes.append(
                f"Body rows {body_start}–{body_end} "
                f"({len(body_rows)} rows ≥ {body_min_px:.0f}px wide)"
            )

        body_h = body_end - body_start
        max_body_w = int(smoothed[body_start:body_end].max()) if body_h > 0 else 0

        # Column extent of body region
        if fg_mask is not None:
            body_strip = fg_mask[body_start:body_end, :]
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            body_strip = (gray[body_start:body_end, :] < self.dark_thresh).astype(np.uint8)

        col_widths = np.sum(body_strip > 0, axis=0)
        body_cols = np.where(col_widths > 0)[0]
        x_start = int(body_cols[0])  if len(body_cols) else 0
        x_end   = int(body_cols[-1]) if len(body_cols) else w

        logger.info(
            f"BodyIsolator: body region x={x_start}–{x_end}, "
            f"y={body_start}–{body_end}, "
            f"size={x_end-x_start}x{body_h}px, "
            f"conf={confidence:.2f}"
        )

        return BodyRegion(
            x=x_start,
            y=body_start,
            width=x_end - x_start,
            height=body_h,
            confidence=confidence,
            neck_end_row=body_start,
            max_body_width_px=max_body_w,
            notes=notes,
        )


# ── Integration ──────────────────────────────────────────────────────────────
INTEGRATION_NOTES = """
In PhotoVectorizerV2._extract_image(), after Stage 4 (background removal)
and before Stage 7 (calibration), add:

    from patch_03_body_isolator import BodyIsolator
    isolator = BodyIsolator()
    body_region = isolator.isolate(image, fg_mask=alpha_mask)

    # Pass body_height_px to calibrator (Patch 01)
    calibration = self.calibrator.calibrate(
        image,
        known_mm=known_dimension_mm,
        known_px=known_dimension_px,
        spec_name=spec_name,
        image_dpi=exif_dpi,
        fg_mask=alpha_mask,
        body_height_px=float(body_region.height_px),  # ← NEW
    )

The BodyRegion.bbox can also be used to seed GrabCut's hint_rect,
improving background removal accuracy:

    fg_image, alpha_mask, bg_used = self.bg_remover.remove(
        image,
        method=self.bg_method,
        hint_rect=body_region.bbox,    # ← seeds GrabCut to body area
        is_dark_bg=is_dark_bg,
    )
"""


# ── Self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/32c946b6334a.png"
    img  = cv2.imread(path)

    # First split, then isolate body in each crop
    from patch_02_multi_instrument_split import MultiInstrumentSplitter
    split = MultiInstrumentSplitter().detect_and_split(img)

    isolator = BodyIsolator()

    for i, (cx, cy, cw, ch) in enumerate(split.crops):
        crop = img[cy:cy+ch, cx:cx+cw]
        region = isolator.isolate(crop)

        # Spec calibration
        spec_h_mm = 520.0  # dreadnought
        mpp = spec_h_mm / region.height_px if region.height_px > 0 else 0
        body_w_mm = region.width_px * mpp

        print(f"\nInstrument {i+1}:")
        print(f"  Crop:          {cw}x{ch}px")
        print(f"  Body region:   {region.width_px}x{region.height_px}px "
              f"@ ({region.x},{region.y})")
        print(f"  Confidence:    {region.confidence:.2f}")
        print(f"  mpp (spec):    {mpp:.5f}")
        print(f"  Body dims:     {body_w_mm:.0f} x {spec_h_mm:.0f}mm")
        for note in region.notes:
            print(f"  Note: {note}")

        # Save annotated preview
        preview = crop.copy()
        cv2.rectangle(preview,
                      (region.x, region.y),
                      (region.x + region.width, region.y + region.height),
                      (0, 255, 0), 3)
        out = f"/tmp/body_region_{i+1}.jpg"
        cv2.imwrite(out, preview)
        print(f"  Preview: {out}")
