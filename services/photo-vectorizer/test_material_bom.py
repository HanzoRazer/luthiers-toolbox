"""
Tests for Material BOM Generator (Patch 08).

Covers:
  - Shoelace area computation (rectangle, triangle, irregular)
  - Perimeter computation
  - FeatureBOMLine.to_dict() serialization
  - MaterialBOM summary / JSON / CSV export
  - MaterialBOMGenerator with mock PhotoExtractionResult
  - Binding/purfling linear pricing
  - Low calibration confidence warning
  - No-calibration path
  - Nesting layout (shelf-packing)
  - Custom material_map and price_table overrides
  - Empty features edge case
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent))

from material_bom import (
    DEFAULT_MATERIAL_MAP,
    DEFAULT_PRICES_USD_PER_SQ_MM,
    FeatureBOMLine,
    MaterialBOM,
    MaterialBOMGenerator,
    NestingLayout,
)


# ---------------------------------------------------------------------------
# Mock types matching PhotoVectorizerV2 data model
# ---------------------------------------------------------------------------

class MockFeatureType(Enum):
    BODY_OUTLINE = "body_outline"
    PICKUP_ROUTE = "pickup_route"
    NECK_POCKET = "neck_pocket"
    SOUNDHOLE = "soundhole"
    BRIDGE_ROUTE = "bridge_route"
    BINDING = "binding"
    PURFLING = "purfling"
    ROSETTE = "rosette"
    F_HOLE = "f_hole"
    UNKNOWN = "unknown"


class MockScaleSource(Enum):
    USER_DIMENSION = "user_dimension"
    INSTRUMENT_SPEC = "instrument_spec"
    REFERENCE_OBJECT = "reference_object"
    NONE = "none"


@dataclass
class MockCalibration:
    mm_per_px: float = 1.0
    confidence: float = 0.85
    message: str = "test calibration"

    class _Source:
        value = "instrument_spec"
    source = _Source()


@dataclass
class MockLowCalibration:
    mm_per_px: float = 1.0
    confidence: float = 0.30
    message: str = "low confidence"

    class _Source:
        value = "fallback"
    source = _Source()


@dataclass
class MockFeatureContour:
    points_px: np.ndarray = None
    points_mm: Optional[np.ndarray] = None
    feature_type: object = None


@dataclass
class MockExtractionResult:
    source_path: str = "test_guitar.png"
    calibration: object = None
    features: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rect_contour(w: float, h: float, x0: float = 0, y0: float = 0) -> np.ndarray:
    """Closed rectangle contour at (x0, y0)."""
    return np.array([
        [x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]
    ], dtype=np.float32)


def _triangle_contour(base: float, height: float) -> np.ndarray:
    return np.array([
        [0, 0], [base, 0], [base / 2, height]
    ], dtype=np.float32)


# ===================================================================
# Unit tests — math helpers
# ===================================================================

class TestShoelaceArea:
    def test_rectangle_400x520(self):
        pts = _rect_contour(400, 520)
        area = MaterialBOMGenerator._shoelace_area(pts)
        assert abs(area - 208_000.0) < 0.1

    def test_unit_square(self):
        pts = _rect_contour(1, 1)
        area = MaterialBOMGenerator._shoelace_area(pts)
        assert abs(area - 1.0) < 0.01

    def test_triangle(self):
        pts = _triangle_contour(100, 50)
        area = MaterialBOMGenerator._shoelace_area(pts)
        expected = 100 * 50 / 2.0
        assert abs(area - expected) < 0.1

    def test_offset_rectangle(self):
        pts = _rect_contour(200, 300, x0=50, y0=100)
        area = MaterialBOMGenerator._shoelace_area(pts)
        assert abs(area - 60_000.0) < 0.1


class TestPerimeter:
    def test_rectangle_perimeter(self):
        pts = _rect_contour(400, 520)
        perim = MaterialBOMGenerator._perimeter(pts)
        assert abs(perim - 1840.0) < 0.1

    def test_unit_square_perimeter(self):
        pts = _rect_contour(1, 1)
        perim = MaterialBOMGenerator._perimeter(pts)
        assert abs(perim - 4.0) < 0.01

    def test_triangle_perimeter(self):
        pts = _triangle_contour(100, 50)
        # sides: base=100, two equal sides of sqrt(50^2 + 50^2) = ~70.71
        expected = 100 + 2 * np.sqrt(50**2 + 50**2)
        perim = MaterialBOMGenerator._perimeter(pts)
        assert abs(perim - expected) < 0.5


# ===================================================================
# Unit tests — data classes
# ===================================================================

class TestFeatureBOMLine:
    def test_to_dict_keys(self):
        line = FeatureBOMLine(
            feature_type="body_outline", layer="BODY_OUTLINE",
            area_sq_mm=100.0, area_sq_in=0.155,
            bbox_w_mm=10.0, bbox_h_mm=10.0,
            perimeter_mm=40.0, material="spruce_top",
            unit_price=0.0012, cost_usd=0.15)
        d = line.to_dict()
        assert set(d.keys()) == {
            "feature_type", "layer", "area_sq_mm", "area_sq_in",
            "bbox_w_mm", "bbox_h_mm", "perimeter_mm", "material",
            "unit_price", "quantity", "cost_usd", "notes"}

    def test_to_dict_rounding(self):
        line = FeatureBOMLine(
            feature_type="body_outline", layer="BODY_OUTLINE",
            area_sq_mm=123.456789, area_sq_in=0.12345678,
            bbox_w_mm=10.1234, bbox_h_mm=20.5678,
            perimeter_mm=61.9876, material="spruce_top",
            unit_price=0.0012, cost_usd=0.123456789)
        d = line.to_dict()
        assert d["area_sq_mm"] == 123.46
        assert d["area_sq_in"] == 0.1235
        assert d["cost_usd"] == 0.1235


class TestMaterialBOMExport:
    def test_summary_includes_source(self):
        bom = MaterialBOM(source_path="guitar.png",
                          calibration_source="instrument_spec",
                          calibration_confidence=0.85)
        s = bom.summary()
        assert "guitar.png" in s

    def test_summary_includes_total(self):
        bom = MaterialBOM(source_path="g.png",
                          calibration_source="none",
                          calibration_confidence=0.0,
                          total_cost_usd=42.50)
        s = bom.summary()
        assert "42.5000" in s

    def test_to_json(self, tmp_path):
        bom = MaterialBOM(source_path="test.png",
                          calibration_source="spec",
                          calibration_confidence=0.9,
                          total_cost_usd=5.0,
                          warnings=["low confidence"])
        line = FeatureBOMLine(
            feature_type="body_outline", layer="BODY_OUTLINE",
            area_sq_mm=100.0, area_sq_in=0.155,
            bbox_w_mm=10.0, bbox_h_mm=10.0,
            perimeter_mm=40.0, material="spruce_top",
            unit_price=0.0012, cost_usd=0.15)
        bom.lines.append(line)
        out = str(tmp_path / "bom.json")
        bom.to_json(out)
        data = json.loads(Path(out).read_text())
        assert data["source"] == "test.png"
        assert len(data["lines"]) == 1
        assert data["warnings"] == ["low confidence"]

    def test_to_csv(self, tmp_path):
        bom = MaterialBOM(source_path="test.png",
                          calibration_source="spec",
                          calibration_confidence=0.9)
        line = FeatureBOMLine(
            feature_type="body_outline", layer="BODY_OUTLINE",
            area_sq_mm=100.0, area_sq_in=0.155,
            bbox_w_mm=10.0, bbox_h_mm=10.0,
            perimeter_mm=40.0, material="spruce_top",
            unit_price=0.0012, cost_usd=0.15)
        bom.lines.append(line)
        out = str(tmp_path / "bom.csv")
        bom.to_csv(out)
        text = Path(out).read_text()
        assert "feature_type" in text
        assert "body_outline" in text

    def test_to_csv_empty_lines(self, tmp_path):
        bom = MaterialBOM(source_path="test.png",
                          calibration_source="none",
                          calibration_confidence=0.0)
        out = str(tmp_path / "empty.csv")
        bom.to_csv(out)
        assert not Path(out).exists()


# ===================================================================
# Integration tests — MaterialBOMGenerator
# ===================================================================

class TestMaterialBOMGenerator:

    def _make_result(self, features: dict, cal=None) -> MockExtractionResult:
        r = MockExtractionResult()
        r.calibration = cal or MockCalibration()
        r.features = features
        return r

    def test_single_body_outline(self):
        """Dreadnought-ish body: 400×520mm → area = 208,000 sq mm."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))

        assert len(bom.lines) == 1
        ln = bom.lines[0]
        assert ln.feature_type == "body_outline"
        assert ln.layer == "BODY_OUTLINE"
        assert ln.material == "spruce_top"
        assert abs(ln.area_sq_mm - 208_000) < 1
        assert abs(ln.bbox_w_mm - 400) < 0.1
        assert abs(ln.bbox_h_mm - 520) < 0.1
        # cost = area × price × waste = 208000 × 0.0012 × 1.25 = 312.0
        assert abs(ln.cost_usd - 312.0) < 0.1
        assert abs(bom.total_cost_usd - 312.0) < 0.1

    def test_multiple_features(self):
        """Body + soundhole + bridge route → 3 BOM lines."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ],
            MockFeatureType.SOUNDHOLE: [
                MockFeatureContour(points_mm=_rect_contour(80, 80, 160, 180))
            ],
            MockFeatureType.BRIDGE_ROUTE: [
                MockFeatureContour(points_mm=_rect_contour(120, 30, 140, 350))
            ],
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))

        assert len(bom.lines) == 3
        types = {ln.feature_type for ln in bom.lines}
        assert types == {"body_outline", "soundhole", "bridge_route"}
        assert bom.total_cost_usd > 0

    def test_binding_linear_pricing(self):
        """Binding should use perimeter-based pricing, not area-based."""
        binding_pts = _rect_contour(400, 520)
        features = {
            MockFeatureType.BINDING: [
                MockFeatureContour(points_mm=binding_pts)
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))

        assert len(bom.lines) == 1
        ln = bom.lines[0]
        assert ln.material == "abs_binding"
        assert "linear pricing" in ln.notes
        # cost = perimeter × price × waste = 1840 × 0.001 × 1.25 = 2.30
        expected_cost = 1840 * 0.001 * 1.25
        assert abs(ln.cost_usd - expected_cost) < 0.1

    def test_purfling_linear_pricing(self):
        """Purfling should also use linear pricing."""
        features = {
            MockFeatureType.PURFLING: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))

        ln = bom.lines[0]
        assert ln.material == "celluloid"
        assert "linear pricing" not in ln.notes  # celluloid is area-priced

    def test_rosette_material_assignment(self):
        """Rosette should default to MOP."""
        features = {
            MockFeatureType.ROSETTE: [
                MockFeatureContour(points_mm=_rect_contour(50, 50, 175, 175))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        assert bom.lines[0].material == "mop"

    def test_low_calibration_warning(self):
        """Low confidence triggers warning."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features, cal=MockLowCalibration()))

        assert len(bom.warnings) == 1
        assert "Low calibration confidence" in bom.warnings[0]

    def test_no_calibration(self):
        """No calibration → source 'none', confidence 0.0."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        result = MockExtractionResult()
        result.calibration = None
        result.features = features
        gen = MaterialBOMGenerator()
        bom = gen.generate(result)

        assert bom.calibration_source == "none"
        assert bom.calibration_confidence == 0.0
        assert len(bom.lines) == 1  # still processes contours

    def test_skip_none_points_mm(self):
        """Features with points_mm=None should be skipped."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=None),
                MockFeatureContour(points_mm=_rect_contour(400, 520)),
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        assert len(bom.lines) == 1

    def test_empty_features(self):
        """Empty features dict → empty BOM, zero cost."""
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result({}))
        assert len(bom.lines) == 0
        assert bom.total_cost_usd == 0.0
        assert len(bom.nesting) == 0

    def test_custom_material_map(self):
        """Custom material_map overrides defaults."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        gen = MaterialBOMGenerator(material_map={"BODY_OUTLINE": "rosewood"})
        bom = gen.generate(self._make_result(features))
        assert bom.lines[0].material == "rosewood"

    def test_custom_price_table(self):
        """Custom price_table overrides default pricing."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(100, 100))
            ]
        }
        gen = MaterialBOMGenerator(price_table={"spruce_top": 0.01})
        bom = gen.generate(self._make_result(features))
        # area=10000, price=0.01, waste=1.25 → cost = 125.0
        assert abs(bom.lines[0].cost_usd - 125.0) < 0.1

    def test_custom_waste_factor(self):
        """Custom waste_factor scales cost."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(100, 100))
            ]
        }
        gen_default = MaterialBOMGenerator()
        gen_higher = MaterialBOMGenerator(waste_factor=1.50)
        bom_default = gen_default.generate(self._make_result(features))
        bom_higher = gen_higher.generate(self._make_result(features))
        assert bom_higher.total_cost_usd > bom_default.total_cost_usd

    def test_area_sq_in_conversion(self):
        """area_sq_in = area_sq_mm / 645.16."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(25.4, 25.4))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        ln = bom.lines[0]
        # 25.4mm × 25.4mm = 645.16 sq mm = 1 sq in
        assert abs(ln.area_sq_in - 1.0) < 0.01


