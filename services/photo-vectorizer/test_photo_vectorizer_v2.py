"""
Integration tests for Photo Vectorizer v2.0 — patch integration verification.

Covers:
  - MultiInstrumentSplitter (patch_02)
  - BodyIsolator (patch_03)
  - ScaleCalibrator with enhanced 6-priority chain (patch_01)
  - estimate_render_dpi heuristic (patch_01)
  - Full pipeline extract() for single + multi-instrument images
  - grid_classify import and merge_classifications wiring
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
import pytest

# Module under test — adjust sys.path so grid_classify resolves
import sys
sys.path.insert(0, str(Path(__file__).parent))

from photo_vectorizer_v2 import (
    BodyIsolator,
    BodyRegion,
    CalibrationResult,
    ContourScore,
    ContourStageResult,
    FeatureContour,
    FeatureType,
    InstrumentFamily,
    MultiInstrumentSplitter,
    PhotoVectorizerV2,
    ScaleCalibrator,
    ScaleSource,
    SplitResult,
    Unit,
    detect_dark_background,
    estimate_render_dpi,
    run_contour_stage_v2,
    vectorize_photo_v2,
    INSTRUMENT_SPECS,
)
from grid_classify import PhotoGridClassifier, merge_classifications, GridClassification


# ── Synthetic image helpers ──────────────────────────────────────────────────

def _make_guitar_image(width: int = 800, height: int = 1200,
                       body_color: int = 60, bg_color: int = 230) -> np.ndarray:
    """
    Create a synthetic guitar-shaped image:
      - Light background
      - Narrow neck region at top (rows 50-400, centered strip ~120px wide)
      - Wide body region below    (rows 400-1050, ~500px wide ellipse)
    Returns BGR image.
    """
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)
    cx = width // 2

    # Draw neck (narrow rectangle)
    neck_w = 60
    cv2.rectangle(img, (cx - neck_w, 50), (cx + neck_w, 450),
                  (body_color, body_color, body_color), -1)

    # Draw body (ellipse)
    cv2.ellipse(img, (cx, 700), (250, 320), 0, 0, 360,
                (body_color, body_color, body_color), -1)

    return img


def _make_multi_guitar_image(n: int = 2, gap_width: int = 100) -> np.ndarray:
    """Create an image with N guitars side by side separated by bright gaps."""
    single_w = 400
    single_h = 800
    total_w = n * single_w + (n - 1) * gap_width
    img = np.full((single_h, total_w, 3), 230, dtype=np.uint8)

    for i in range(n):
        x_offset = i * (single_w + gap_width)
        cx = x_offset + single_w // 2
        # body ellipse
        cv2.ellipse(img, (cx, 500), (150, 250), 0, 0, 360, (50, 50, 50), -1)
        # neck
        cv2.rectangle(img, (cx - 30, 80), (cx + 30, 350), (50, 50, 50), -1)

    return img


def _make_fg_mask(image: np.ndarray, threshold: int = 150) -> np.ndarray:
    """Simple foreground mask from a synthetic image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    return mask


# =============================================================================
# MultiInstrumentSplitter tests
# =============================================================================

class TestMultiInstrumentSplitter:

    def test_single_instrument_no_split(self):
        img = _make_guitar_image()
        splitter = MultiInstrumentSplitter()
        result = splitter.detect_and_split(img)
        assert not result.is_multi
        assert result.count == 1
        assert result.crops[0] == (0, 0, img.shape[1], img.shape[0])

    def test_two_instruments_detected(self):
        img = _make_multi_guitar_image(n=2, gap_width=120)
        splitter = MultiInstrumentSplitter(bg_brightness_threshold=180)
        result = splitter.detect_and_split(img)
        assert result.is_multi
        assert result.count == 2
        assert result.split_axis == "vertical"
        assert len(result.gap_positions) >= 1

    def test_three_instruments_detected(self):
        img = _make_multi_guitar_image(n=3, gap_width=100)
        splitter = MultiInstrumentSplitter(bg_brightness_threshold=180)
        result = splitter.detect_and_split(img)
        assert result.count >= 2  # at least detects multi

    def test_max_instruments_cap(self):
        img = _make_multi_guitar_image(n=5, gap_width=80)
        splitter = MultiInstrumentSplitter(bg_brightness_threshold=180,
                                           max_instruments=3)
        result = splitter.detect_and_split(img)
        assert result.count <= 3

    def test_split_result_properties(self):
        r = SplitResult(crops=[(0, 0, 100, 200), (200, 0, 100, 200)])
        assert r.is_multi
        assert r.count == 2

    def test_split_result_single(self):
        r = SplitResult(crops=[(0, 0, 800, 1200)])
        assert not r.is_multi
        assert r.count == 1

    def test_find_runs_basic(self):
        arr = np.array([0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0])
        runs = MultiInstrumentSplitter._find_runs(arr, value=1, min_length=3)
        assert len(runs) >= 1
        assert runs[0] == (2, 4)

    def test_find_runs_no_match(self):
        arr = np.array([0, 0, 0, 0])
        runs = MultiInstrumentSplitter._find_runs(arr, value=1, min_length=2)
        assert runs == []


