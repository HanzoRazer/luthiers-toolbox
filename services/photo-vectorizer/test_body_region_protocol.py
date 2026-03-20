from __future__ import annotations

from body_isolation_result import BodyRegionProtocol, ReplayBodyRegion
from photo_vectorizer_v2 import BodyRegion


def test_replay_body_region_satisfies_protocol():
    region = ReplayBodyRegion(
        x=12,
        y=24,
        width=180,
        height=220,
        confidence=0.87,
    )

    assert isinstance(region, BodyRegionProtocol)
    assert region.bbox == (12, 24, 180, 220)
    assert region.height_px == 220


def test_live_body_region_satisfies_protocol():
    region = BodyRegion(
        x=8,
        y=16,
        width=140,
        height=210,
        confidence=0.91,
        neck_end_row=30,
        max_body_width_px=140,
    )

    assert isinstance(region, BodyRegionProtocol)
    assert region.bbox == (8, 16, 140, 210)
    assert region.height_px == 210
