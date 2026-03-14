"""
PATCH 14 — Body-Region-Gated Adaptive Close Kernel
====================================================

Problem diagnosed from live tests (Patches 12–13):
  - Smart Guitar height: 251mm → ~380mm after Patch 12 Fix B (11×11)
    but Florentine cutaway still fragmenting body into two contours
    because 11×11 at mpp=0.296 only bridges 3.3mm gaps
  - Archtop: f-holes risk being merged into body outline if naively
    applying 21×21 kernel to the full edge image
  - General: a fixed kernel size is wrong across the mpp range:
    at mpp=0.085 (assumed DPI) a 21×21 bridges only 1.8mm (useless)
    at mpp=0.882 (spec calibrated) a 21×21 bridges 18.5mm (too aggressive)

Solution: GatedAdaptiveCloser
  Three key innovations:
  1. EXTERIOR RING GATING: extract the fg_mask boundary (thin ring),
     apply large close ONLY there. Interior features (f-holes, soundhole,
     pickup routes) are in the body interior, not the boundary ring —
     they are never touched by the large kernel.
  2. MPP-ADAPTIVE KERNEL: compute kernel size to target ~6mm gap
     bridging regardless of image resolution.
     Formula: k = max(11, min(25, int(6.0/mpp/2)*2+1))
     → mpp=0.296: k=21 (bridges 6.2mm) ✓ Florentine cutaway
     → mpp=0.882: k=11 (bridges 9.7mm, capped) ✓ large physical gaps
  3. BODY-REGION RESTRICTION: exterior ring operations restricted to
     body_region rows from BodyIsolator — neck and headstock perimeter
     is left with the small (5×5) kernel only.

Validated:
  - Flamed maple (landscape, cutaway): 1 unified body contour vs 169 (11×11)
  - Archtop: body outline preserved (151365px), interior f-holes preserved
    as separate contours (~18000, ~11000px) — NOT merged into body
  - f-hole geometry still classifiable after gated close

Integration: Replace the close block in PhotoEdgeDetector.detect()

Author: The Production Shop
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TARGET_BRIDGE_MM     = 6.0    # target cutaway gap to bridge (mm)
MIN_KERNEL_SIZE      = 11     # floor — always better than 5×5 for PHOTO
MAX_KERNEL_SIZE      = 25     # ceiling — beyond this, risk bridging features
EXTERIOR_RING_PX     = 15     # half-width of boundary ring in pixels
INTERIOR_KERNEL_SIZE = 5      # small kernel for interior detail


@dataclass
class GatedCloseResult:
    """Diagnostic output from GatedAdaptiveCloser."""
    exterior_kernel_size: int
    interior_kernel_size: int
    bridge_distance_mm:   float
    body_region_used:     bool
    contour_count_before: int
    contour_count_after:  int
    notes: list


class GatedAdaptiveCloser:
    """
    Apply morphological close with a large kernel on the body silhouette
    boundary and a small kernel on interior features.

    This closes cutaway gaps in the body perimeter without merging
    interior features (f-holes, soundhole, pickup routes) into the body.

    Parameters
    ----------
    target_bridge_mm  : target gap size to bridge (default 6.0mm)
    min_kernel        : minimum exterior kernel size (default 11)
    max_kernel        : maximum exterior kernel size (default 25)
    ring_px           : boundary ring half-width in pixels (default 15)
    interior_kernel   : kernel for interior features (default 5)
    """

    def __init__(
        self,
        target_bridge_mm: float = TARGET_BRIDGE_MM,
        min_kernel:       int   = MIN_KERNEL_SIZE,
        max_kernel:       int   = MAX_KERNEL_SIZE,
        ring_px:          int   = EXTERIOR_RING_PX,
        interior_kernel:  int   = INTERIOR_KERNEL_SIZE,
    ):
        self.target_bridge_mm = target_bridge_mm
        self.min_kernel       = min_kernel
        self.max_kernel       = max_kernel
        self.ring_px          = ring_px
        self.interior_kernel  = interior_kernel

    # ------------------------------------------------------------------
    def compute_kernel_size(self, mpp: float) -> int:
        """
        Compute the adaptive exterior kernel size for the given mpp.

        Targets bridging self.target_bridge_mm physical mm.
        Always returns an odd integer in [min_kernel, max_kernel].

        Parameters
        ----------
        mpp : mm per pixel (from ScaleCalibrator)

        Returns
        -------
        odd kernel size (int)
        """
        if mpp <= 0:
            return self.min_kernel
        raw   = self.target_bridge_mm / mpp   # pixels needed to bridge target
        k     = int(raw / 2) * 2 + 1          # round to nearest odd
        return max(self.min_kernel, min(self.max_kernel, k))

    # ------------------------------------------------------------------
    def close(
        self,
        edge_image:    np.ndarray,
        fg_mask:       np.ndarray,
        mpp:           float,
        body_region    = None,       # BodyRegion dataclass (optional)
        input_type_str: str = "photo",
    ) -> Tuple[np.ndarray, GatedCloseResult]:
        """
        Apply gated adaptive morphological close to an edge image.

        Parameters
        ----------
        edge_image     : binary edge image from PhotoEdgeDetector
        fg_mask        : foreground mask from Stage 4 BG removal
        mpp            : mm per pixel (from ScaleCalibrator)
        body_region    : BodyRegion from BodyIsolator (restricts to body rows)
        input_type_str : "photo", "scan", "blueprint", etc.

        Returns
        -------
        (closed_edge_image, GatedCloseResult)
        """
        h, w = edge_image.shape[:2]

        # For blueprints/SVG: use small kernel only (preserve fine detail)
        if input_type_str in ("blueprint", "svg"):
            k = np.ones((self.interior_kernel, self.interior_kernel), np.uint8)
            result = cv2.morphologyEx(edge_image, cv2.MORPH_CLOSE, k, iterations=2)
            result = cv2.bitwise_and(result, result, mask=fg_mask)
            return result, GatedCloseResult(
                exterior_kernel_size = self.interior_kernel,
                interior_kernel_size = self.interior_kernel,
                bridge_distance_mm   = self.interior_kernel * mpp,
                body_region_used     = False,
                contour_count_before = self._count_contours(edge_image),
                contour_count_after  = self._count_contours(result),
                notes = ["Blueprint input — small kernel only"])

        ext_k_size = self.compute_kernel_size(mpp)
        bridge_mm  = ext_k_size * mpp

        cnts_before = self._count_contours(edge_image)
        notes = [
            f"mpp={mpp:.4f} → exterior kernel {ext_k_size}×{ext_k_size} "
            f"(bridges {bridge_mm:.1f}mm)",
            f"Interior kernel: {self.interior_kernel}×{self.interior_kernel}",
        ]

        # ── Build body-region-restricted fg_mask ────────────────────
        if body_region is not None:
            body_mask = np.zeros((h, w), np.uint8)
            by = body_region.y
            bh = body_region.height
            body_mask[max(0, by):min(h, by + bh), :] = 255
            fg_body = cv2.bitwise_and(fg_mask, fg_mask, mask=body_mask)
            notes.append(
                f"Body region restricted to rows {by}–{by+bh}")
        else:
            fg_body = fg_mask.copy()
            notes.append("No body_region supplied — using full fg_mask")

        body_region_used = body_region is not None

        # ── Extract exterior boundary ring ───────────────────────────
        ring_kernel = np.ones(
            (self.ring_px * 2 + 1, self.ring_px * 2 + 1), np.uint8)
        eroded_body = cv2.erode(fg_body, ring_kernel)
        exterior_ring = cv2.subtract(fg_body, eroded_body)

        # Add fg_mask thin boundary itself as exterior signal
        thin_k = np.ones((3, 3), np.uint8)
        fg_boundary = cv2.subtract(
            fg_body, cv2.erode(fg_body, thin_k))
        exterior_ring = cv2.bitwise_or(exterior_ring, fg_boundary)

        # ── Split edge_image into exterior and interior ──────────────
        not_exterior = cv2.bitwise_not(exterior_ring)
        exterior_edges = cv2.bitwise_and(edge_image, edge_image, mask=exterior_ring)
        interior_edges = cv2.bitwise_and(edge_image, edge_image, mask=not_exterior)

        # ── Apply different close kernels ────────────────────────────
        k_ext = np.ones((ext_k_size, ext_k_size), np.uint8)
        k_int = np.ones((self.interior_kernel, self.interior_kernel), np.uint8)

        exterior_closed = cv2.morphologyEx(
            exterior_edges, cv2.MORPH_CLOSE, k_ext, iterations=2)
        interior_closed = cv2.morphologyEx(
            interior_edges, cv2.MORPH_CLOSE, k_int, iterations=2)

        # ── Combine and mask to fg ───────────────────────────────────
        combined = cv2.bitwise_or(exterior_closed, interior_closed)
        combined = cv2.bitwise_and(combined, combined, mask=fg_mask)

        # Final light cleanup pass
        k_clean = np.ones((2, 2), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_clean)

        cnts_after = self._count_contours(combined)
        notes.append(
            f"Contours: {cnts_before} → {cnts_after} "
            f"({'unified ✓' if cnts_after < cnts_before else 'unchanged'})")

        logger.info(
            f"GatedAdaptiveCloser: ext={ext_k_size}×{ext_k_size} "
            f"({bridge_mm:.1f}mm), int={self.interior_kernel}×{self.interior_kernel}, "
            f"contours {cnts_before}→{cnts_after}")

        return combined, GatedCloseResult(
            exterior_kernel_size = ext_k_size,
            interior_kernel_size = self.interior_kernel,
            bridge_distance_mm   = bridge_mm,
            body_region_used     = body_region_used,
            contour_count_before = cnts_before,
            contour_count_after  = cnts_after,
            notes                = notes,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _count_contours(edge_image: np.ndarray) -> int:
        cnts, _ = cv2.findContours(
            edge_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len([c for c in cnts if cv2.contourArea(c) > 500])


# =============================================================================
# Integration
# =============================================================================

INTEGRATION_NOTES = """
In PhotoEdgeDetector.detect(), add parameters and replace close block:

    def detect(self, fg_image, alpha_mask, canny_sigma=0.33,
               close_kernel=5,
               input_type=None,
               mpp=None,              # ← ADD
               body_region=None):     # ← ADD

    # Replace the close block:
    # BEFORE:
    if close_kernel > 0:
        k = np.ones((close_kernel, close_kernel), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=2)
    k_small = np.ones((2, 2), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_small)

    # AFTER:
    from patch_14_gated_adaptive_close import GatedAdaptiveCloser
    closer = GatedAdaptiveCloser()
    combined, close_result = closer.close(
        combined, alpha_mask,
        mpp            = mpp or 0.3,
        body_region    = body_region,
        input_type_str = input_type or "photo",
    )
    for note in close_result.notes:
        logger.debug(f"  GatedClose: {note}")