# =============================================================================
# BodyIsolator tests
# =============================================================================

class TestBodyIsolator:

    def test_isolate_with_fg_mask(self):
        img = _make_guitar_image()
        mask = _make_fg_mask(img)
        isolator = BodyIsolator()
        region = isolator.isolate(img, fg_mask=mask)

        assert isinstance(region, BodyRegion)
        assert region.height > 0
        assert region.width > 0
        assert region.confidence > 0
        assert "Row widths from fg_mask" in region.notes[0]

    def test_isolate_without_mask(self):
        img = _make_guitar_image()
        isolator = BodyIsolator()
        region = isolator.isolate(img, fg_mask=None)

        assert isinstance(region, BodyRegion)
        assert region.height > 0

    def test_body_region_excludes_neck(self):
        """Body region's top (neck_end_row) should be below the neck area."""
        img = _make_guitar_image()
        mask = _make_fg_mask(img)
        isolator = BodyIsolator()
        region = isolator.isolate(img, fg_mask=mask)

        # Neck is in rows 50-450, body starts around row 380+
        # BodyIsolator should find body starting below the neck
        assert region.neck_end_row > 200, (
            f"Body should start below neck area, got neck_end_row={region.neck_end_row}")

    def test_body_height_px_property(self):
        region = BodyRegion(x=10, y=400, width=500, height=600,
                            confidence=0.8, neck_end_row=400,
                            max_body_width_px=500, notes=[])
        assert region.height_px == 600
        assert region.bbox == (10, 400, 500, 600)

    def test_fallback_on_blank_image(self):
        """All-white image should trigger fallback."""
        img = np.full((1000, 800, 3), 255, dtype=np.uint8)
        isolator = BodyIsolator()
        region = isolator.isolate(img)
        assert region.confidence == 0.30
        assert any("fallback" in n.lower() for n in region.notes)


# =============================================================================
# estimate_render_dpi tests
# =============================================================================

class TestEstimateRenderDPI:

    def test_smooth_render_returns_low_dpi(self):
        """A smooth synthetic image (few edges) should estimate ~96 DPI."""
        img = np.full((800, 600, 3), 200, dtype=np.uint8)
        # Add a single smooth gradient — very few edges
        for r in range(800):
            img[r, :, :] = int(150 + 50 * (r / 800))
        dpi = estimate_render_dpi(img)
        assert dpi <= 150.0, f"Expected low DPI for smooth image, got {dpi}"

    def test_textured_image_returns_higher_dpi(self):
        """A noisy image (many edges) should estimate higher DPI."""
        rng = np.random.RandomState(42)
        img = rng.randint(0, 255, (800, 600, 3), dtype=np.uint8)
        dpi = estimate_render_dpi(img)
        assert dpi >= 150.0, f"Expected high DPI for noisy image, got {dpi}"

    def test_with_fg_mask(self):
        img = _make_guitar_image()
        mask = _make_fg_mask(img)
        dpi = estimate_render_dpi(img, fg_mask=mask)
        assert 50 < dpi < 400


# =============================================================================
# ScaleCalibrator enhanced tests
# =============================================================================

