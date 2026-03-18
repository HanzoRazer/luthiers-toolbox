"""
grid_classify.py — Guitar Body Grid Classifier
===============================================

STATUS: RECONSTRUCTED
  This module was imported by photo_vectorizer_v2.py but never existed on disk.
  The missing import caused a hard ModuleNotFoundError on startup, meaning
  Stage 8.5 (grid zone re-classification) has never executed.

  Reconstructed from the call signatures embedded in photo_vectorizer_v2.py:

    grid_clf = PhotoGridClassifier()
    gc = grid_clf.classify_contour_px(fc.bbox_px, body_bbox_px)
      gc.primary_category  → str
      gc.notes             → List[str]
      gc.grid_confidence   → float

    final_feat, final_conf, reason = merge_classifications(
        fc.feature_type.value, fc.confidence, gc)

    overlay = grid_clf.draw_grid_overlay(
        image, body_bbox_px, contour_bboxes, classifications)

Approach:
  Divide the instrument body into a named grid of zones based on relative
  position within the body bounding box.  Each zone has a strong prior for
  which feature types appear there on a typical guitar body.

  Grid layout (normalized 0.0–1.0 relative to body bbox):

       0.0        0.33       0.67       1.0   ← X (left→right)
  0.0  ┌──────────┬──────────┬──────────┐
       │  UL      │  UC      │  UR      │  Upper third
  0.33 ├──────────┼──────────┼──────────┤
       │  ML      │  MC      │  MR      │  Middle third
  0.67 ├──────────┼──────────┼──────────┤
       │  LL      │  LC      │  LR      │  Lower third
  1.0  └──────────┴──────────┴──────────┘

  Zone → feature priors (for electric guitar orientation, body at bottom):
    UL/UC/UR  → NECK_POCKET, BINDING
    ML/MR     → PICKUP_ROUTE, F_HOLE
    MC        → SOUNDHOLE, ROSETTE
    LL/LR     → PICKUP_ROUTE, CONTROL_CAVITY, JACK_ROUTE
    LC        → BRIDGE_ROUTE, CONTROL_CAVITY

  The grid result is then merged with the dimension-based FeatureClassifier
  result via merge_classifications().  Grid confidence boosts or overrides
  the dimension result depending on agreement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ── Zone definitions ─────────────────────────────────────────────────────────

# Maps zone name → ordered list of likely FeatureType values (strings matching
# FeatureType.value in photo_vectorizer_v2.py)
_ZONE_PRIORS: Dict[str, List[str]] = {
    # Top row — neck area
    "UL": ["binding", "neck_pocket"],
    "UC": ["neck_pocket", "binding"],
    "UR": ["binding", "neck_pocket"],
    # Middle row — main body region
    "ML": ["pickup_route", "f_hole", "binding"],
    "MC": ["soundhole", "rosette", "pickup_route"],
    "MR": ["pickup_route", "f_hole", "binding"],
    # Lower row — tail area
    "LL": ["pickup_route", "control_cavity", "jack_route"],
    "LC": ["bridge_route", "control_cavity"],
    "LR": ["pickup_route", "control_cavity", "jack_route"],
}

# Confidence boost when grid zone agrees with dimension classifier
_AGREEMENT_BOOST   = 0.15
# Confidence penalty when grid contradicts dimension classifier
_DISAGREEMENT_DROP = 0.10


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class GridClassification:
    """Result of classifying a single contour by body-relative grid position."""
    zone: str                             # e.g. "MC", "LL"
    primary_category: str                 # top FeatureType.value for this zone
    candidates: List[str]                 # all zone priors in order
    relative_x: float                     # 0.0–1.0 within body bbox
    relative_y: float                     # 0.0–1.0 within body bbox
    grid_confidence: float                # 0.0–1.0
    notes: List[str] = field(default_factory=list)


# ── Main classifier ──────────────────────────────────────────────────────────

class PhotoGridClassifier:
    """
    Classifies contours by their position relative to the instrument body
    bounding box using a fixed 3×3 zone grid.

    Parameters
    ----------
    x_splits : tuple
        Normalised x boundaries between columns.  Default (0.33, 0.67).
    y_splits : tuple
        Normalised y boundaries between rows.  Default (0.33, 0.67).
    """

    def __init__(
        self,
        x_splits: Tuple[float, float] = (0.33, 0.67),
        y_splits: Tuple[float, float] = (0.33, 0.67),
    ):
        self.x_splits = x_splits
        self.y_splits = y_splits

    # ------------------------------------------------------------------
    def classify_contour_px(
        self,
        contour_bbox: Tuple[int, int, int, int],
        body_bbox:    Tuple[int, int, int, int],
    ) -> GridClassification:
        """
        Classify a single contour by its position within the body bounding box.

        Parameters
        ----------
        contour_bbox : (x, y, w, h) pixel bounding box of the contour
        body_bbox    : (x, y, w, h) pixel bounding box of the body outline

        Returns
        -------
        GridClassification
        """
        bx, by, bw, bh = body_bbox
        cx, cy, cw, ch = contour_bbox

        # Centre of contour relative to body
        cx_centre = cx + cw / 2.0
        cy_centre = cy + ch / 2.0

        rel_x = (cx_centre - bx) / max(bw, 1)
        rel_y = (cy_centre - by) / max(bh, 1)

        # Clamp to [0, 1] (contour might slightly exceed body bbox)
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))

        # Determine column
        if rel_x < self.x_splits[0]:
            col = "L"
        elif rel_x < self.x_splits[1]:
            col = "C"
        else:
            col = "R"

        # Determine row
        if rel_y < self.y_splits[0]:
            row = "U"
        elif rel_y < self.y_splits[1]:
            row = "M"
        else:
            row = "L"

        zone = row + col
        priors = _ZONE_PRIORS.get(zone, ["unknown"])
        primary = priors[0]

        # Confidence based on how centred the contour is within its zone
        zone_x_centre, zone_y_centre = self._zone_centre(zone)
        dist = np.sqrt((rel_x - zone_x_centre) ** 2 + (rel_y - zone_y_centre) ** 2)
        confidence = max(0.30, 1.0 - dist * 2.0)

        notes = [
            f"Zone {zone}: rel=({rel_x:.2f}, {rel_y:.2f})",
            f"Priors: {priors}",
        ]

        return GridClassification(
            zone=zone,
            primary_category=primary,
            candidates=priors,
            relative_x=rel_x,
            relative_y=rel_y,
            grid_confidence=round(confidence, 3),
            notes=notes,
        )

    # ------------------------------------------------------------------
    def draw_grid_overlay(
        self,
        image:           np.ndarray,
        body_bbox:       Tuple[int, int, int, int],
        contour_bboxes:  List[Tuple[int, int, int, int]],
        classifications: List[GridClassification],
    ) -> np.ndarray:
        """
        Draw the 3×3 grid and zone-classified contours onto a copy of the image.

        Returns annotated image (BGR).
        """
        out = image.copy()
        bx, by, bw, bh = body_bbox

        # Draw body bbox
        cv2.rectangle(out, (bx, by), (bx + bw, by + bh), (0, 200, 0), 2)

        # Draw grid lines
        for xf in self.x_splits:
            x = int(bx + xf * bw)
            cv2.line(out, (x, by), (x, by + bh), (0, 200, 0), 1)
        for yf in self.y_splits:
            y = int(by + yf * bh)
            cv2.line(out, (bx, y), (bx + bw, y), (0, 200, 0), 1)

        # Draw zone labels
        _ZONE_COLS = {"L": 0, "C": 1, "R": 2}
        _ZONE_ROWS = {"U": 0, "M": 1, "L": 2}
        col_bounds = [0.0] + list(self.x_splits) + [1.0]
        row_bounds = [0.0] + list(self.y_splits) + [1.0]
        for zone, priors in _ZONE_PRIORS.items():
            row_key, col_key = zone[0], zone[1]
            ri = _ZONE_ROWS[row_key]
            ci = _ZONE_COLS[col_key]
            lx = int(bx + col_bounds[ci] * bw)
            ly = int(by + row_bounds[ri] * bh)
            cv2.putText(out, f"{zone}:{priors[0][:3]}",
                        (lx + 4, ly + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 180, 0), 1,
                        cv2.LINE_AA)

        # Draw each classified contour bbox
        zone_colors = {
            "UL": (255, 100, 0), "UC": (255, 140, 0), "UR": (255, 100, 0),
            "ML": (0, 120, 255), "MC": (0,  60, 255), "MR": (0, 120, 255),
            "LL": (0, 200, 200), "LC": (0, 160, 200), "LR": (0, 200, 200),
        }
        for bbox, gc in zip(contour_bboxes, classifications):
            x, y, w, h = bbox
            color = zone_colors.get(gc.zone, (180, 180, 180))
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 1)
            label = f"{gc.primary_category[:4]} {gc.grid_confidence:.1f}"
            cv2.putText(out, label, (x, y - 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.30, color, 1, cv2.LINE_AA)

        return out

    # ------------------------------------------------------------------
    def _zone_centre(self, zone: str) -> Tuple[float, float]:
        """Return normalised (x, y) centre of a zone."""
        col_bounds = [0.0] + list(self.x_splits) + [1.0]
        row_bounds = [0.0] + list(self.y_splits) + [1.0]
        col_map = {"L": 0, "C": 1, "R": 2}
        row_map = {"U": 0, "M": 1, "L": 2}
        ci = col_map.get(zone[1], 1)
        ri = row_map.get(zone[0], 1)
        cx = (col_bounds[ci] + col_bounds[ci + 1]) / 2.0
        cy = (row_bounds[ri] + row_bounds[ri + 1]) / 2.0
        return cx, cy


# ── merge_classifications ────────────────────────────────────────────────────

def merge_classifications(
    dim_feature:  str,
    dim_conf:     float,
    grid_result:  GridClassification,
) -> Tuple[str, float, str]:
    """
    Merge the dimension-based FeatureClassifier result with the grid-based
    GridClassification result.

    Logic:
      - If both agree   → keep feature, boost confidence
      - If grid unknown → keep dimension result as-is
      - If dim unknown  → promote grid primary category
      - If disagreement → keep higher-confidence source, slight penalty

    Parameters
    ----------
    dim_feature  : FeatureType.value string from FeatureClassifier
    dim_conf     : confidence from FeatureClassifier (0–1)
    grid_result  : GridClassification from PhotoGridClassifier

    Returns
    -------
    (final_feature_str, final_confidence, reason_str)
    """
    grid_primary = grid_result.primary_category
    grid_conf    = grid_result.grid_confidence

    # Both unknown — nothing to do
    if dim_feature == "unknown" and grid_primary == "unknown":
        return "unknown", min(dim_conf, grid_conf), "both unknown"

    # Dimension classifier didn't fire — use grid
    if dim_feature == "unknown":
        return grid_primary, grid_conf * 0.8, f"dim=unknown → grid({grid_primary})"

    # Grid doesn't have a strong prior for this zone
    if grid_primary == "unknown":
        return dim_feature, dim_conf, "grid unknown → keep dim"

    # Agreement
    if dim_feature == grid_primary or dim_feature in grid_result.candidates:
        boosted = min(1.0, max(dim_conf, grid_conf) + _AGREEMENT_BOOST)
        return dim_feature, boosted, f"agree({dim_feature}) → +{_AGREEMENT_BOOST:.2f}"

    # Disagreement: pick the more confident source
    if dim_conf >= grid_conf:
        penalised = max(0.0, dim_conf - _DISAGREEMENT_DROP)
        reason = (f"disagree: dim={dim_feature}({dim_conf:.2f}) "
                  f"vs grid={grid_primary}({grid_conf:.2f}) → dim wins")
        return dim_feature, penalised, reason
    else:
        penalised = max(0.0, grid_conf - _DISAGREEMENT_DROP)
        reason = (f"disagree: dim={dim_feature}({dim_conf:.2f}) "
                  f"vs grid={grid_primary}({grid_conf:.2f}) → grid wins")
        return grid_primary, penalised, reason


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Simulate a guitar image: body bbox covers bottom 60% of a 1024x1024 image
    body_bbox = (50, 400, 450, 580)   # x, y, w, h

    test_contours = [
        # (bbox,                   expected zone, note)
        ((160, 420, 70, 35),      "UC",  "neck pocket"),
        ((100, 560, 80, 35),      "ML",  "neck pickup"),
        ((160, 560, 80, 35),      "MC",  "middle pickup / soundhole"),
        ((220, 560, 80, 35),      "MR",  "bridge pickup"),
        ((100, 720, 120, 80),     "LL",  "control cavity"),
        ((160, 730, 90, 25),      "LC",  "bridge route"),
        ((460, 600,  20, 20),     "LR",  "jack route"),
    ]

    clf = PhotoGridClassifier()

    print(f"\n{'Contour':<30} {'Zone':<5} {'Primary':<20} {'Conf':<6} Notes")
    print("-" * 80)
    for bbox, expected, label in test_contours:
        gc = clf.classify_contour_px(bbox, body_bbox)
        match = "✓" if gc.zone == expected else f"✗(exp {expected})"
        print(f"  {label:<28} {gc.zone:<5} {gc.primary_category:<20} "
              f"{gc.grid_confidence:<6.2f} {match}")

    print("\nmerge_classifications tests:")
    cases = [
        ("pickup_route", 0.75, "ML",  "pickup_route", "should agree+boost"),
        ("unknown",      0.30, "LC",  "bridge_route", "dim unknown, use grid"),
        ("neck_pocket",  0.80, "LC",  "bridge_route", "disagreement, dim wins"),
        ("bridge_route", 0.40, "ML",  "pickup_route", "disagreement, grid wins"),
    ]
    for dim_f, dim_c, zone, expected_f, label in cases:
        gc = GridClassification(zone=zone, primary_category=_ZONE_PRIORS[zone][0],
                                candidates=_ZONE_PRIORS[zone],
                                relative_x=0.5, relative_y=0.5,
                                grid_confidence=0.70)
        feat, conf, reason = merge_classifications(dim_f, dim_c, gc)
        ok = "✓" if feat == expected_f else f"✗(got {feat})"
        print(f"  {label:<40} → {feat:<20} conf={conf:.2f}  {ok}")

    # Live image test if provided
    if len(sys.argv) > 1:
        img = cv2.imread(sys.argv[1])
        if img is not None:
            h, w = img.shape[:2]
            body_bbox_live = (int(w*0.05), int(h*0.35), int(w*0.90), int(h*0.60))
            bboxes = [(int(w*0.1)+i*50, int(h*0.4)+i*30, 60, 30) for i in range(5)]
            gcs    = [clf.classify_contour_px(b, body_bbox_live) for b in bboxes]
            overlay = clf.draw_grid_overlay(img, body_bbox_live, bboxes, gcs)
            out_path = "/tmp/grid_overlay_test.jpg"
            cv2.imwrite(out_path, overlay)
            print(f"\nOverlay saved: {out_path}")
