"""
Tests for Sheet Type Detection & Body Candidate Filtering
==========================================================

Tests the Phase 3.6 improvements:
  1. Aspect ratio gate rejects elongated contours (necks, pickguards)
  2. Configurable min_body_dim / max_body_aspect_ratio via InstrumentSpec
  3. sheet_type propagated to ExtractionResult and summary()

Author: The Production Shop
Version: 3.6.0
"""

import numpy as np
import pytest
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import sys
from pathlib import Path

# Ensure vectorizer is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vectorizer_phase3 import (
    ContourInfo,
    ContourCategory,
    ExtractionResult,
    InstrumentSpec,
    InstrumentType,
    INSTRUMENT_SPECS,
    rerank_body_candidates,
)


# ---------------------------------------------------------------------------
# Helpers — build synthetic ContourInfo objects
# ---------------------------------------------------------------------------

def _make_contour(width_mm: float, height_mm: float) -> np.ndarray:
    """Return a minimal rectangular contour (4 points)."""
    return np.array([
        [[0, 0]],
        [[int(width_mm), 0]],
        [[int(width_mm), int(height_mm)]],
        [[0, int(height_mm)]],
    ], dtype=np.int32)


def _make_contour_info(
    width_mm: float,
    height_mm: float,
    category: ContourCategory = ContourCategory.BODY_OUTLINE,
) -> ContourInfo:
    """Build a ContourInfo with the given mm dimensions."""
    contour = _make_contour(width_mm, height_mm)
    w, h = width_mm, height_mm
    return ContourInfo(
        contour=contour,
        category=category,
        width_mm=w,
        height_mm=h,
        area_px=w * h,
        perimeter_px=2 * (w + h),
        circularity=0.5,
        aspect_ratio=max(w, h) / min(w, h) if min(w, h) > 0 else 999,
        point_count=4,
        bbox=(0, 0, int(w), int(h)),
    )


def _build_classified(
    *infos: Tuple[float, float, ContourCategory],
) -> Dict[ContourCategory, List[ContourInfo]]:
    """
    Build a classified dict from (width_mm, height_mm, category) tuples.

    Example::
        _build_classified(
            (410, 340, ContourCategory.BODY_OUTLINE),
            (156, 320, ContourCategory.PICKGUARD),
        )
    """
    classified: Dict[ContourCategory, List[ContourInfo]] = {}
    for w, h, cat in infos:
        info = _make_contour_info(w, h, cat)
        classified.setdefault(cat, []).append(info)
    return classified


# ---------------------------------------------------------------------------
# 1. Aspect ratio gate
# ---------------------------------------------------------------------------