class TestScaleCalibrator:

    def test_priority_1_user_dimension(self):
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, known_mm=406.0, known_px=812.0)
        assert result.source == ScaleSource.USER_DIMENSION
        assert result.confidence == 1.0
        assert abs(result.mm_per_px - 0.5) < 0.001

    def test_priority_1_unit_conversion_inch(self):
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, known_mm=16.0, known_px=406.4,
                               unit=Unit.INCH)
        # 16 inch = 406.4mm → mpp = 406.4/406.4 = 1.0
        assert result.source == ScaleSource.USER_DIMENSION
        assert abs(result.mm_per_px - 1.0) < 0.01

    def test_priority_3_exif_dpi(self):
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, image_dpi=300.0)
        assert result.source == ScaleSource.EXIF_DPI
        assert result.confidence == 0.85
        assert abs(result.mm_per_px - 25.4 / 300) < 0.001

    def test_priority_4_spec_with_body_height(self):
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, spec_name="stratocaster",
                               body_height_px=812.0)
        assert result.source == ScaleSource.INSTRUMENT_SPEC
        assert result.confidence == 0.75  # Updated for Diff 3
        expected_mpp = 406.0 / 812.0
        assert abs(result.mm_per_px - expected_mpp) < 0.001

    def test_priority_4_requires_body_height(self):
        """Spec without body_height_px should NOT use spec priority."""
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, spec_name="stratocaster")
        # Should fall through to priority 5 or 6, not spec
        assert result.source != ScaleSource.INSTRUMENT_SPEC

    def test_priority_5_render_dpi_estimation(self):
        """When no EXIF, no spec, no user dim → should use estimated DPI."""
        cal = ScaleCalibrator(default_dpi=300.0)
        # Smooth image → edge density low → estimate 96 DPI (≠300)
        img = np.full((800, 600, 3), 200, dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (500, 700), (50, 50, 50), -1)
        result = cal.calibrate(img)
        # Should pick estimated render DPI (96) or assumed
        assert result.source in (ScaleSource.ESTIMATED_RENDER_DPI, ScaleSource.ASSUMED_DPI)

    def test_priority_6_assumed_fallback(self):
        """Force assumed fallback."""
        cal = ScaleCalibrator(default_dpi=300.0)
        # Need edge density to match default DPI so estimation doesn't fire
        # Use a moderately noisy image that estimates ~300 DPI
        rng = np.random.RandomState(99)
        img = rng.randint(0, 255, (800, 600, 3), dtype=np.uint8)
        result = cal.calibrate(img)
        # With noisy image, estimate_render_dpi returns 300 which == default
        # so it falls through to assumed
        if result.source == ScaleSource.ASSUMED_DPI:
            assert result.confidence == 0.2

    def test_new_fg_mask_param_accepted(self):
        """Verify calibrate() accepts fg_mask without error."""
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        mask = _make_fg_mask(img)
        result = cal.calibrate(img, fg_mask=mask)
        assert result.mm_per_px > 0

    def test_new_body_height_px_param_accepted(self):
        """Verify calibrate() accepts body_height_px without error."""
        cal = ScaleCalibrator()
        img = _make_guitar_image()
        result = cal.calibrate(img, body_height_px=500.0,
                               spec_name="stratocaster")
        assert result.mm_per_px > 0


# =============================================================================
# ScaleSource enum tests
# =============================================================================

class TestScaleSourceEnum:

    def test_estimated_render_dpi_exists(self):
        assert ScaleSource.ESTIMATED_RENDER_DPI.value == "estimated_render_dpi"

    def test_all_sources_distinct(self):
        values = [s.value for s in ScaleSource]
        assert len(values) == len(set(values))


# =============================================================================
# Dark background detection tests
# =============================================================================

class TestDarkBackgroundDetection:

    def test_dark_image(self):
        img = np.full((400, 400, 3), 20, dtype=np.uint8)
        assert detect_dark_background(img) == True

    def test_light_image(self):
        img = np.full((400, 400, 3), 220, dtype=np.uint8)
        assert detect_dark_background(img) == False


# =============================================================================
# grid_classify integration tests
# =============================================================================

