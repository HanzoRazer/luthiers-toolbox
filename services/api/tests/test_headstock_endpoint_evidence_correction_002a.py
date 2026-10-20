"""HEADSTOCK-ENDPOINT-EVIDENCE-CORRECTION-002A.

The spline path stays absent. The feasibility record may not call that absence
"broken" unless a runtime witness shows the routed client actually requests it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    REPO_ROOT
    / "docs"
    / "investigations"
    / "headstock-integration-feasibility-002_2026-10-19"
)
CLIENT = REPO_ROOT / "packages" / "client" / "src"
SPLINE = "/api/dxf/spline/evaluate"
CLASSIFICATION = "REACHABLE_VISIBLE_FAILURE"


def _inventory() -> dict:
    return json.loads((EVIDENCE / "inventory.json").read_text(encoding="utf-8"))


def _spline_row() -> dict:
    rows = [row for row in _inventory()["endpoints"] if row["path"] == SPLINE]
    assert len(rows) == 1
    return rows[0]


def _walk(routes, prefix=""):
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            original = getattr(route, "original_router", None)
            if original is not None:
                yield from _walk(original.routes, prefix + (getattr(context, "prefix", "") or ""))
            continue
        path = getattr(route, "path", None)
        if path is not None:
            yield prefix + path, getattr(route, "methods", None) or set()


def test_mounted_routes_do_not_include_spline_evaluate():
    from app.main import app

    mounted = [path for path, _methods in _walk(app.routes)]
    assert SPLINE not in mounted
    assert not any("spline/evaluate" in path for path in mounted)

    response = TestClient(app).post(SPLINE, json={"samples": 8})
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"


def test_inlay_workspace_is_the_only_runtime_importer():
    router = (CLIENT / "router" / "index.ts").read_text(encoding="utf-8")
    route = router.split('path: "/art-studio/inlay-workspace"', 1)[1][:400]
    assert "InlayWorkspaceShell.vue" in route

    shell = (CLIENT / "views" / "art-studio" / "InlayWorkspaceShell.vue").read_text(encoding="utf-8")
    assert "useDxfImport" in shell
    assert "dxfImport.loadFile" in shell
    assert "dxfImport.error" in shell

    callers = []
    for path in CLIENT.rglob("*"):
        if path.suffix not in {".ts", ".vue"} or not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.endswith("composables/useDxfImport.ts") or "/__tests__/" in rel:
            continue
        if "useDxfImport(" in path.read_text(encoding="utf-8", errors="replace"):
            callers.append(rel)
    assert callers == ["packages/client/src/views/art-studio/InlayWorkspaceShell.vue"]


def test_inventory_records_witnessed_failure_without_active_broken_label():
    row = _spline_row()
    expected = {
        "class": CLASSIFICATION,
        "prior_classification": "broken",
        "prior_classification_status": "withdrawn",
        "route_present": False,
        "direct_post_status": 404,
        "workflow_reachable": True,
        "endpoint_request_observed": False,
        "visible_behavior": "Error: DxfParser not loaded",
        "processing_continues": False,
        "substitute_geometry_shown": False,
        "kind": "manufacturing",
    }
    assert {key: row[key] for key in expected} == expected


def test_narrative_records_match_the_inventory_classification():
    audit = (EVIDENCE / "BACKEND_ENDPOINT_AUDIT.md").read_text(encoding="utf-8")
    witness = (EVIDENCE / "SPLINE_EVALUATE_WITNESS.md").read_text(encoding="utf-8")

    assert CLASSIFICATION in audit
    assert CLASSIFICATION in witness
    assert "Prior statement from PR #444, withdrawn" in audit
    assert "Error: DxfParser not loaded" in witness
    assert "spline/evaluate" in witness

    # The current spline row is the witnessed class, not the withdrawn word.
    spline_section = audit.split("## Spline evaluate, corrected", 1)[1]
    assert f"Current class: **{CLASSIFICATION}**" in spline_section
    assert "class | broken" not in audit
