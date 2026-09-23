"""LTB-CF2-INVENTORY-001: route discovery and inventory integrity.

Static metadata only. These tests do not call a generator or send a program.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ci.manufacturing_output_walk import (
    naive_walk,
    normalize_path,
    openapi_operations,
    reconcile,
    walk_live,
)
from _manufacturing_output_testkit import walk_routes

pytestmark = pytest.mark.allow_missing_request_id

PINNED = "1ebc49610b1690ef7d761ab598758c5db8d6193c"
INVENTORY = Path(__file__).resolve().parents[1] / "governance" / "manufacturing_output_inventory.json"
REPORT = Path(__file__).resolve().parents[1] / "governance" / "manufacturing_output_inventory.md"


class _Route:
    def __init__(self, path, methods=("GET",), include=True, model=None):
        self.path = path
        self.methods = set(methods)
        self.include_in_schema = include
        self.response_model = model
        self.name = "sample"
        self.endpoint = None


class _Mount:
    path = None

    def __init__(self, routes):
        self.routes = routes


class _IncludedRouter:
    def __init__(self, original, prefix=""):
        self.original_router = original
        self.include_context = type("Ctx", (), {"prefix": prefix})()


class _BrokenInclude:
    original_router = None
    include_context = None


class APIWebSocketRoute:
    path = "/ws/monitor"
    endpoint = None
    include_in_schema = True
    response_model = None
    name = "monitor"


def _schema_with(*items):
    paths = {}
    for method, path in items:
        paths.setdefault(path, {})[method.lower()] = {}
    return {"paths": paths}


def test_converter_strips_path_and_int_converters():
    # 6, 7
    assert normalize_path("/files/{file_path:path}") == "/files/{file_path}"
    assert normalize_path("/items/{id:int}") == "/items/{id}"


def test_recursive_walk_sees_mounts_the_naive_walk_drops():
    # 1, 2, 3
    child = _Route("/nested/gcode", methods={"POST"})
    mounted = _Mount([child])
    included = _IncludedRouter(type("Router", (), {"routes": [_Route("/child")]})(), "/api")
    live, unresolved = walk_live([mounted, included])
    naive = naive_walk([mounted, included])
    assert unresolved == []
    assert ("POST", "/nested/gcode") in {(item.method, item.path) for item in live}
    assert ("GET", "/api/child") in {(item.method, item.path) for item in live}
    assert naive == []
    assert len(naive) < len(live)


def test_pathless_object_and_broken_include_are_unresolved():
    # 4, 5
    class Mystery:
        pass

    _live, missed = walk_live([Mystery(), _BrokenInclude()])
    assert [item.type_name for item in missed] == ["Mystery", "_BrokenInclude"]


def test_head_options_are_skipped_and_hidden_routes_remain():
    # 8, 10
    route = _Route("/keep", methods={"GET", "HEAD", "OPTIONS"}, include=False)
    live, unresolved = walk_live([route])
    assert unresolved == []
    assert [(item.method, item.include_in_schema) for item in live] == [("GET", False)]


def test_websocket_is_not_an_http_reconciliation_failure():
    # 9, 15
    live, _missed = walk_live([APIWebSocketRoute()])
    assert [(item.method, item.path) for item in live] == [("WEBSOCKET", "/ws/monitor")]
    schema = _schema_with(("GET", "/health"))
    # The socket is live but not an HTTP operation, so it is not live-only.
    live_http = [item for item in live if item.method != "WEBSOCKET"]
    assert reconcile(live_http, schema) == ["openapi-only GET /health"]


def test_framework_and_hidden_routes_reconcile():
    # 12, 13, 14, 16
    live, _missed = walk_live([
        _Route("/docs"),
        _Route("/redoc"),
        _Route("/openapi.json"),
        _Route("/docs/oauth2-redirect"),
        _Route("/hidden/gcode", include=False),
        _Route("/visible"),
    ])
    schema = _schema_with(("GET", "/visible"))
    assert reconcile(live, schema) == []
    extra = dict(schema)
    extra["paths"] = {**schema["paths"], "/missing": {"post": {}}}
    assert reconcile(live, extra) == ["openapi-only POST /missing"]
    # rebuild via walk so include_in_schema is set
    stray_live, _missed = walk_live([_Route("/stray"), _Route("/visible")])
    assert "live-only GET /stray" in reconcile(stray_live, schema)


def test_hidden_duplicate_does_not_mask_a_visible_operation():
    live, unresolved = walk_live([
        _Route("/api/cam/thing", methods={"POST"}, include=False),
        _Route("/api/cam/thing", methods={"POST"}, include=True),
    ])
    assert unresolved == []
    assert reconcile(live, {"paths": {}}) == ["live-only POST /api/cam/thing"]


def test_all_duplicates_hidden_is_an_accepted_exception():
    live, unresolved = walk_live([
        _Route("/api/cam/thing", methods={"POST"}, include=False),
        _Route("/api/cam/thing", methods={"POST"}, include=False),
    ])
    assert unresolved == []
    assert reconcile(live, {"paths": {}}) == []


def test_openapi_operation_set_ignores_non_http_keys():
    found = openapi_operations({"paths": {"/x": {"post": {}, "parameters": {}}}})
    assert found == {("POST", "/x")}


@pytest.fixture(scope="module")
def inventory_app():
    from app.main import app
    return app


def test_live_population_reconciles_and_naive_walk_truncates(inventory_app):
    # 11, 55, 56
    live, unresolved = walk_live(inventory_app.routes)
    assert unresolved == []
    assert live
    assert inventory_app.openapi()["paths"]
    assert reconcile(live, inventory_app.openapi()) == []
    assert len(naive_walk(inventory_app.routes)) < len(live)
    resolved, missed = walk_routes(inventory_app.routes)
    assert missed == []
    assert len(resolved) == len(live)


def test_committed_inventory_matches_the_pinned_tree(inventory_app):
    # 17, 20, 54, 57, 58
    from app.ci.manufacturing_output_inventory import check_inventory, render_markdown

    document = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert document["base_sha"] == PINNED
    assert document["historical_audit"]["broad_candidates"] == 420
    assert document["current"]["candidates"] != 420
    assert "not a forced" in document["reconciliation"]
    assert check_inventory(document, inventory_app.routes) == []
    report = REPORT.read_text(encoding="utf-8")
    assert report.startswith("# Manufacturing output inventory\n")
    assert "UNEXAMINED` does not mean safe" in report
    assert "does not qualify a generator" in report
    live, _missed = walk_live(inventory_app.routes)
    rendered = render_markdown(document, len(live), len(inventory_app.openapi()["paths"]))
    assert rendered == report


def test_stale_duplicate_and_wrong_sha_fail_the_check(inventory_app):
    # 18, 19, 20
    from app.ci.manufacturing_output_inventory import check_inventory, validate_document

    document = json.loads(INVENTORY.read_text(encoding="utf-8"))
    stale = json.loads(json.dumps(document))
    stale["rows"] = stale["rows"][1:]
    problems = check_inventory(stale, inventory_app.routes)
    assert any(item.startswith("missing candidate") for item in problems)

    duplicated = json.loads(json.dumps(document))
    duplicated["rows"] = [duplicated["rows"][0], duplicated["rows"][0]]
    assert any(item.startswith("duplicate") for item in validate_document(duplicated))

    shifted = json.loads(json.dumps(document))
    shifted["base_sha"] = "0" * 40
    assert any("base_sha" in item for item in check_inventory(shifted, inventory_app.routes))


def test_production_modules_do_not_import_the_inventory():
    # 52, 53
    app_root = Path(__file__).resolve().parents[1] / "app"
    banned = "manufacturing_output_inventory"
    offenders = []
    for path in app_root.rglob("*.py"):
        if "/ci/" in str(path).replace("\\", "/"):
            continue
        if banned in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []
    engine = (app_root / "ci" / "manufacturing_output_classify.py").read_text(encoding="utf-8")
    assert "import app.cam.flying_v" not in engine
    assert "import socket" not in engine
    assert "from socket" not in engine
