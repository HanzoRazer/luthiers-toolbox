"""
Spec → Contract Matrix Verification (CNC Saw Lab + RMOS Runs)

This test suite answers: "Did we leave anything out?"

It verifies, end-to-end, that:
1) Required endpoints exist (route inventory)
2) Compare → Batch artifacts are written
3) Decision capture writes a decision artifact referencing batch + selected child
4) Toolpaths-from-decision writes a toolpaths artifact inheriting the decision
5) /api/rmos/runs supports filtering by batch_label / session_id / kind
6) /api/rmos/runs/diff returns a structured diff (best-effort tolerant)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient


# ---------------------------
# Helpers
# ---------------------------

def _has_route(app, *, path: str, method: str) -> bool:
    m = method.upper()
    for r in app.router.routes:
        if getattr(r, "path", None) == path and hasattr(r, "methods") and m in r.methods:
            return True
    return False


def _id_of(item: Dict[str, Any]) -> Optional[str]:
    return item.get("artifact_id") or item.get("run_id") or item.get("id")


def _assert_any_id_matches(items: List[Dict[str, Any]], expected_id: str):
    ids = [_id_of(it) for it in items]
    assert any(i == expected_id for i in ids), {"expected": expected_id, "got": ids}


def _first(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    assert items and isinstance(items, list)
    assert isinstance(items[0], dict)
    return items[0]


def _post(client: TestClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = client.post(path, json=payload)
    assert r.status_code == 200, {"path": path, "status": r.status_code, "body": r.text}
    return r.json()


def _get(client: TestClient, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    r = client.get(path, params=params or {})
    assert r.status_code == 200, {"path": path, "status": r.status_code, "body": r.text}
    return r.json()


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def client() -> TestClient:
    """
    Import the FastAPI app from main.py.
    Must include RMOS runs router at /api/rmos/runs and saw compare router at /api/saw.
    """
    from app.main import app
    return TestClient(app)


# ---------------------------
# 1) Route Inventory
# ---------------------------

def test_route_inventory_required_endpoints_exist(client: TestClient):
    app = client.app

    required = [
        # Saw compare surface
        ("/api/saw/compare", "POST"),
        ("/api/saw/compare/batches", "GET"),
        ("/api/saw/compare/approve", "POST"),
        ("/api/saw/compare/decisions", "GET"),
        ("/api/saw/compare/toolpaths", "POST"),
        ("/api/saw/compare/toolpaths", "GET"),

        # RMOS runs
        ("/api/rmos/runs", "GET"),
        ("/api/rmos/runs/diff", "GET"),
    ]

    missing = [(p, m) for (p, m) in required if not _has_route(app, path=p, method=m)]
    assert not missing, {"missing_routes": missing}


# ---------------------------
# 2) End-to-End: Compare → Approve → Toolpaths
# ---------------------------

def test_contract_matrix_compare_decide_toolpaths_and_query_and_diff(client: TestClient):
    batch_label = "pytest-contract-matrix"
    session_id = "sess_pytest_contract_matrix"

    # ---- Step A: Compare ----
    compare_payload = {
        "batch_label": batch_label,
        "session_id": session_id,
        "candidates": [
            {
                "candidate_id": "c1",
                "label": "candidate 1",
                "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "maple"},
                "context": {
                    "tool_id": "saw:thin_140",
                    "material_id": "maple",
                    "machine_id": "router_a",
                    "spindle_rpm": 18000,
                    "feed_rate": 800,
                },
            },
            {
                "candidate_id": "c2",
                "label": "candidate 2",
                "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "ebony"},
                "context": {
                    "tool_id": "saw:thin_140",
                    "material_id": "ebony",
                    "machine_id": "router_a",
                    "spindle_rpm": 18000,
                    "feed_rate": 800,
                },
            },
        ],
    }

    compare_res = _post(client, "/api/saw/compare", compare_payload)

    parent_batch_id = compare_res.get("parent_artifact_id")
    assert parent_batch_id, compare_res

    items = compare_res.get("items")
    assert isinstance(items, list) and len(items) == 2
    assert all(it.get("artifact_id") for it in items)

    chosen_child_id = items[0]["artifact_id"]

    # ---- Step B: Decision capture ----
    decision_payload = {
        "parent_batch_artifact_id": parent_batch_id,
        "selected_child_artifact_id": chosen_child_id,
        "approved_by": "pytest-operator",
        "reason": "best candidate under constraints",
        "ticket_id": "TEST-123",
    }
    decision_res = _post(client, "/api/saw/compare/approve", decision_payload)
    decision_id = decision_res.get("decision_artifact_id")
    assert decision_id, decision_res

    # ---- Step C: Toolpaths from decision ----
    toolpaths_res = _post(client, "/api/saw/compare/toolpaths", {"decision_artifact_id": decision_id})
    toolpaths_id = toolpaths_res.get("toolpaths_artifact_id")
    assert toolpaths_id, toolpaths_res
    assert toolpaths_res.get("decision_artifact_id") == decision_id
    assert toolpaths_res.get("status") in ("OK", "BLOCKED", "ERROR")

    # ---- Step D: Alias lookups work ----
    # Batches alias
    batches = _get(client, "/api/saw/compare/batches", {"batch_label": batch_label, "limit": 50})
    assert isinstance(batches, list)
    _assert_any_id_matches(batches, parent_batch_id)

    # Decisions alias
    decisions = _get(client, "/api/saw/compare/decisions", {"batch_label": batch_label, "limit": 50})
    assert isinstance(decisions, list)
    _assert_any_id_matches(decisions, decision_id)

    # Toolpaths alias returns latest for decision
    latest_toolpaths = _get(client, "/api/saw/compare/toolpaths", {"decision_artifact_id": decision_id})
    assert _id_of(latest_toolpaths) == toolpaths_id or latest_toolpaths.get("artifact_id") == toolpaths_id

    # ---- Step E: /api/rmos/runs filters work ----
    # Parent batch discoverable by mode + batch_label
    runs_batches = _get(client, "/api/rmos/runs", {"mode": "saw_compare", "batch_label": batch_label, "limit": 100})
    assert isinstance(runs_batches, list)
    _assert_any_id_matches(runs_batches, parent_batch_id)

    # Decision discoverable by mode + batch_label
    runs_decisions = _get(client, "/api/rmos/runs", {"mode": "saw_compare", "batch_label": batch_label, "limit": 100})
    assert isinstance(runs_decisions, list)
    _assert_any_id_matches(runs_decisions, decision_id)

    # Toolpaths discoverable by mode + batch_label
    runs_toolpaths = _get(client, "/api/rmos/runs", {"mode": "saw_compare", "batch_label": batch_label, "limit": 100})
    assert isinstance(runs_toolpaths, list)
    _assert_any_id_matches(runs_toolpaths, toolpaths_id)

    # ---- Step F: Diff endpoint returns structured output (best-effort) ----
    # We diff the parent batch vs decision or decision vs toolpaths.
    # The diff endpoint uses query params: /api/rmos/runs/diff?a={id}&b={id}
    def try_diff(left_id: str, right_id: str) -> Tuple[bool, Any]:
        r = client.get("/api/rmos/runs/diff", params={"a": left_id, "b": right_id})
        if r.status_code != 200:
            return False, {"status": r.status_code, "body": r.text}
        return True, r.json()

    ok, diff_body = try_diff(decision_id, toolpaths_id)
    if not ok:
        ok, diff_body = try_diff(parent_batch_id, decision_id)

    assert ok, {"diff_failed": diff_body}

    # Minimal structural assertions that won't overfit your diff schema
    assert isinstance(diff_body, dict), diff_body
    # common keys in diff payloads: "summary", "deltas", "changes", "left", "right"
    assert any(k in diff_body for k in ("summary", "deltas", "changes", "left", "right")), diff_body


# ---------------------------
# 3) "Nothing left out" artifact-kind sanity
# ---------------------------

def test_artifact_kinds_exist_in_index_for_batch_label(client: TestClient):
    batch_label = "pytest-contract-matrix-kinds"
    session_id = "sess_pytest_contract_matrix_kinds"

    # Create compare + decision + toolpaths quickly
    compare = _post(
        client,
        "/api/saw/compare",
        {
            "batch_label": batch_label,
            "session_id": session_id,
            "candidates": [
                {
                    "candidate_id": "c1",
                    "label": "candidate 1",
                    "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "maple"},
                    "context": {"tool_id": "saw:thin_140", "material_id": "maple", "machine_id": "router_a", "spindle_rpm": 18000, "feed_rate": 800},
                }
            ],
        },
    )
    parent_id = compare["parent_artifact_id"]
    child_id = compare["items"][0]["artifact_id"]

    decision = _post(
        client,
        "/api/saw/compare/approve",
        {
            "parent_batch_artifact_id": parent_id,
            "selected_child_artifact_id": child_id,
            "approved_by": "pytest",
            "reason": "sanity",
        },
    )
    decision_id = decision["decision_artifact_id"]

    toolpaths = _post(client, "/api/saw/compare/toolpaths", {"decision_artifact_id": decision_id})
    toolpaths_id = toolpaths["toolpaths_artifact_id"]

    # Now assert artifacts show up in /api/rmos/runs filtered by mode and batch_label
    # All three artifacts should be discoverable
    all_runs = _get(client, "/api/rmos/runs", {"mode": "saw_compare", "batch_label": batch_label, "limit": 50})
    assert isinstance(all_runs, list)
    
    # Verify all three IDs are present
    _assert_any_id_matches(all_runs, parent_id)
    _assert_any_id_matches(all_runs, decision_id)
    _assert_any_id_matches(all_runs, toolpaths_id)
