from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from body_isolation_stage import BodyIsolationParams, BodyIsolationStage


@dataclass
class _BodyRegionStub:
    x: int = 20
    y: int = 30
    width: int = 40
    height: int = 60
    confidence: float = 0.75
    notes: list = field(default_factory=list)


class _BodyIsolatorStub:
    def __init__(self, region: _BodyRegionStub):
        self.region = region
        self.body_width_min = 0.40
        self.smooth_window = 15
        self.use_adaptive = False

    def isolate(self, image, fg_mask=None, original_image=None):
        return self.region


def test_body_region_expansion_profile_is_registered():
    params = BodyIsolationParams(profile="body_region_expansion")
    stage = BodyIsolationStage(_BodyIsolatorStub(_BodyRegionStub()))
    image = np.zeros((120, 100, 3), dtype=np.uint8)

    result = stage.run(image, params=params)

    assert result.diagnostics["retry_profile_used"] == "body_region_expansion"
    assert result.diagnostics["bbox_expand_ratio"] > 0.0
    assert result.diagnostics["allow_vertical_growth"] is True
    assert result.diagnostics["allow_lower_bout_growth"] is True


def test_expand_body_bbox_grows_bbox_for_body_region_expansion():
    stage = BodyIsolationStage(_BodyIsolatorStub(_BodyRegionStub()))
    params = BodyIsolationParams(
        profile="body_region_expansion",
        bbox_expand_ratio=0.10,
        allow_vertical_growth=True,
        allow_lower_bout_growth=True,
        upper_bound_expand_pct=0.06,
        lower_bound_expand_pct=0.18,
    )

    expanded = stage._expand_body_bbox(
        image_shape=(160, 120),
        bbox=(20, 30, 40, 60),
        params=params,
    )

    assert expanded[0] < 20
    assert expanded[1] < 30
    assert expanded[2] > 40
    assert expanded[3] > 60


def test_run_uses_expanded_bbox_in_stage_output():
    stage = BodyIsolationStage(_BodyIsolatorStub(_BodyRegionStub()))
    image = np.zeros((140, 100, 3), dtype=np.uint8)
    fg_mask = np.zeros((140, 100), dtype=np.uint8)
    fg_mask[20:118, 18:70] = 255

    result = stage.run(
        image,
        fg_mask=fg_mask,
        params=BodyIsolationParams(profile="body_region_expansion"),
    )

    assert result.body_bbox_px != (20, 30, 40, 60)
    assert result.diagnostics["raw_body_bbox_px"] == (20, 30, 40, 60)
    assert result.diagnostics["expanded_body_bbox_px"] == result.body_bbox_px


def test_body_region_expansion_changes_isolation_mask_not_just_profile_name():
    stage = BodyIsolationStage(_BodyIsolatorStub(_BodyRegionStub()))
    image = np.zeros((140, 100, 3), dtype=np.uint8)
    fg_mask = np.zeros((140, 100), dtype=np.uint8)

    # FG reaches beyond the raw body bbox, especially downward.
    fg_mask[25:122, 18:72] = 255

    baseline = stage.run(
        image,
        fg_mask=fg_mask,
        params=BodyIsolationParams(),
    )
    expanded = stage.run(
        image,
        fg_mask=fg_mask,
        params=BodyIsolationParams(profile="body_region_expansion"),
    )

    assert np.count_nonzero(expanded.isolation_mask) > np.count_nonzero(baseline.isolation_mask)
    assert expanded.completeness_score >= baseline.completeness_score


def test_lower_band_recovery_can_fill_gap_inside_expanded_roi():
    stage = BodyIsolationStage(_BodyIsolatorStub(_BodyRegionStub()))
    image_shape = (140, 100)
    bbox = (20, 20, 50, 90)
    fg_mask = np.zeros(image_shape, dtype=np.uint8)

    # Upper/middle body present, lower bout fragment present, with a gap between.
    fg_mask[25:70, 25:65] = 255
    fg_mask[86:108, 20:70] = 255

    mask = stage._make_isolation_mask(
        image_shape=image_shape,
        bbox=bbox,
        fg_mask=fg_mask,
        params=BodyIsolationParams(
            bbox_expand_ratio=0.10,
            allow_vertical_growth=True,
            allow_lower_bout_growth=True,
        ),
    )

    # Gap area should gain recovered coverage.
    assert np.count_nonzero(mask[72:88, 25:65]) > 0
