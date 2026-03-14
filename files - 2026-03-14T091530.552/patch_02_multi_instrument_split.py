"""
PATCH 02 — Multi-Instrument Image Splitter
==========================================

Problem diagnosed:
  - Image contains TWO guitars side by side (front + back view)
  - GrabCut rect covers both → only 33% foreground coverage
  - ContourAssembler elects ONE body (largest) and drops the other
  - Pipeline returns one guitar outline, silently ignores the second

Fix:
  MultiInstrumentSplitter runs BEFORE Stage 3 (perspective correction).
  It detects vertical or horizontal gap(s) in the image and returns
  individual crop regions. The caller loops over crops, running the
  full pipeline on each, and collects results.

  Detection strategy:
    1. Compute column-wise mean brightness (vertical split detection)
       and row-wise mean brightness (horizontal split detection)
    2. Find contiguous bright bands (background gap between instruments)
    3. If a gap is found, return crop bounding boxes
    4. If no gap found, return [(0, 0, w, h)] (single instrument, no split)

Usage (see integration note at bottom):
    splitter = MultiInstrumentSplitter()
    crops = splitter.detect_and_split(image)
    # crops → list of (x, y, w, h) tuples

    for i, (cx, cy, cw, ch) in enumerate(crops):
        crop_img = image[cy:cy+ch, cx:cx+cw]
        result = vectorizer.extract_from_array(crop_img, ...)
        result.source_path = f"{stem}_instrument_{i+1}"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SplitResult:
    crops: List[Tuple[int, int, int, int]]   # (x, y, w, h) per instrument
    split_axis: Optional[str] = None          # "vertical" | "horizontal" | None
    gap_positions: List[int] = field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.crops)

    @property
    def is_multi(self) -> bool:
        return len(self.crops) > 1


class MultiInstrumentSplitter:
    """
    Detects whether an image contains multiple instruments and
    returns crop coordinates for each one.

    Parameters
    ----------
    bg_brightness_threshold : int
        Pixel brightness above which a column/row is considered "background".
        Default 190 works well for light-grey AI render backgrounds.
    min_gap_width_pct : float
        Minimum gap width as fraction of image dimension to count as a real
        separation (not just a neck or thin instrument region).  Default 0.03.
    margin_px : int
        Pixels to add on each side of each crop for safety.  Default 10.
    max_instruments : int
        Cap on number of splits (prevents over-splitting on noisy images).
    """

    def __init__(
        self,
        bg_brightness_threshold: int = 190,
        min_gap_width_pct: float      = 0.03,
        margin_px: int                = 10,
        max_instruments: int          = 4,
    ):
        self.bg_thresh        = bg_brightness_threshold
        self.min_gap_pct      = min_gap_width_pct
        self.margin           = margin_px
        self.max_instruments  = max_instruments

    # ------------------------------------------------------------------
    def detect_and_split(self, image: np.ndarray) -> SplitResult:
        """
        Main entry point.  Returns a SplitResult with crop boxes.
        If no split is detected, returns one crop covering the full image.
        """
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Try vertical split first (side-by-side, most common)
        v_result = self._find_gaps(gray, axis="vertical")
        if v_result.is_multi:
            logger.info(
                f"MultiInstrumentSplitter: {v_result.count} instruments detected "
                f"(vertical split at columns {v_result.gap_positions})"
            )
            return v_result

        # Try horizontal split (stacked views, less common)
        h_result = self._find_gaps(gray, axis="horizontal")
        if h_result.is_multi:
            logger.info(
                f"MultiInstrumentSplitter: {h_result.count} instruments detected "
                f"(horizontal split at rows {h_result.gap_positions})"
            )
            return h_result

        logger.info("MultiInstrumentSplitter: single instrument detected")
        return SplitResult(
            crops=[(0, 0, w, h)],
            split_axis=None,
            confidence=0.9,
            notes=["No gap detected — treating as single instrument"],
        )

    # ------------------------------------------------------------------
    def _find_gaps(self, gray: np.ndarray, axis: str) -> SplitResult:
        """
        Project image onto one axis and find bright (background) bands.

        axis="vertical"   → project along rows, find column gaps
        axis="horizontal" → project along columns, find row gaps
        """
        h, w = gray.shape[:2]
        dim = w if axis == "vertical" else h
        min_gap_px = max(3, int(dim * self.min_gap_pct))

        # Mean brightness profile along the chosen axis
        if axis == "vertical":
            profile = gray.mean(axis=0)        # shape (w,)
        else:
            profile = gray.mean(axis=1)        # shape (h,)

        # Binary: is this column/row "background"?
        is_bg = (profile >= self.bg_thresh).astype(np.uint8)

        # Find contiguous background runs
        gaps = self._find_runs(is_bg, value=1, min_length=min_gap_px)

        if not gaps:
            return SplitResult(crops=[], confidence=0.0)

        # Build instrument crop boxes from the foreground regions between gaps
        # Foreground regions are everything NOT in a gap
        gap_set = set()
        for start, end in gaps:
            for i in range(start, end + 1):
                gap_set.add(i)

        fg_regions = self._find_runs(is_bg, value=0, min_length=min_gap_px * 2)

        if len(fg_regions) < 2:
            return SplitResult(crops=[], confidence=0.0)

        # Cap to max_instruments
        fg_regions = fg_regions[:self.max_instruments]

        crops = []
        for (start, end) in fg_regions:
            s = max(0, start - self.margin)
            e = min(dim - 1, end + self.margin)
            if axis == "vertical":
                crops.append((s, 0, e - s, h))            # (x, y, w, h)
            else:
                crops.append((0, s, w, e - s))            # (x, y, w, h)

        gap_centers = [(s + e) // 2 for s, e in gaps]
        conf = min(1.0, 0.5 + 0.1 * len(gaps))

        notes = [
            f"Found {len(gaps)} background gap(s) along {axis} axis",
            f"Gap width threshold: {min_gap_px}px",
            f"Instrument regions: {len(crops)}",
        ]

        return SplitResult(
            crops=crops,
            split_axis=axis,
            gap_positions=gap_centers,
            confidence=conf,
            notes=notes,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _find_runs(
        arr: np.ndarray, value: int, min_length: int
    ) -> List[Tuple[int, int]]:
        """Return list of (start, end) index pairs for runs of `value`."""
        runs = []
        in_run = False
        start = 0
        for i, v in enumerate(arr):
            if v == value and not in_run:
                in_run = True
                start = i
            elif v != value and in_run:
                in_run = False
                if (i - start) >= min_length:
                    runs.append((start, i - 1))
        if in_run and (len(arr) - start) >= min_length:
            runs.append((start, len(arr) - 1))
        return runs


# ── Convenience wrapper ──────────────────────────────────────────────────────

def split_if_multi(image: np.ndarray, **kwargs) -> SplitResult:
    """One-liner helper for quick use."""
    return MultiInstrumentSplitter(**kwargs).detect_and_split(image)


# ── Integration notes ────────────────────────────────────────────────────────
INTEGRATION_NOTES = """
Step 1 — Add extract_from_array() to PhotoVectorizerV2
-------------------------------------------------------
Refactor the core of extract() so it accepts a pre-loaded np.ndarray in
addition to a file path.  Simplest approach:

    def extract(self, source_path, output_dir=None, **kwargs):
        image = self._load_image(Path(source_path))
        return self._extract_image(image, Path(source_path).stem,
                                   output_dir, **kwargs)

    def extract_from_array(self, image, stem, output_dir=None, **kwargs):
        return self._extract_image(image, stem, output_dir, **kwargs)

    def _extract_image(self, image, stem, output_dir, **kwargs):
        # ... existing body of extract() ...