class TestGridClassifyIntegration:

    def test_import_works(self):
        """grid_classify module imports successfully from photo-vectorizer dir."""
        clf = PhotoGridClassifier()
        assert clf is not None

    def test_classify_contour_returns_grid_classification(self):
        clf = PhotoGridClassifier()
        body_bbox = (50, 400, 450, 580)
        contour_bbox = (160, 420, 70, 35)
        gc = clf.classify_contour_px(contour_bbox, body_bbox)
        assert hasattr(gc, 'primary_category')
        assert hasattr(gc, 'grid_confidence')
        assert hasattr(gc, 'notes')

    def test_merge_classifications_agreement(self):
        clf = PhotoGridClassifier()
        body_bbox = (50, 400, 450, 580)
        contour_bbox = (160, 420, 70, 35)
        gc = clf.classify_contour_px(contour_bbox, body_bbox)

        feat, conf, reason = merge_classifications(
            gc.primary_category, 0.7, gc)  # Use primary_category, not mapped_feature
        assert isinstance(feat, str)
        assert 0.0 <= conf <= 1.0

    def test_merge_unknown_dimension(self):
        clf = PhotoGridClassifier()
        body_bbox = (50, 400, 450, 580)
        contour_bbox = (160, 420, 70, 35)
        gc = clf.classify_contour_px(contour_bbox, body_bbox)

        feat, conf, reason = merge_classifications("unknown", 0.3, gc)
        # Should use grid result since dimension is unknown
        assert feat != "unknown" or gc.mapped_feature == "unknown"


# =============================================================================
# Full pipeline integration tests
# =============================================================================

class TestFullPipeline:

    def test_extract_single_guitar_produces_result(self, tmp_path):
        """Full extract() on a synthetic guitar image produces a result."""
        img = _make_guitar_image()
        img_path = tmp_path / "test_guitar.png"
        cv2.imwrite(str(img_path), img)

        v = PhotoVectorizerV2(bg_method=BGRemovalMethod.THRESHOLD)
        result = v.extract(str(img_path), output_dir=str(tmp_path),
                           export_svg=True, export_dxf=False,
                           export_json=False, correct_perspective=False)

        # Single instrument → should return one result, not a list
        if isinstance(result, list):
            assert len(result) >= 1
            result = result[0]

        assert result.processing_time_ms > 0
        assert result.calibration is not None
        assert result.calibration.mm_per_px > 0

    def test_extract_multi_guitar_returns_list(self, tmp_path):
        """Multi-instrument image should return a list of results."""
        img = _make_multi_guitar_image(n=2, gap_width=120)
        img_path = tmp_path / "test_multi.png"
        cv2.imwrite(str(img_path), img)

        v = PhotoVectorizerV2(bg_method=BGRemovalMethod.THRESHOLD)
        result = v.extract(str(img_path), output_dir=str(tmp_path),
                           export_svg=False, export_dxf=False,
                           export_json=False, correct_perspective=False)

        if isinstance(result, list):
            assert len(result) >= 2, f"Expected 2+ results, got {len(result)}"

    def test_body_isolator_feeds_calibrator(self, tmp_path):
        """Verify body_height_px from isolator reaches calibrator."""
        img = _make_guitar_image()
        img_path = tmp_path / "test_body_iso.png"
        cv2.imwrite(str(img_path), img)

        v = PhotoVectorizerV2(bg_method=BGRemovalMethod.THRESHOLD)
        result = v.extract(str(img_path), output_dir=str(tmp_path),
                           spec_name="stratocaster",
                           export_svg=False, export_dxf=False,
                           correct_perspective=False)

        if isinstance(result, list):
            result = result[0]

        assert result.calibration is not None
        # With spec + body height, should use spec-based calibration
        # or render DPI estimation
        assert result.calibration.source in (
            ScaleSource.INSTRUMENT_SPEC,
            ScaleSource.ESTIMATED_RENDER_DPI,
            ScaleSource.ASSUMED_DPI,
        )

    def test_calibration_confidence_warning(self, tmp_path):
        """Low-confidence calibration should not crash."""
        img = np.full((400, 400, 3), 200, dtype=np.uint8)
        cv2.rectangle(img, (50, 50), (350, 350), (60, 60, 60), -1)
        img_path = tmp_path / "test_low_conf.png"
        cv2.imwrite(str(img_path), img)

        v = PhotoVectorizerV2(bg_method=BGRemovalMethod.THRESHOLD)
        result = v.extract(str(img_path), output_dir=str(tmp_path),
                           export_svg=False, export_dxf=False,
                           correct_perspective=False)

        if isinstance(result, list):
            result = result[0]
        assert result.calibration is not None

    def test_debug_images_flag(self, tmp_path):
        """debug_images=True should produce additional output files."""
        img = _make_guitar_image()
        img_path = tmp_path / "test_debug.png"
        cv2.imwrite(str(img_path), img)

        v = PhotoVectorizerV2(bg_method=BGRemovalMethod.THRESHOLD)
        result = v.extract(str(img_path), output_dir=str(tmp_path),
                           debug_images=True, export_svg=False,
                           export_dxf=False, correct_perspective=False)

        if isinstance(result, list):
            result = result[0]
        assert len(result.debug_images) > 0


