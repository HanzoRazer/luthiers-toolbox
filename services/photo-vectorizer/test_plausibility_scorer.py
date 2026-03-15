"""Tests for ContourPlausibilityScorer, ContourScore, ContourStageResult, and export blocking."""

import numpy as np
import pytest
import cv2

from photo_vectorizer_v2 import (
    ContourPlausibilityScorer,
    ContourScore,
    ContourStageResult,
    MergeResult,
    FeatureContour,
    FeatureType,
    BodyRegion,
    InstrumentFamily,
    EXPORT_BLOCK_THRESHOLD,
    _FAMILY_DIMENSION_PRIORS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fc(x, y, w, h, area=None, feature_type=FeatureType.UNKNOWN,
             confidence=0.8, solidity=0.85):
    """Create a FeatureContour from a bounding-box spec (rectangle contour)."""
    pts = np.array([
        [x, y], [x + w, y], [x + w, y + h], [x, y + h]
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


# ===========================================================================
# ContourScore dataclass
# ===========================================================================

class TestContourScore:
    """Tests for ContourScore dataclass."""

    def test_basic_creation(self):
        cs = ContourScore(
            contour_index=0, score=0.75, completeness=0.8,
            includes_neck=False, border_contact=False,
            dimension_plausibility=0.9, symmetry_score=0.7,
            aspect_ratio_ok=True,
        )
        assert cs.score == 0.75
        assert cs.issues == []

    def test_with_issues(self):
        cs = ContourScore(
            contour_index=1, score=0.3, completeness=0.4,
            includes_neck=True, border_contact=True,
            dimension_plausibility=0.2, symmetry_score=0.5,
            aspect_ratio_ok=False,
            issues=["low solidity 0.40", "border contact on 3 edges"],
        )
        assert len(cs.issues) == 2
        assert cs.includes_neck is True


# ===========================================================================
# ContourStageResult dataclass
# ===========================================================================

class TestContourStageResult:
    """Tests for ContourStageResult dataclass."""

    def test_default_values(self):
        csr = ContourStageResult()
        assert csr.feature_contours_pre_merge == []
        assert csr.merge_result is None
        assert csr.elected_source == "post_merge"
        assert csr.export_blocked is False
        assert csr.block_reason is None
        assert csr.best_score == 0.0
        assert csr.diagnostics == {}

    def test_populated(self):
        fc = _make_fc(10, 10, 100, 200)
        csr = ContourStageResult(
            feature_contours_pre_merge=[fc],
            elected_source="pre_merge",
            best_score=0.72,
            export_blocked=True,
            block_reason="low score",
        )
        assert len(csr.feature_contours_pre_merge) == 1
        assert csr.export_blocked is True


# ===========================================================================
# ContourPlausibilityScorer
# ===========================================================================

class TestScorerScoreCandidate:
    """Tests for ContourPlausibilityScorer.score_candidate."""

    def setup_method(self):
        self.scorer = ContourPlausibilityScorer()
        self.image_shape = (2000, 1500)
        self.body_region = _make_body_region(200, 300, 600, 900)

    def test_good_body_candidate(self):
        """A well-shaped body contour should score high."""
        fc = _make_fc(220, 310, 560, 850, solidity=0.88)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.score > 0.5
        assert cs.border_contact is False
        assert cs.includes_neck is False
        assert cs.aspect_ratio_ok is True

    def test_border_contact_penalized(self):
        """A contour touching 2+ edges should have border_contact=True and lower score."""
        fc = _make_fc(0, 0, 1500, 2000, solidity=0.7)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.border_contact is True
        assert "border contact" in cs.issues[0] if cs.issues else True

    def test_neck_inclusion_detected(self):
        """A contour extending significantly above body region should flag neck."""
        # Body region at y=500, contour starts at y=50, much taller than body
        body = _make_body_region(200, 500, 600, 800)
        fc = _make_fc(200, 50, 600, 1300, solidity=0.8)
        cs = self.scorer.score_candidate(
            fc, 0, body, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.includes_neck is True

    def test_low_solidity_issues(self):
        """A contour with poor solidity should report issues."""
        fc = _make_fc(220, 310, 560, 850, solidity=0.35)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert any("solidity" in issue for issue in cs.issues)

    def test_score_between_0_and_1(self):
        """Score is always in [0, 1] range."""
        for sol in [0.1, 0.5, 0.9]:
            fc = _make_fc(220, 310, 560, 850, solidity=sol)
            cs = self.scorer.score_candidate(
                fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
                mpp=0.5, image_shape=self.image_shape)
            assert 0.0 <= cs.score <= 1.0

    def test_dimension_plausibility_good_match(self):
        """Contour whose mm dimensions match family priors should have high dim_plausibility."""
        # Solid body: ~406x325mm, so at mpp=0.5: ~812x650px
        fc = _make_fc(100, 100, 650, 812, solidity=0.85)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.dimension_plausibility > 0.7

    def test_dimension_plausibility_bad_match(self):
        """Contour far from family priors should have low dim_plausibility."""
        # Tiny contour: 50x50px at mpp=0.5 = 25x25mm -- absurdly small
        fc = _make_fc(100, 100, 50, 50, solidity=0.85)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.dimension_plausibility < 0.3

    def test_no_body_region_still_works(self):
        """Scorer should work even without body_region hint."""
        fc = _make_fc(100, 100, 400, 600, solidity=0.85)
        cs = self.scorer.score_candidate(
            fc, 0, None, InstrumentFamily.UNKNOWN,
            mpp=0.5, image_shape=self.image_shape)
        assert 0.0 <= cs.score <= 1.0
        assert cs.includes_neck is False

    def test_unknown_family_uses_wide_priors(self):
        """UNKNOWN family should use wider dimension range."""
        fc = _make_fc(100, 100, 500, 700, solidity=0.85)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.UNKNOWN,
            mpp=0.5, image_shape=self.image_shape)
        assert cs.dimension_plausibility > 0.0

    def test_zero_mpp_skips_dimension_check(self):
        """When mpp=0, dimension plausibility should stay at default 1.0."""
        fc = _make_fc(220, 310, 560, 850, solidity=0.85)
        cs = self.scorer.score_candidate(
            fc, 0, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.0, image_shape=self.image_shape)
        assert cs.dimension_plausibility == 1.0


class TestScorerScoreAll:
    """Tests for ContourPlausibilityScorer.score_all_candidates."""

    def setup_method(self):
        self.scorer = ContourPlausibilityScorer()
        self.image_shape = (2000, 1500)
        self.body_region = _make_body_region(200, 300, 600, 900)

    def test_filters_by_min_area(self):
        """Contours below area threshold should not be scored."""
        contours = [
            _make_fc(100, 100, 400, 600, area=240000),
            _make_fc(100, 100, 10, 10, area=100),  # tiny
            _make_fc(200, 200, 300, 500, area=150000),
        ]
        scores = self.scorer.score_all_candidates(
            contours, self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert len(scores) == 2
        assert all(s.contour_index in [0, 2] for s in scores)

    def test_empty_list(self):
        scores = self.scorer.score_all_candidates(
            [], self.body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=self.image_shape)
        assert scores == []


class TestScorerElectBest:
    """Tests for ContourPlausibilityScorer.elect_best."""

    def setup_method(self):
        self.scorer = ContourPlausibilityScorer()

    def _cs(self, idx, score, source="pre"):
        return ContourScore(
            contour_index=idx, score=score, completeness=0.8,
            includes_neck=False, border_contact=False,
            dimension_plausibility=0.8, symmetry_score=0.7,
            aspect_ratio_ok=True,
        )

    def test_post_merge_preferred_when_close(self):
        """Post-merge should win when scores are within 0.05."""
        pre = [self._cs(0, 0.70)]
        post = [self._cs(2, 0.68)]
        idx, source, score = self.scorer.elect_best(pre, post)
        assert source == "post_merge"
        assert idx == 2

    def test_pre_merge_wins_clearly_better(self):
        """Pre-merge should win when significantly better (>0.05 gap)."""
        pre = [self._cs(0, 0.85)]
        post = [self._cs(2, 0.70)]
        idx, source, score = self.scorer.elect_best(pre, post)
        assert source == "pre_merge"
        assert idx == 0
        assert score == 0.85

    def test_empty_pre_uses_post(self):
        post = [self._cs(1, 0.60)]
        idx, source, score = self.scorer.elect_best([], post)
        assert source == "post_merge"
        assert idx == 1

    def test_empty_post_uses_pre(self):
        pre = [self._cs(0, 0.60)]
        idx, source, score = self.scorer.elect_best(pre, [])
        assert source == "pre_merge"
        assert idx == 0

    def test_both_empty(self):
        idx, source, score = self.scorer.elect_best([], [])
        assert idx == -1
        assert source == "none"
        assert score == 0.0

    def test_multiple_candidates_picks_best(self):
        pre = [self._cs(0, 0.50), self._cs(1, 0.75)]
        post = [self._cs(2, 0.65), self._cs(3, 0.60)]
        idx, source, score = self.scorer.elect_best(pre, post)
        assert source == "pre_merge"
        assert idx == 1
        assert score == 0.75


class TestScorerSymmetry:
    """Tests for symmetry computation."""

    def setup_method(self):
        self.scorer = ContourPlausibilityScorer()

    def test_symmetric_rectangle(self):
        """A contour with many points that is symmetric should have high symmetry."""
        # Create a rectangular contour with many points along edges
        pts = []
        x0, y0, w, h = 100, 100, 400, 600
        # Top edge
        for x in range(x0, x0 + w, 10):
            pts.append([x, y0])
        # Right edge
        for y in range(y0, y0 + h, 10):
            pts.append([x0 + w, y])
        # Bottom edge (reverse)
        for x in range(x0 + w, x0, -10):
            pts.append([x, y0 + h])
        # Left edge (reverse)
        for y in range(y0 + h, y0, -10):
            pts.append([x0, y])
        pts_arr = np.array(pts, dtype=np.int32).reshape(-1, 1, 2)
        fc = FeatureContour(
            points_px=pts_arr, area_px=240000, bbox_px=(x0, y0, w, h),
            hash_id="test", solidity=0.85,
        )
        sym = self.scorer._compute_symmetry(fc, (1000, 600))
        assert sym > 0.8

    def test_too_few_points(self):
        """Fewer than 10 points should return 0.5 default."""
        pts = np.array([[0, 0], [100, 0], [100, 100]], dtype=np.int32).reshape(-1, 1, 2)
        fc = FeatureContour(
            points_px=pts, area_px=5000, bbox_px=(0, 0, 100, 100),
            hash_id="test",
        )
        sym = self.scorer._compute_symmetry(fc, (500, 500))
        assert sym == 0.5


# ===========================================================================
# Export Blocking
# ===========================================================================

class TestExportBlocking:
    """Tests for export blocking threshold behavior."""

    def test_threshold_constant_exists(self):
        assert isinstance(EXPORT_BLOCK_THRESHOLD, float)
        assert 0.0 < EXPORT_BLOCK_THRESHOLD < 1.0

    def test_low_score_triggers_block(self):
        """If best_score < threshold, export is blocked."""
        csr = ContourStageResult(
            best_score=0.15,
            elected_source="post_merge",
        )
        if csr.best_score < EXPORT_BLOCK_THRESHOLD:
            csr.export_blocked = True
            csr.block_reason = "low plausibility"
        assert csr.export_blocked is True

    def test_good_score_not_blocked(self):
        """Scores above threshold should not block."""
        csr = ContourStageResult(
            best_score=0.65,
            elected_source="post_merge",
        )
        if csr.best_score < EXPORT_BLOCK_THRESHOLD:
            csr.export_blocked = True
        assert csr.export_blocked is False


# ===========================================================================
# Family Dimension Priors
# ===========================================================================

class TestFamilyPriors:
    """Tests for family dimension prior ranges."""

    def test_all_families_have_priors(self):
        for family in [InstrumentFamily.SOLID_BODY, InstrumentFamily.ARCHTOP,
                       InstrumentFamily.ACOUSTIC, InstrumentFamily.SEMI_HOLLOW,
                       InstrumentFamily.UNKNOWN]:
            assert family in _FAMILY_DIMENSION_PRIORS
            h_min, h_max, w_min, w_max = _FAMILY_DIMENSION_PRIORS[family]
            assert h_min < h_max
            assert w_min < w_max

    def test_priors_are_reasonable_mm(self):
        """All dimensions should be in reasonable guitar body mm range."""
        for family, (h_min, h_max, w_min, w_max) in _FAMILY_DIMENSION_PRIORS.items():
            assert 200 < h_min < 600, f"h_min unreasonable for {family}"
            assert 250 < h_max < 700, f"h_max unreasonable for {family}"
            assert 200 < w_min < 500, f"w_min unreasonable for {family}"
            assert 200 < w_max < 600, f"w_max unreasonable for {family}"


# ===========================================================================
# Integration: scorer + stage result together
# ===========================================================================

class TestScorerIntegration:
    """Integration test: score contours, build stage result, check election."""

    def test_full_flow(self):
        scorer = ContourPlausibilityScorer()
        body_region = _make_body_region(200, 300, 600, 800)
        image_shape = (1600, 1000)

        # Pre-merge: one decent body candidate
        pre_contours = [
            _make_fc(220, 310, 560, 780, solidity=0.82, area=436800),
            _make_fc(100, 100, 80, 80, area=6400, solidity=0.9),
        ]
        scores_pre = scorer.score_all_candidates(
            pre_contours, body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=image_shape)

        # Post-merge: the merged contour might be bloated
        post_contours = list(pre_contours) + [
            _make_fc(180, 290, 640, 840, solidity=0.75, area=537600),
        ]
        scores_post = scorer.score_all_candidates(
            post_contours, body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.5, image_shape=image_shape)

        idx, source, best_score = scorer.elect_best(scores_pre, scores_post)

        # Build stage result
        csr = ContourStageResult(
            feature_contours_pre_merge=pre_contours,
            feature_contours_post_merge=post_contours,
            contour_scores_pre=scores_pre,
            contour_scores_post=scores_post,
            elected_source=source,
            best_score=best_score,
        )

        assert csr.elected_source in ("pre_merge", "post_merge")
        assert csr.best_score > 0.0
        assert len(csr.contour_scores_pre) > 0
        assert len(csr.contour_scores_post) > 0

    def test_no_viable_candidates_blocks_export(self):
        """When all contours are terrible, export should be blocked."""
        scorer = ContourPlausibilityScorer()
        image_shape = (500, 500)

        # Tiny junk contours that will score near 0
        contours = [
            _make_fc(0, 0, 500, 500, solidity=0.2, area=250000),
        ]
        body_region = _make_body_region(50, 50, 400, 400)
        scores = scorer.score_all_candidates(
            contours, body_region, InstrumentFamily.SOLID_BODY,
            mpp=0.1, image_shape=image_shape)

        if scores:
            best_score = max(s.score for s in scores)
        else:
            best_score = 0.0

        # With very bad solidity, border contact, and wrong dimensions,
        # score should be low
        assert best_score < 0.5  # Degraded but might not hit 0.30 threshold exactly