Step 2 — Add splitting at the top of _extract_image()
------------------------------------------------------
    from patch_02_multi_instrument_split import MultiInstrumentSplitter

    splitter = MultiInstrumentSplitter()
    split = splitter.detect_and_split(image)

    if split.is_multi:
        results = []
        for idx, (cx, cy, cw, ch) in enumerate(split.crops):
            crop = image[cy:cy+ch, cx:cx+cw]
            r = self._extract_image(
                    crop,
                    stem=f"{stem}_instrument_{idx+1}",
                    output_dir=output_dir,
                    **kwargs)
            r.notes = r.warnings  # carry through
            results.append(r)
        return results   # caller gets a list

    # ... continue with single-instrument pipeline ...


Step 3 — Update CLI to handle list results
------------------------------------------
    results = v.extract(args.source, ...)
    if not isinstance(results, list):
        results = [results]
    for r in results:
        print(f"  SVG: {r.output_svg}")
        print(f"  DXF: {r.output_dxf}")
        print(f"  Body: {r.body_dimensions_mm[0]:.1f} x "
              f"{r.body_dimensions_mm[1]:.1f} mm")
"""


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python patch_02_multi_instrument_split.py <image_path>")
        sys.exit(0)

    img = cv2.imread(sys.argv[1])
    if img is None:
        print(f"Could not load: {sys.argv[1]}")
        sys.exit(1)

    result = split_if_multi(img)
    print(f"\nSplit result:")
    print(f"  Instruments: {result.count}")
    print(f"  Axis:        {result.split_axis}")
    print(f"  Confidence:  {result.confidence:.2f}")
    print(f"  Gaps at:     {result.gap_positions}")
    for note in result.notes:
        print(f"  Note: {note}")
    print(f"\nCrops:")
    for i, (x, y, w, h) in enumerate(result.crops):
        print(f"  [{i+1}] x={x} y={y} w={w} h={h}")

    # Save crop previews
    for i, (x, y, w, h) in enumerate(result.crops):
        crop = img[y:y+h, x:x+w]
        out = f"/tmp/crop_{i+1}.jpg"
        cv2.imwrite(out, crop)
        print(f"  Saved: {out}")