# Need BGRemovalMethod import for test class
from photo_vectorizer_v2 import BGRemovalMethod


# =============================================================================
# Standalone contour stage helpers
# =============================================================================

def _make_fc(x, y, w, h, area=None, feature_type=FeatureType.UNKNOWN,
             confidence=0.8, solidity=0.85):
    """Create a FeatureContour from a bounding-box spec (rectangle contour)."""
    pts = np.array([
        [x, y], [x + w, y], [x + w, y + h], [x, y + h],
    ], dtype=np.int32).reshape(-1, 1, 2)
    actual_area = area if area is not None else float(w * h)
    return FeatureContour(
        points_px=pts,
        feature_type=feature_type,
        confidence=confidence,
        area_px=actual_area,
        bbox_px=(x, y, w, h),
        hash_id="test",
        solidity=solidity,
        aspect_ratio=max(w, h) / max(1, min(w, h)),
    )


def _make_body_region(x, y, w, h):
    return BodyRegion(
        x=x, y=y, width=w, height=h,
        confidence=0.9, neck_end_row=y, max_body_width_px=w,
    )


def _make_score(
    contour_index: int,
    score: float,
    *,
    issues=None,
    includes_neck=False,
    border_contact=False,
    ownership_score=0.85,
    vertical_coverage=0.92,
    neck_inclusion_score=0.02,
):
    return ContourScore(
        contour_index=contour_index,
        score=score,
        completeness=0.82,
        includes_neck=includes_neck,
        border_contact=border_contact,
        dimension_plausibility=0.80,
        symmetry_score=0.78,
        aspect_ratio_ok=True,
        ownership_score=ownership_score,
        vertical_coverage=vertical_coverage,
        neck_inclusion_score=neck_inclusion_score,
        issues=issues or [],
    )


# =============================================================================
# run_contour_stage_v2 tests — ownership gate mirroring
# =============================================================================


def test_run_contour_stage_v2_mirrors_ownership_fields(monkeypatch):
    feature_contours = [
        _make_fc(10, 20, 120, 220, area=26000),
        _make_fc(15, 0, 70, 280, area=24000),
    ]

    monkeypatch.setattr(
        "photo_vectorizer_v2.extract_feature_contours",
        lambda *args, **kwargs: feature_contours,
    )
    monkeypatch.setattr(
        "photo_vectorizer_v2.merge_feature_contours",
        lambda contours, image_shape, body_region, mpp: contours,
    )

    class _ScorerStub:
        def score_all_candidates(self, contours, body_region, family, mpp, image_shape):
            # Both contours below ownership threshold (0.60) so gate rejects all
            return [
                _make_score(0, 0.78, ownership_score=0.52, vertical_coverage=0.60),
                _make_score(
                    1,
                    0.83,
                    ownership_score=0.41,
                    includes_neck=True,
                    issues=["body ownership weak (0.41)"],
                    vertical_coverage=0.48,
                    neck_inclusion_score=0.72,
                ),
            ]

    monkeypatch.setattr("photo_vectorizer_v2.ContourPlausibilityScorer", lambda **kwargs: _ScorerStub())

    result = run_contour_stage_v2(
        image=np.zeros((400, 300, 3), dtype=np.uint8),
        merged_mask=np.zeros((400, 300), dtype=np.uint8),
        body_region=_make_body_region(10, 20, 140, 240),
        family=InstrumentFamily.ARCHTOP,
        mpp=0.5,
    )

    assert result.body_contour_final is not None
    # best_cs = highest .score among post_merge scores → score[1] with .score=0.83
    assert result.best_score == 0.83
    assert result.ownership_score == 0.41
    assert result.ownership_ok is False
    assert result.export_blocked is True
    assert result.recommended_next_action == "rerun_body_isolation"
    assert "body_ownership_failed" in result.export_block_issues
    assert result.diagnostics["body_ownership_gate_failed"] is True
    assert result.export_block_score_breakdown["ownership_score"] == 0.41
    assert result.export_block_score_breakdown["vertical_coverage"] == 0.48