class TestAspectRatioGate:
    """
    The dual-gate should reject body candidates that are:
      - too small (max_dim < min_body_dim), OR
      - too elongated (aspect_ratio > max_body_aspect_ratio).
    """

    def test_normal_guitar_body_accepted(self):
        """A 410×340mm Strat body passes both gates."""
        classified = _build_classified(
            (410, 340, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000)
        assert len(result[ContourCategory.BODY_OUTLINE]) == 1

    def test_tele_pickguard_rejected_by_aspect_ratio(self):
        """
        320×156mm Tele pickguard — bigger than 300mm but aspect 2.05.
        Rejected by the aspect ratio gate (>2.0).
        """
        classified = _build_classified(
            (156, 320, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000, min_body_score=0.0)
        # Body list should be cleared — the contour was demoted
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0

    def test_tele_neck_rejected_by_aspect_ratio(self):
        """
        178×713mm Tele neck — aspect ~4.0, clearly not a body.
        Rejected by the aspect ratio gate.
        """
        classified = _build_classified(
            (178, 713, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000, min_body_score=0.0)
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0

    def test_small_contour_rejected_by_size(self):
        """A 200×180mm contour is below the 300mm minimum."""
        classified = _build_classified(
            (200, 180, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000, min_body_score=0.0)
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0

    def test_square_body_accepted(self):
        """A 350×340mm body with aspect ~1.03 passes easily."""
        classified = _build_classified(
            (350, 340, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000)
        assert len(result[ContourCategory.BODY_OUTLINE]) == 1


# ---------------------------------------------------------------------------
# 2. Configurable thresholds via InstrumentSpec
# ---------------------------------------------------------------------------

class TestConfigurableThresholds:
    """
    InstrumentSpec now carries min_body_dim and max_body_aspect_ratio
    so small instruments (ukuleles, Klein) can use lower thresholds.
    """

    def test_klein_spec_has_lower_min_body_dim(self):
        """Klein body is only ~250mm wide — spec sets min_body_dim=210."""
        spec = INSTRUMENT_SPECS["klein"]
        assert spec.min_body_dim == 210.0

    def test_ukulele_specs_have_lower_min_body_dim(self):
        """Ukulele specs have min_body_dim from 155-195mm."""
        for key in ("ukulele_soprano", "ukulele_concert", "ukulele_tenor"):
            spec = INSTRUMENT_SPECS[key]
            assert spec.min_body_dim < 200.0
            assert spec.max_body_aspect_ratio == 1.8

    def test_klein_body_accepted_with_custom_threshold(self):
        """A 260×230mm Klein body passes with min_body_dim=210."""
        classified = _build_classified(
            (260, 230, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(
            classified, 2000, 3000,
            min_body_dim=210.0, max_body_aspect_ratio=2.0,
        )
        assert len(result[ContourCategory.BODY_OUTLINE]) == 1

    def test_klein_body_rejected_at_default_threshold(self):
        """Same 260mm contour fails at default min_body_dim=300."""
        classified = _build_classified(
            (260, 230, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(
            classified, 2000, 3000,
            min_body_score=0.0, min_body_dim=300.0,
        )
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0

    def test_soprano_ukulele_body_accepted(self):
        """Soprano ukulele body ~170mm passes with its spec threshold."""
        spec = INSTRUMENT_SPECS["ukulele_soprano"]
        classified = _build_classified(
            (170, 140, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(
            classified, 1000, 1500,
            min_body_score=0.0,
            min_body_dim=spec.min_body_dim,
            max_body_aspect_ratio=spec.max_body_aspect_ratio,
        )
        assert len(result[ContourCategory.BODY_OUTLINE]) == 1

    def test_default_spec_values(self):
        """Default InstrumentSpec uses 300mm min and 2.0 max aspect."""
        spec = InstrumentSpec(
            name="test",
            body_length_range=(400, 450),
            body_width_range=(300, 350),
            neck_pocket_range=(55, 60),
        )
        assert spec.min_body_dim == 300.0
        assert spec.max_body_aspect_ratio == 2.0


# ---------------------------------------------------------------------------
# 3. sheet_type in ExtractionResult
# ---------------------------------------------------------------------------

class TestSheetTypePropagation:
    """
    ExtractionResult carries sheet_type and exposes it in summary().
    """

    def test_default_sheet_type_is_body(self):
        result = ExtractionResult(
            source_path="test.pdf",
            output_dxf="test.dxf",
            output_svg=None,
            instrument_type=InstrumentType.ELECTRIC_GUITAR,
            contours_by_category={},
        )
        assert result.sheet_type == "body"

    def test_pickguard_sheet_type(self):
        result = ExtractionResult(
            source_path="test.pdf",
            output_dxf="test.dxf",
            output_svg=None,
            instrument_type=InstrumentType.ELECTRIC_GUITAR,
            contours_by_category={},
            sheet_type="pickguard_sheet",
        )
        assert result.sheet_type == "pickguard_sheet"

    def test_sheet_type_in_summary(self):
        result = ExtractionResult(
            source_path="test.pdf",
            output_dxf="test.dxf",
            output_svg=None,
            instrument_type=InstrumentType.ELECTRIC_GUITAR,
            contours_by_category={},
            sheet_type="component_sheet",
        )
        summary = result.summary()
        assert summary["sheet_type"] == "component_sheet"


# ---------------------------------------------------------------------------
# 4. Compound scenarios — body vs component classification
# ---------------------------------------------------------------------------

class TestCompoundScenarios:
    """
    Mixed sheets: body present alongside components, or no body at all.
    """

    def test_body_with_pickguard_keeps_both(self):
        """A sheet with a valid body and a pickguard — body wins, pickguard kept."""
        classified = _build_classified(
            (410, 340, ContourCategory.BODY_OUTLINE),
            (156, 320, ContourCategory.PICKGUARD),
        )
        result = rerank_body_candidates(classified, 2000, 3000)
        assert len(result[ContourCategory.BODY_OUTLINE]) == 1
        assert len(result[ContourCategory.PICKGUARD]) == 1

    def test_no_body_candidates_returns_unchanged(self):
        """If there are no body candidates at all, dict is returned unchanged."""
        classified = _build_classified(
            (150, 100, ContourCategory.PICKGUARD),
        )
        result = rerank_body_candidates(classified, 2000, 3000)
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0
        assert len(result[ContourCategory.PICKGUARD]) == 1

    def test_rejected_body_moves_to_pickguard_if_size_fits(self):
        """
        A body candidate that fails the dual-gate gets reclassified.
        If its dimensions are in typical pickguard range (100-400mm max,
        50-350mm min), it should land in PICKGUARD.
        """
        classified = _build_classified(
            (156, 320, ContourCategory.BODY_OUTLINE),
        )
        result = rerank_body_candidates(classified, 2000, 3000, min_body_score=0.0)
        # Body should be empty — candidate was rejected
        assert len(result.get(ContourCategory.BODY_OUTLINE, [])) == 0
        # The rejected contour should be reclassified as pickguard
        assert len(result.get(ContourCategory.PICKGUARD, [])) >= 1
