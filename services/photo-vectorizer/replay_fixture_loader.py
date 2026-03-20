from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from body_isolation_result import BodyIsolationResult
from replay_objects import hydrate_body_result, make_contour_stage_result


@dataclass
class ReplayRegressionCase:
    case_id: str
    family: Optional[str]
    expected_action: Optional[str]
    manual_review_required: bool
    payload: Dict[str, Any]


def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def regression_fixture_path(case_id: str) -> Path:
    return fixtures_dir() / f"regression_replay_{case_id}.json"


def load_regression_case(case_id: str) -> ReplayRegressionCase:
    payload = json.loads(regression_fixture_path(case_id).read_text(encoding="utf-8"))
    return ReplayRegressionCase(
        case_id=payload["case_id"],
        family=payload.get("family"),
        expected_action=payload.get("expected_action"),
        manual_review_required=bool(payload.get("manual_review_required", False)),
        payload=payload,
    )


def load_regression_cases(case_ids: Optional[List[str]] = None) -> List[ReplayRegressionCase]:
    paths = sorted(fixtures_dir().glob("regression_replay_*.json"))
    cases = [load_regression_case(p.stem.replace("regression_replay_", "")) for p in paths]
    if case_ids is None:
        return cases
    wanted = set(case_ids)
    return [c for c in cases if c.case_id in wanted]


def make_serialized_body_result(payload: Dict[str, Any]) -> BodyIsolationResult:
    """
    Build a concrete BodyIsolationResult instance from regression fixture payload.

    Unlike the older helper, this preserves top-level replay diagnostics so the
    same object can be passed directly into full replay execution.
    """
    body_payload = dict(payload.get("body_result", {}) or {})
    if "body_region" not in body_payload:
        bbox = list(body_payload.get("body_bbox_px", [0, 0, 0, 0]))
        body_payload["body_region"] = {
            "x": int(bbox[0]) if len(bbox) > 0 else 0,
            "y": int(bbox[1]) if len(bbox) > 1 else 0,
            "width": int(bbox[2]) if len(bbox) > 2 else 0,
            "height": int(bbox[3]) if len(bbox) > 3 else 0,
            "confidence": float(body_payload.get("confidence", 0.0)),
        }
    result = BodyIsolationResult.from_payload(body_payload)
    return hydrate_body_result(result, payload)


def make_serialized_contour_result(payload: Dict[str, Any]):
    """
    Build a concrete ContourStageResult instance from regression fixture payload.

    This replaces synthetic runtime-only stubs in replay execution so the coach
    loop works against the same serialized object shape used by replay summary.
    """
    return make_contour_stage_result(payload)