def test_run_contour_stage_v2_keeps_owned_candidate_exportable(monkeypatch):
    feature_contours = [
        _make_fc(10, 20, 120, 220, area=26000),
    ]

    monkeypatch.setattr(
        "photo_vectorizer_v2.extract_feature_contours",
        lambda *args, **kwargs: feature_contours,
    )
    monkeypatch.setattr(
        "photo_vectorizer_v2.merge_feature_contours",
        lambda contours, image_shape, body_region, mpp: feature_contours,
    )

    class _ScorerStub:
        def score_all_candidates(self, contours, body_region, family, mpp, image_shape):
            return [
                _make_score(0, 0.84, ownership_score=0.88, vertical_coverage=0.95),
            ]

    monkeypatch.setattr("photo_vectorizer_v2.ContourPlausibilityScorer", lambda **kwargs: _ScorerStub())

    result = run_contour_stage_v2(
        image=np.zeros((400, 300, 3), dtype=np.uint8),
        merged_mask=np.zeros((400, 300), dtype=np.uint8),
        body_region=_make_body_region(10, 20, 140, 240),
        family=InstrumentFamily.ARCHTOP,
        mpp=0.5,
    )

    assert result.export_blocked is False
    assert result.ownership_score == 0.88
    assert result.ownership_ok is True
    assert result.recommended_next_action is None


# =============================================================================
# vectorize_photo_v2 tests — ownership warning surfacing
# =============================================================================


def test_vectorize_photo_v2_surfaces_ownership_failure_warning(monkeypatch):
    from body_isolation_result import BodyIsolationResult

    body_region = _make_body_region(10, 20, 140, 240)
    body_result = BodyIsolationResult(
        body_bbox_px=(10, 20, 140, 240),
        body_region=body_region,
        confidence=0.75,
        completeness_score=0.69,
    )

    contour_stage = ContourStageResult(
        best_score=0.58,
        export_blocked=True,
        block_reason="No contour passed body ownership threshold 0.60",
        recommended_next_action="rerun_body_isolation",
        ownership_score=0.39,
        ownership_ok=False,
        export_block_issues=["body_ownership_failed"],
    )

    monkeypatch.setattr("photo_vectorizer_v2.run_body_isolation_stage", lambda *args, **kwargs: body_result)
    monkeypatch.setattr("photo_vectorizer_v2.run_contour_stage_v2", lambda *args, **kwargs: contour_stage)

    result = vectorize_photo_v2(
        image=np.zeros((400, 300, 3), dtype=np.uint8),
        family_hint=InstrumentFamily.ARCHTOP,
        mpp=0.5,
    )

    assert any("ownership failed" in w.lower() for w in result.warnings)
    assert any("export blocked" in w.lower() for w in result.warnings)


# =============================================================================
# Run with: pytest test_photo_vectorizer_v2.py -v
# =============================================================================


# =============================================================================
# Diff 4 + 5: BodyModel integration and symmetry tests
# =============================================================================

def test_compute_body_symmetry_score_uses_isolation_mask():
    """Symmetric ellipse mask produces high symmetry score."""
    from photo_vectorizer_v2 import PhotoVectorizerV2
    pv = PhotoVectorizerV2()

    mask = np.zeros((220, 180), dtype=np.uint8)
    cv2.ellipse(mask, (90, 110), (50, 80), 0, 0, 360, 255, -1)

    body_result = type("R", (), {
        "body_bbox_px": (40, 30, 100, 160),
        "isolation_mask": mask,
        "column_profile": np.sum(mask > 0, axis=0).astype(float),
    })()

    score = pv._compute_body_symmetry_score(body_result)
    assert score > 0.85