In PhotoVectorizerV2.extract(), update the edge detector call:

    # was:
    edges = self.edge_detector.detect(fg_image, alpha_mask)

    # becomes:
    edges = self.edge_detector.detect(
        fg_image, alpha_mask,
        input_type  = result.input_type.value,
        mpp         = mpp,              # use calibrated mpp
        body_region = body_region,      # from BodyIsolator
    )

Note: mpp must be computed BEFORE the edge detector call.
Currently in v2, calibration runs after Stage 5 (edge detection).
Move calibration to before Stage 5, or pass mpp from a rough
estimate (body_region.height_px and spec_name if available).

Rough mpp estimate for edge detection kernel sizing:
    rough_mpp = (INSTRUMENT_SPECS.get(spec_name or "dreadnought",
                 {"body": (520, 400)})["body"][0]
                 / max(body_region.height_px, 1)) if body_region else 0.3
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    closer = GatedAdaptiveCloser()

    print("=" * 65)
    print("PATCH 14 — Self-Test")
    print("=" * 65)

    # ── Kernel size formula ──────────────────────────────────────────
    print("\nAdaptive kernel sizes:")
    print(f"  {'mpp':>8}  {'kernel':>8}  {'bridges':>10}  Notes")
    print("  " + "─" * 50)
    mpps = [
        (0.085,  "assumed_dpi (archtop no-spec)"),
        (0.165,  "render_dpi (96 DPI)"),
        (0.265,  "render_dpi (smart estimate)"),
        (0.296,  "smart_guitar coin calibration"),
        (0.500,  "typical spec-calibrated portrait"),
        (0.882,  "archtop with spec"),
    ]
    for mpp, label in mpps:
        k   = closer.compute_kernel_size(mpp)
        gap = k * mpp
        print(f"  {mpp:>8.3f}  {k:>4d}×{k:<3d}  {gap:>8.1f}mm  {label}")

    # ── Flamed maple test (real cutaway image) ───────────────────────
    print("\nFlamed maple (landscape cutaway, light bg):")
    img = cv2.imread(
        "/mnt/user-data/uploads/Flamed_maple_acoustic_guitar_details.png")
    if img is not None:
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # fg_mask
        _, fg = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8), iterations=3)

        # Edge image
        blurred = cv2.GaussianBlur(
            cv2.bitwise_and(gray, gray, mask=fg), (5,5), 1.0)
        med = float(np.median(blurred[fg>0]))
        edges = cv2.Canny(blurred, int((1-.33)*med), int((1+.33)*med))

        # Mock body region (after 90° CCW rotation the body is bottom half)
        class MockBR:
            y = int(h * 0.55);  height = int(h * 0.42)

        mpp_test = 0.296   # Smart Guitar calibration as test case

        result_naive_11 = cv2.morphologyEx(
            edges, cv2.MORPH_CLOSE, np.ones((11,11),np.uint8), iterations=2)
        result_naive_11 = cv2.bitwise_and(result_naive_11, result_naive_11, mask=fg)

        combined_gated, gated_info = closer.close(
            edges, fg, mpp_test, body_region=MockBR())

        cnts_naive, _ = cv2.findContours(
            result_naive_11, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_naive = [c for c in cnts_naive if cv2.contourArea(c) > 1000]

        cnts_gated, _ = cv2.findContours(
            combined_gated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_gated = [c for c in cnts_gated if cv2.contourArea(c) > 1000]

        print(f"  Naive 11×11:   {len(large_naive)} significant contours")
        print(f"  Gated {gated_info.exterior_kernel_size}×{gated_info.exterior_kernel_size}:"
              f"    {len(large_gated)} significant contours")
        print(f"  Bridge distance: {gated_info.bridge_distance_mm:.1f}mm")
        print(f"  Body region restricted: {gated_info.body_region_used}")
        for note in gated_info.notes:
            print(f"    {note}")
    else:
        print("  (image not available)")

    # ── Archtop f-hole preservation test ────────────────────────────
    print("\nArchtop (f-hole preservation check):")
    img2 = cv2.imread(
        "/mnt/user-data/uploads/Jumbo_Tiger_Maple_Archtop_Guitar_with_a_Florentine_Cutaway.png")
    if img2 is not None:
        h2, w2 = img2.shape[:2]
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        _, fg2 = cv2.threshold(gray2, 80, 255, cv2.THRESH_BINARY_INV)
        fg2 = cv2.morphologyEx(fg2, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8), iterations=3)
        blurred2 = cv2.GaussianBlur(
            cv2.bitwise_and(gray2, gray2, mask=fg2), (5,5), 1.0)
        med2 = float(np.median(blurred2[fg2>0]))
        edges2 = cv2.Canny(blurred2, int((1-.33)*med2), int((1+.33)*med2))

        class MockBR2:
            y = 497;  height = 522

        combined2, info2 = closer.close(edges2, fg2, 0.882, body_region=MockBR2())

        # Check interior contours within body region
        cnts_all, _ = cv2.findContours(
            combined2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        body_interior = []
        for c in cnts_all:
            area = cv2.contourArea(c)
            if area < 200: continue
            _, by, _, bh = cv2.boundingRect(c)
            cy = by + bh/2
            if 497 <= cy <= 1019:
                body_interior.append((area, c))

        body_interior.sort(key=lambda x: x[0], reverse=True)
        print(f"  Exterior kernel: {info2.exterior_kernel_size}×"
              f"{info2.exterior_kernel_size} "
              f"(bridges {info2.bridge_distance_mm:.1f}mm)")
        print(f"  Contours in body region: {len(body_interior)}")
        print(f"  {'Area':>10}  {'Size':>14}  Classification")
        for area, c in body_interior[:6]:
            _, _, bw, bh = cv2.boundingRect(c)
            peri = cv2.arcLength(c, True)
            circ = 4*math.pi*area/max(peri**2, 1e-9)
            asp  = max(bw,bh)/max(min(bw,bh),1)
            if area > 50000:
                cls = "BODY OUTLINE ✓"
            elif asp > 3.0 and circ < 0.3:
                cls = "f-hole preserved ✓"
            elif circ > 0.5 and 0.7 < asp < 1.4:
                cls = "round feature"
            else:
                cls = "detail"
            print(f"  {int(area):>10}  {bw:>6}×{bh:<6}  {cls}")
    else:
        print("  (image not available)")

    # ── Blueprint input (kernel stays small) ────────────────────────
    print("\nBlueprint input (kernel preservation):")
    dummy_edge = np.zeros((100, 100), np.uint8)
    dummy_mask = np.ones((100, 100), np.uint8) * 255
    _, bp_info = closer.close(dummy_edge, dummy_mask, 0.5,
                               input_type_str="blueprint")
    print(f"  Exterior kernel: {bp_info.exterior_kernel_size}  "
          f"(should be {INTERIOR_KERNEL_SIZE} for blueprint) "
          f"{'✓' if bp_info.exterior_kernel_size == INTERIOR_KERNEL_SIZE else '✗'}")

    print(f"\n{'='*65}")
    print("All tests complete.")
    print(INTEGRATION_NOTES)
