from __future__ import annotations

from body_isolation_result import ReplayBodyRegion, BodyRegionProtocol
from replay_fixture_loader import load_regression_case, make_serialized_body_result
from replay_objects import (
    advance_contour_stage_result,
    hydrate_body_result,
    make_contour_stage_result,
)


def test_make_contour_stage_result_builds_concrete_object_from_fixture():
    case = load_regression_case("smart_guitar")

    result = make_contour_stage_result(case.payload)

    assert result.best_score == 0.58
    assert result.ownership_score == 0.39
    assert result.ownership_ok is False
    assert "retry_attempts" in result.diagnostics
    assert len(result.diagnostics["retry_attempts"]) == 2


def test_advance_contour_stage_result_applies_retry_state():
    case = load_regression_case("archtop")
    result = make_contour_stage_result(case.payload)

    updated = advance_contour_stage_result(
        result,
        score_after=0.70,
        ownership_score_after=0.63,
        ownership_ok_after=True,
        retry_profile_used="body_region_expansion",
        retry_iteration=1,
    )

    assert updated.best_score == 0.70
    assert updated.ownership_score == 0.63
    assert updated.ownership_ok is True
    assert updated.diagnostics["replay_retry_iteration"] == 1
    assert updated.diagnostics["replay_retry_profile_used"] == "body_region_expansion"


def test_hydrate_body_result_preserves_body_diagnostics():
    case = load_regression_case("benedetto")
    body = make_serialized_body_result(case.payload)

    hydrated = hydrate_body_result(body, case.payload)

    assert hydrated.body_bbox_px == tuple(case.payload["body_result"]["body_bbox_px"])
    assert isinstance(hydrated.diagnostics, dict)


def test_contour_stage_result_round_trips_payload():
    case = load_regression_case("smart_guitar")
    result = make_contour_stage_result(case.payload)

    payload = result.to_payload()
    restored = result.from_payload(payload)

    assert restored.best_score == result.best_score
    assert restored.ownership_score == result.ownership_score
    assert restored.ownership_ok == result.ownership_ok
    assert restored.export_block_issues == result.export_block_issues
    assert restored.diagnostics["retry_attempts"] == result.diagnostics["retry_attempts"]


def test_body_isolation_result_round_trips_payload():
    case = load_regression_case("archtop")
    body = make_serialized_body_result(case.payload)

    payload = body.to_payload()
    restored = body.from_payload(payload)

    assert restored.body_bbox_px == body.body_bbox_px
    assert restored.completeness_score == body.completeness_score
    assert restored.border_contact_likely == body.border_contact_likely
    assert restored.neck_inclusion_likely == body.neck_inclusion_likely
    assert isinstance(restored.body_region, ReplayBodyRegion)


def test_replay_body_region_round_trips_as_typed_dataclass():
    case = load_regression_case("archtop")
    body = make_serialized_body_result(case.payload)

    payload = body.to_payload()
    restored = body.from_payload(payload)

    assert isinstance(restored.body_region, ReplayBodyRegion)
    assert restored.body_region.x == body.body_region.x
    assert restored.body_region.y == body.body_region.y
    assert restored.body_region.width == body.body_region.width
    assert restored.body_region.height == body.body_region.height
    assert restored.body_region.confidence == body.body_region.confidence


def test_body_region_protocol_accepts_replay_region():
    region = ReplayBodyRegion(x=1, y=2, width=3, height=4, confidence=0.5)

    assert isinstance(region, ReplayBodyRegion)
    assert isinstance(region, BodyRegionProtocol)

    assert region.bbox == (1, 2, 3, 4)
    assert region.height_px == 4