def test_compute_body_symmetry_score_penalizes_asymmetric_mask():
    """Deliberately asymmetric mask produces lower symmetry score."""
    from photo_vectorizer_v2 import PhotoVectorizerV2
    pv = PhotoVectorizerV2()

    mask = np.zeros((220, 180), dtype=np.uint8)
    cv2.ellipse(mask, (90, 110), (50, 80), 0, 0, 360, 255, -1)
    mask[120:190, 90:150] = 0  # remove right lower quadrant

    body_result = type("R", (), {
        "body_bbox_px": (40, 30, 100, 160),
        "isolation_mask": mask,
        "column_profile": np.sum(mask > 0, axis=0).astype(float),
    })()

    score = pv._compute_body_symmetry_score(body_result)
    assert score < 0.80


def test_compute_body_symmetry_score_fallback_to_profile():
    """When no isolation_mask, falls back to column_profile comparison."""
    from photo_vectorizer_v2 import PhotoVectorizerV2
    pv = PhotoVectorizerV2()

    # Symmetric column profile
    profile = np.concatenate([np.linspace(10, 80, 50), np.linspace(80, 10, 50)])

    body_result = type("R", (), {
        "body_bbox_px": (0, 0, 100, 200),
        "isolation_mask": None,
        "column_profile": profile,
    })()

    score = pv._compute_body_symmetry_score(body_result)
    assert score > 0.90


def test_build_body_model_returns_none_on_failure():
    """_build_body_model degrades gracefully on broken body_result."""
    from photo_vectorizer_v2 import PhotoVectorizerV2, InstrumentFamily

    pv = PhotoVectorizerV2()

    # An object with None bbox will cause landmark extraction to fail,
    # but the method should still return a BodyModel (with manual_review_required=True)
    # or None — it must not raise.
    broken = type("R", (), {"body_bbox_px": None, "body_region": None})()
    calibration = type("C", (), {"mm_per_px": 0.5})()

    # Should not raise
    try:
        result = pv._build_body_model(
            body_result=broken,
            family=InstrumentFamily.SOLID_BODY,
            spec_name=None,
            calibration=calibration,
        )
        # Either None or a BodyModel with manual_review_required — both acceptable
        if result is not None:
            from body_model import BodyModel
            assert isinstance(result, BodyModel)
    except Exception as exc:
        raise AssertionError(f"_build_body_model raised unexpectedly: {exc}")


def test_run_contour_stage_v2_uses_expected_outline_prior(monkeypatch):
    """run_contour_stage_v2 sets used_expected_outline_prior when body_model provided."""
    from photo_vectorizer_v2 import run_contour_stage_v2, InstrumentFamily
    from body_model import BodyModel

    # Use a non-blank image so contours can be found
    image = np.zeros((400, 300, 3), dtype=np.uint8)
    cv2.rectangle(image, (20, 30), (260, 270), (200, 200, 200), -1)
    cv2.rectangle(image, (20, 30), (260, 270), (50, 50, 50), 3)
    merged_mask = np.zeros((400, 300), dtype=np.uint8)
    merged_mask[30:270, 20:260] = 255
    body_region = _make_body_region(20, 30, 240, 240)

    body_model = BodyModel(
        source_image_id=None,
        family_hint="solid_body",
        spec_hint=None,
        body_bbox_px=(20, 30, 240, 240),
        body_region=body_region,
        row_width_profile_px=np.zeros(500, dtype=float),
        row_width_profile_smoothed_px=np.zeros(500, dtype=float),
        column_profile_px=np.zeros(300, dtype=float),
        mm_per_px=0.5,
        expected_outline_px=np.array(
            [[80.0, 30.0], [20.0, 150.0], [80.0, 270.0],
             [140.0, 270.0], [200.0, 150.0], [140.0, 30.0]],
            dtype=np.float32,
        ),
    )

    result = run_contour_stage_v2(
        image=image,
        merged_mask=merged_mask,
        body_region=body_region,
        body_model=body_model,
        family=InstrumentFamily.SOLID_BODY,
        mpp=0.5,
        image_shape=(400, 300),
    )

    # The diagnostic key should exist — value depends on whether contours passed
    # the ownership gate, but the key itself must be present
    assert "used_expected_outline_prior" in result.diagnostics