# ===================================================================
# Nesting tests
# ===================================================================

class TestNestingLayout:

    def _make_result(self, features, cal=None):
        r = MockExtractionResult()
        r.calibration = cal or MockCalibration()
        r.features = features
        return r

    def test_single_piece_nesting(self):
        """Single piece fits on default sheet."""
        features = {
            MockFeatureType.BODY_OUTLINE: [
                MockFeatureContour(points_mm=_rect_contour(200, 300))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))

        assert len(bom.nesting) == 1
        nest = bom.nesting[0]
        assert nest.material == "spruce_top"
        assert abs(nest.used_area_sq_mm - 60_000) < 1
        assert nest.waste_pct > 0
        assert len(nest.pieces) == 1

    def test_binding_skips_nesting(self):
        """Linear materials (binding) should not produce nesting layouts."""
        features = {
            MockFeatureType.BINDING: [
                MockFeatureContour(points_mm=_rect_contour(400, 520))
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        assert len(bom.nesting) == 0

    def test_multiple_pieces_same_material(self):
        """Two soundholes should nest onto one sheet."""
        features = {
            MockFeatureType.SOUNDHOLE: [
                MockFeatureContour(points_mm=_rect_contour(80, 80, 0, 0)),
                MockFeatureContour(points_mm=_rect_contour(80, 80, 100, 0)),
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        # Both use "unknown" material → should get one nesting layout
        nests = [n for n in bom.nesting if n.material == "unknown"]
        assert len(nests) == 1
        assert len(nests[0].pieces) == 2

    def test_piece_wraps_to_next_row(self):
        """Pieces that exceed sheet width wrap to next shelf row."""
        # 4 pieces of 100mm wide on 304.8mm sheet → row wraps
        features = {
            MockFeatureType.SOUNDHOLE: [
                MockFeatureContour(points_mm=_rect_contour(100, 50, i * 110, 0))
                for i in range(4)
            ]
        }
        gen = MaterialBOMGenerator()
        bom = gen.generate(self._make_result(features))
        nest = bom.nesting[0]
        # Last piece should be on second row (y > 0)
        assert nest.pieces[-1][1] > 0


# ===================================================================
# Default maps sanity
# ===================================================================

class TestDefaults:
    def test_all_feature_types_mapped(self):
        """Every FeatureType should have a default material mapping."""
        from photo_vectorizer_v2 import FeatureType
        for ft in FeatureType:
            assert ft.value.upper() in DEFAULT_MATERIAL_MAP, f"Missing: {ft.value}"

    def test_all_materials_have_prices(self):
        """Every material in DEFAULT_MATERIAL_MAP must have a price."""
        for mat in DEFAULT_MATERIAL_MAP.values():
            assert mat in DEFAULT_PRICES_USD_PER_SQ_MM, f"Missing price: {mat}"
