"""
PATCH 08 — Material BOM Generator
===================================

Downstream of: PhotoVectorizerV2 → PhotoExtractionResult
Input:  PhotoExtractionResult (closed mm-coordinate contours + calibration)
Output: MaterialBOM dataclass → JSON, CSV, human-readable report

Computes:
  - Area per feature layer (BODY_OUTLINE, PICKUP_ROUTE, F_HOLE, etc.)
  - Bounding box dimensions per feature (for stock-size selection)
  - Material assignment per feature type
  - Unit cost estimates (configurable price table)
  - Simple rectangular nesting layout (no rotation — conservative estimate)
  - Waste percentage
  - Total cost estimate with waste factor

Design decisions:
  - Areas computed from shoelace formula on mm contours (exact for polygons)
  - Nesting is axis-aligned bounding-box packing — not optimal but fast and
    conservative (real CAM nesting will always do better)
  - Price table is user-configurable; defaults are ballpark workshop prices
  - No grain direction enforcement here — that is Patch 09's job

Author: The Production Shop
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Default material price table (USD per square mm, configurable)
# ---------------------------------------------------------------------------

DEFAULT_PRICES_USD_PER_SQ_MM: Dict[str, float] = {
    # Tonewoods ($/sq mm derived from $/sq inch)
    "spruce_top":       0.0012,   # ~$0.78/sq in
    "maple_back_side":  0.0008,   # ~$0.52/sq in
    "mahogany":         0.0006,   # ~$0.39/sq in
    "rosewood":         0.0018,   # ~$1.16/sq in
    "ebony":            0.0025,   # ~$1.61/sq in
    "walnut":           0.0007,   # ~$0.45/sq in
    # Inlay materials ($/sq mm)
    "abalone":          0.0775,   # ~$50/sq in
    "mop":              0.0465,   # ~$30/sq in
    "paua":             0.0620,   # ~$40/sq in
    "celluloid":        0.0031,   # ~$2/sq in
    # Binding/purfling ($/linear mm — flagged separately)
    "abs_binding":      0.0010,   # $/linear mm
    "wood_binding":     0.0020,   # $/linear mm
    # Generic fallback
    "unknown":          0.0010,
}

# Feature type → default material
DEFAULT_MATERIAL_MAP: Dict[str, str] = {
    "BODY_OUTLINE":    "spruce_top",
    "PICKUP_ROUTE":    "unknown",
    "NECK_POCKET":     "unknown",
    "CONTROL_CAVITY":  "unknown",
    "BRIDGE_ROUTE":    "unknown",
    "F_HOLE":          "unknown",
    "SOUNDHOLE":       "unknown",
    "ROSETTE":         "mop",
    "JACK_ROUTE":      "unknown",
    "BINDING":         "abs_binding",
    "PURFLING":        "celluloid",
    "UNKNOWN":         "unknown",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FeatureBOMLine:
    """One line in the BOM — one feature contour."""
    feature_type:    str
    layer:           str
    area_sq_mm:      float
    area_sq_in:      float
    bbox_w_mm:       float
    bbox_h_mm:       float
    perimeter_mm:    float
    material:        str
    unit_price:      float          # USD per sq mm (or per linear mm for binding)
    quantity:        int   = 1
    cost_usd:        float = 0.0
    notes:           str  = ""

    def to_dict(self) -> dict:
        return {
            "feature_type": self.feature_type,
            "layer":        self.layer,
            "area_sq_mm":   round(self.area_sq_mm, 2),
            "area_sq_in":   round(self.area_sq_in, 4),
            "bbox_w_mm":    round(self.bbox_w_mm, 2),
            "bbox_h_mm":    round(self.bbox_h_mm, 2),
            "perimeter_mm": round(self.perimeter_mm, 2),
            "material":     self.material,
            "unit_price":   self.unit_price,
            "quantity":     self.quantity,
            "cost_usd":     round(self.cost_usd, 4),
            "notes":        self.notes,
        }


@dataclass
class NestingLayout:
    """Axis-aligned bounding-box nesting result for a single material."""
    material:        str
    sheet_w_mm:      float
    sheet_h_mm:      float
    used_area_sq_mm: float
    waste_area_sq_mm: float
    waste_pct:       float
    pieces:          List[Tuple[float, float, float, float]]  # (x, y, w, h) placements


@dataclass
class MaterialBOM:
    """Complete bill of materials for one extraction result."""
    source_path:     str
    calibration_source: str
    calibration_confidence: float
    lines:           List[FeatureBOMLine] = field(default_factory=list)
    nesting:         List[NestingLayout]  = field(default_factory=list)
    total_cost_usd:  float = 0.0
    warnings:        List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"BOM — {Path(self.source_path).name}",
            f"  Calibration: {self.calibration_source} "
            f"(confidence {self.calibration_confidence:.2f})",
            f"  {'Feature':<22} {'Material':<18} {'Area(sq in)':>12} "
            f"{'Bbox mm':>14} {'Cost USD':>10}",
            "  " + "─" * 80,
        ]
        for ln in self.lines:
            bbox = f"{ln.bbox_w_mm:.0f}×{ln.bbox_h_mm:.0f}"
            lines.append(
                f"  {ln.feature_type:<22} {ln.material:<18} "
                f"{ln.area_sq_in:>12.4f} {bbox:>14} {ln.cost_usd:>10.4f}")
        lines.append("  " + "─" * 80)
        lines.append(f"  {'TOTAL':>56} {self.total_cost_usd:>10.4f} USD")
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  ⚠  {w}")
        return "\n".join(lines)

    def to_json(self, path: str) -> None:
        data = {
            "source":               self.source_path,
            "calibration_source":   self.calibration_source,
            "calibration_confidence": self.calibration_confidence,
            "lines":                [ln.to_dict() for ln in self.lines],
            "total_cost_usd":       round(self.total_cost_usd, 4),
            "warnings":             self.warnings,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_csv(self, path: str) -> None:
        if not self.lines:
            return
        fieldnames = list(self.lines[0].to_dict().keys())
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows([ln.to_dict() for ln in self.lines])


# ---------------------------------------------------------------------------
# Core BOM generator
# ---------------------------------------------------------------------------

class MaterialBOMGenerator:
    """
    Generates a MaterialBOM from a PhotoExtractionResult.

    Parameters
    ----------
    material_map  : feature-type → material name overrides
    price_table   : material name → USD/sq mm price overrides
    waste_factor  : multiplier applied to cost for material waste (default 1.25)
    sheet_w_mm    : default sheet width for nesting (default 304.8 = 12 inches)
    sheet_h_mm    : default sheet height for nesting (default 609.6 = 24 inches)
    """

    def __init__(
        self,
        material_map:  Optional[Dict[str, str]]   = None,
        price_table:   Optional[Dict[str, float]]  = None,
        waste_factor:  float = 1.25,
        sheet_w_mm:    float = 304.8,   # 12 inches
        sheet_h_mm:    float = 609.6,   # 24 inches
    ):
        self.material_map  = {**DEFAULT_MATERIAL_MAP,  **(material_map  or {})}
        self.price_table   = {**DEFAULT_PRICES_USD_PER_SQ_MM, **(price_table or {})}
        self.waste_factor  = waste_factor
        self.sheet_w_mm    = sheet_w_mm
        self.sheet_h_mm    = sheet_h_mm

    # ------------------------------------------------------------------
    def generate(self, extraction_result) -> MaterialBOM:
        """
        Generate BOM from a PhotoExtractionResult.

        Parameters
        ----------
        extraction_result : PhotoExtractionResult from PhotoVectorizerV2.extract()

        Returns
        -------
        MaterialBOM
        """
        cal = extraction_result.calibration
        bom = MaterialBOM(
            source_path           = extraction_result.source_path,
            calibration_source    = cal.source.value if cal else "none",
            calibration_confidence= cal.confidence  if cal else 0.0,
        )

        if cal and cal.confidence < 0.5:
            bom.warnings.append(
                f"Low calibration confidence ({cal.confidence:.2f}) — "
                "area/cost estimates will be inaccurate. "
                "Supply --spec or --mm/--px for better calibration.")

        # Collect all feature contours
        for feature_type, contour_list in extraction_result.features.items():
            layer = feature_type.value.upper()
            material = self.material_map.get(layer, "unknown")
            price = self.price_table.get(material, self.price_table["unknown"])

            for fc in contour_list:
                if fc.points_mm is None:
                    continue

                pts = fc.points_mm
                area_mm   = self._shoelace_area(pts)
                perim_mm  = self._perimeter(pts)
                xs, ys    = pts[:, 0], pts[:, 1]
                bbox_w    = float(xs.max() - xs.min())
                bbox_h    = float(ys.max() - ys.min())

                # Binding/purfling: price per linear mm not area
                if material in ("abs_binding", "wood_binding"):
                    cost = perim_mm * price * self.waste_factor
                    notes = f"linear pricing ({perim_mm:.1f}mm)"
                else:
                    cost = area_mm * price * self.waste_factor
                    notes = ""

                line = FeatureBOMLine(
                    feature_type = feature_type.value,
                    layer        = layer,
                    area_sq_mm   = area_mm,
                    area_sq_in   = area_mm / 645.16,
                    bbox_w_mm    = bbox_w,
                    bbox_h_mm    = bbox_h,
                    perimeter_mm = perim_mm,
                    material     = material,
                    unit_price   = price,
                    cost_usd     = cost,
                    notes        = notes,
                )
                bom.lines.append(line)

        bom.total_cost_usd = sum(ln.cost_usd for ln in bom.lines)

        # Nesting per material
        material_groups: Dict[str, List[FeatureBOMLine]] = {}
        for ln in bom.lines:
            material_groups.setdefault(ln.material, []).append(ln)

        for mat, lines in material_groups.items():
            if mat in ("abs_binding", "wood_binding"):
                continue  # linear material — no nesting
            layout = self._nest_rectangles(mat, lines)
            if layout:
                bom.nesting.append(layout)

        return bom

    # ------------------------------------------------------------------
    @staticmethod
    def _shoelace_area(pts: np.ndarray) -> float:
        """Shoelace formula for polygon area (always positive)."""
        x, y = pts[:, 0], pts[:, 1]
        return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2.0

    @staticmethod
    def _perimeter(pts: np.ndarray) -> float:
        """Perimeter of a closed polygon."""
        diff = np.diff(np.vstack([pts, pts[:1]]), axis=0)
        return float(np.sum(np.sqrt((diff ** 2).sum(axis=1))))

    def _nest_rectangles(
        self,
        material: str,
        lines:    List[FeatureBOMLine],
    ) -> Optional[NestingLayout]:
        """
        Simple strip-packing nesting (axis-aligned, no rotation).
        Places bounding boxes left-to-right, wrapping to next row when full.
        Returns None if no pieces to nest.
        """
        pieces = [(ln.bbox_w_mm, ln.bbox_h_mm) for ln in lines if ln.bbox_w_mm > 0]
        if not pieces:
            return None

        # Sort by height descending (shelf algorithm)
        pieces_sorted = sorted(pieces, key=lambda p: p[1], reverse=True)
        GAP = 5.0   # mm gap between pieces

        x, y, row_h = 0.0, 0.0, 0.0
        placements = []
        used_area  = 0.0

        for pw, ph in pieces_sorted:
            if x + pw > self.sheet_w_mm:
                x   = 0.0
                y  += row_h + GAP
                row_h = 0.0
            placements.append((x, y, pw, ph))
            used_area += pw * ph
            x     += pw + GAP
            row_h  = max(row_h, ph)

        total_h   = y + row_h
        sheet_h   = max(self.sheet_h_mm, total_h)
        sheet_area = self.sheet_w_mm * sheet_h
        waste     = sheet_area - used_area
        waste_pct = waste / sheet_area * 100 if sheet_area > 0 else 0.0

        return NestingLayout(
            material         = material,
            sheet_w_mm       = self.sheet_w_mm,
            sheet_h_mm       = sheet_h,
            used_area_sq_mm  = used_area,
            waste_area_sq_mm = waste,
            waste_pct        = waste_pct,
            pieces           = placements,
        )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Build a minimal mock ExtractionResult using real contour data
    from dataclasses import dataclass as dc, field as dcf
    from enum import Enum

    class FT(Enum):
        BODY_OUTLINE  = "body_outline"
        SOUNDHOLE     = "soundhole"
        BRIDGE_ROUTE  = "bridge_route"
        BINDING       = "binding"

    @dc
    class MockFC:
        points_mm: object
        feature_type: object = None

    @dc
    class MockCal:
        source: object = None
        confidence: float = 0.80
        class _src:
            value = "instrument_spec"
        source = _src()

    @dc
    class MockResult:
        source_path: str = "test_guitar.png"
        calibration: object = None
        features: dict = dcf(default_factory=dict)

    # Create mock contours (approximate dreadnought)
    body_pts = np.array([
        [0, 0], [400, 0], [400, 520], [0, 520]
    ], dtype=np.float32)

    soundhole_pts = np.array([
        [160, 180], [240, 180], [240, 260], [160, 260]
    ], dtype=np.float32)

    bridge_pts = np.array([
        [140, 350], [260, 350], [260, 380], [140, 380]
    ], dtype=np.float32)

    binding_pts = np.array([
        [0, 0], [400, 0], [400, 520], [0, 520]
    ], dtype=np.float32)

    mock = MockResult(calibration=MockCal())
    mock.features = {
        FT.BODY_OUTLINE:  [MockFC(body_pts,     FT.BODY_OUTLINE)],
        FT.SOUNDHOLE:     [MockFC(soundhole_pts, FT.SOUNDHOLE)],
        FT.BRIDGE_ROUTE:  [MockFC(bridge_pts,    FT.BRIDGE_ROUTE)],
        FT.BINDING:       [MockFC(binding_pts,   FT.BINDING)],
    }

    gen = MaterialBOMGenerator()
    bom = gen.generate(mock)

    print(bom.summary())
    print(f"\nNesting layouts: {len(bom.nesting)}")
    for n in bom.nesting:
        print(f"  {n.material}: {n.sheet_w_mm:.0f}×{n.sheet_h_mm:.0f}mm  "
              f"waste={n.waste_pct:.1f}%  pieces={len(n.pieces)}")

    bom.to_json("/tmp/bom_test.json")
    bom.to_csv("/tmp/bom_test.csv")
    print(f"\nJSON: /tmp/bom_test.json")
    print(f"CSV:  /tmp/bom_test.csv")