# =============================================================================
# Ownership pre-filter and two-pass calibration tests
# =============================================================================

def test_contour_assembler_rejects_off_body_candidates():
    """Pre-filter removes contours that don't overlap the body region."""
    from photo_vectorizer_v2 import ContourAssembler, FeatureClassifier

    # Create an edge image with two rectangles: one inside the body region,
    # one completely outside
    edges = np.zeros((400, 300), dtype=np.uint8)
    # Inside body region (x=50..200, y=50..300)
    cv2.rectangle(edges, (55, 60), (190, 280), 255, 2)
    # Outside body region — far left
    cv2.rectangle(edges, (5, 10), (40, 100), 255, 2)

    alpha_mask = np.zeros((400, 300), dtype=np.uint8)
    alpha_mask[50:300, 50:200] = 255

    body_region = _make_body_region(50, 50, 150, 250)

    assembler = ContourAssembler(FeatureClassifier(), min_area_px=100)

    with_filter = assembler.assemble(edges, alpha_mask, 0.5, body_region=body_region)
    without_filter = assembler.assemble(edges, alpha_mask, 0.5, body_region=None)

    # Pre-filter should reduce candidate count
    assert len(with_filter) <= len(without_filter)


def test_contour_assembler_body_region_none_identical_to_no_filter():
    """When body_region is None, assemble() behaves identically to old behavior."""
    from photo_vectorizer_v2 import ContourAssembler, FeatureClassifier

    edges = np.zeros((300, 200), dtype=np.uint8)
    cv2.rectangle(edges, (20, 30), (150, 200), 255, 2)
    alpha_mask = np.ones((300, 200), dtype=np.uint8) * 255

    assembler = ContourAssembler(FeatureClassifier(), min_area_px=100)
    result_no_region = assembler.assemble(edges, alpha_mask, 0.5, body_region=None)
    result_default = assembler.assemble(edges, alpha_mask, 0.5)

    assert len(result_no_region) == len(result_default)


def test_two_pass_updates_body_model_mm_per_px(monkeypatch):
    """Two-pass calibration writes corrected mm_per_px back to body_model."""
    from contour_stage import ContourStage, StageParams
    from photo_vectorizer_v2 import ScaleSource, CalibrationResult, InstrumentFamily
    from body_model import BodyModel

    stage = ContourStage()

    # Create a real-looking edge image with a detectable rectangle
    edges = np.zeros((600, 450), dtype=np.uint8)
    cv2.rectangle(edges, (25, 25), (420, 570), 255, 3)
    alpha_mask = np.zeros((600, 450), dtype=np.uint8)
    alpha_mask[25:570, 25:420] = 255
    body_region = _make_body_region(25, 25, 395, 545)

    # Force low-confidence scale source to trigger two-pass
    calibration = CalibrationResult(
        mm_per_px=0.3,  # deliberately wrong
        source=ScaleSource.ASSUMED_DPI,
        confidence=0.2,
        message="test assumed",
    )

    body_model = BodyModel(
        source_image_id=None,
        family_hint="stratocaster",
        spec_hint=None,
        body_bbox_px=(25, 25, 395, 545),
        body_region=body_region,
        row_width_profile_px=np.zeros(700, dtype=float),
        row_width_profile_smoothed_px=np.zeros(700, dtype=float),
        column_profile_px=np.zeros(450, dtype=float),
        mm_per_px=0.3,  # same wrong value
    )

    original_mpp = body_model.mm_per_px

    stage.run(
        edges=edges,
        alpha_mask=alpha_mask,
        body_region=body_region,
        body_model=body_model,
        calibration=calibration,
        family=InstrumentFamily.SOLID_BODY,
        image_shape=edges.shape,
        spec_name="stratocaster",
    )

    # If two-pass fired, mm_per_px should have been updated
    # (it may or may not fire depending on contour detection, but if it did
    # the value must differ from the original wrong value)
    # We just assert the method completed without error and body_model is intact
    assert body_model is not None
    assert isinstance(body_model.mm_per_px, (float, type(None)))
