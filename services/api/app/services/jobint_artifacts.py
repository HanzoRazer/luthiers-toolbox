"""Helper utilities for extracting JobInt artifacts (geometry, plan, moves).

B20 introduces optional job intelligence fields (geometry_loops, plan_request,
moves, moves_path, baseline_id). Pipeline and adaptive routers can use this
helper to gather whatever context is available without duplicating heuristics.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


ArtifactTuple = Tuple[
    Optional[List[Dict[str, Any]]],
    Optional[Dict[str, Any]],
    Optional[List[Dict[str, Any]]],
    Optional[str],
]


def extract_jobint_artifacts(ctx: Dict[str, Any]) -> ArtifactTuple:
    """Best-effort extraction of JobInt artifacts from a planning context.

    Args:
        ctx: Arbitrary dictionary built during a pipeline/adaptive run.

    Returns:
        Tuple of (geometry_loops, plan_request, moves, moves_path).
    """

    geometry_loops: Optional[List[Dict[str, Any]]] = None
    plan_request: Optional[Dict[str, Any]] = None
    moves: Optional[List[Dict[str, Any]]] = None
    moves_path: Optional[str] = None

    candidate_plan = (
        ctx.get("plan_request")
        or ctx.get("adaptive_plan_request")
        or ctx.get("plan")
        or ctx.get("params")
    )
    if isinstance(candidate_plan, dict):
        plan_request = candidate_plan
        loops = candidate_plan.get("loops")
        if isinstance(loops, list):
            geometry_loops = loops

    candidate_moves = (
        ctx.get("moves")
        or ctx.get("adaptive_moves")
        or ctx.get("toolpath_moves")
    )
    if isinstance(candidate_moves, list):
        moves = candidate_moves

    if isinstance(ctx.get("moves_path"), str):
        moves_path = ctx["moves_path"]

    return geometry_loops, plan_request, moves, moves_path


def build_jobint_payload(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a JSON-safe payload for job intelligence logging.

    Args:
        ctx: Arbitrary planning context shared across adaptive/pipeline flows.

    Returns:
        Dict with optional keys geometry_loops/plan_request/moves/moves_path,
        or None if no artifacts could be extracted.
    """

    geometry_loops, plan_request, moves, moves_path = extract_jobint_artifacts(ctx)

    payload: Dict[str, Any] = {}

    if geometry_loops is not None:
        payload["geometry_loops"] = deepcopy(geometry_loops)
    if plan_request is not None:
        payload["plan_request"] = deepcopy(plan_request)
    if moves is not None:
        payload["moves"] = deepcopy(moves)
    if moves_path is not None:
        payload["moves_path"] = moves_path

    return payload or None
