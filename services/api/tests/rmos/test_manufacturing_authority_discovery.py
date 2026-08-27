"""RMOS-AUTHORITY-MAP-001 Stage 1 — discovery completeness (MAR-006–008, 021–024).

Uses a synthetic FastAPI app for negative tests so they do not depend on
production route churn. One live test reconciles the committed registry
against ``app.main:app``.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from fastapi import APIRouter, FastAPI

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts/audit/rmos_authority_map.py"
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "services/api/app/rmos/schemas/manufacturing_authority_registry.schema.json"
)


def _load_script():
    spec = importlib.util.spec_from_file_location("rmos_authority_map", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_script()


def _mini_app() -> FastAPI:
    app = FastAPI()
    retract = APIRouter()

    @retract.post("/gcode")
    def retract_gcode():
        return "ok"

    @retract.post("/gcode_governed")
    def retract_gcode_governed():
        return "ok"

    @retract.post("/gcode/download")
    def retract_download():
        return "ok"

    @retract.post("/gcode/download_governed")
    def retract_download_governed():
        return "ok"

    app.include_router(retract, prefix="/api/cam/retract")

    @app.post("/api/cam/profiling/gcode")
    def profiling_gcode():
        return "ok"

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


def test_mar_008_aliases_group_under_one_capability(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    grouped = mod.group_capabilities(classified["candidates"])
    assert "retract" in grouped
    paths = {item["path"] for item in grouped["retract"]}
    assert paths == {
        "/api/cam/retract/gcode",
        "/api/cam/retract/gcode_governed",
        "/api/cam/retract/gcode/download",
        "/api/cam/retract/gcode/download_governed",
    }
    # Four retract aliases must not mint four capabilities.
    assert sum(1 for cid in grouped if cid.startswith("retract")) == 1
    assert "profiling" in grouped
    assert len(grouped["profiling"]) == 1


def test_mar_006_and_021_unregistered_emitter_fails_validation(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    skeleton = mod.build_skeleton(inventory, classified)
    # Drop profiling so a mounted G-code emitter is silently omitted.
    skeleton["capabilities"] = [
        c for c in skeleton["capabilities"] if c["capability_id"] != "profiling"
    ]
    errors = mod.validate_registry(
        skeleton, inventory=inventory, classified=classified
    )
    joined = "\n".join(errors)
    assert "MAR-006/MAR-021" in joined
    assert "/api/cam/profiling/gcode" in joined


def test_mar_007_unknown_newly_mounted_gcode_emitter_fails(mod):
    app = _mini_app()

    @app.post("/api/cam/brand_new/gcode")
    def brand_new():
        return "G21"

    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    # Registry seeded from the mini app *before* the extra emitter existed.
    base_app = _mini_app()
    base_inv = mod.collect_inventory(base_app)
    base_cls = mod.classify_routes(base_inv["routes"])
    registry = mod.build_skeleton(base_inv, base_cls)
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    joined = "\n".join(errors)
    assert "MAR-006/MAR-021" in joined
    assert "/api/cam/brand_new/gcode" in joined


def test_mar_004_registered_unmounted_route_fails_unless_historical(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    registry = mod.build_skeleton(inventory, classified)
    ghost = {
        "path": "/api/cam/retract/gcode/ancient",
        "methods": ["POST"],
        "mount_state": "MOUNTED",
        "route_role": "alias",
        "historical_or_dead": False,
    }
    retract = next(c for c in registry["capabilities"] if c["capability_id"] == "retract")
    retract["routes"].append(ghost)
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    assert any("MAR-004" in e and "ancient" in e for e in errors)

    ghost["mount_state"] = "HISTORICAL"
    ghost["historical_or_dead"] = True
    errors_ok = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    assert not any("ancient" in e for e in errors_ok)


def test_mar_022_empty_consumers_do_not_classify_dead(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    registry = mod.build_skeleton(inventory, classified)
    retract = next(c for c in registry["capabilities"] if c["capability_id"] == "retract")
    assert retract["client_consumers"] == []
    # Stage-1 empty consumers + MOUNTED is valid.
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    assert not any("MAR-022" in e for e in errors)
    # Collapsing empty consumers into RUNTIME_BROKEN is not allowed.
    retract["reachability"] = "RUNTIME_BROKEN"
    retract["runtime_evidence"] = "NOT_OBTAINED_STAGE_1"
    errors_bad = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    assert any("MAR-022" in e for e in errors_bad)


def test_mar_023_source_presence_cannot_establish_runtime_reachable(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    registry = mod.build_skeleton(inventory, classified)
    retract = next(c for c in registry["capabilities"] if c["capability_id"] == "retract")
    retract["reachability"] = "RUNTIME_REACHABLE"
    retract["runtime_evidence"] = "NOT_OBTAINED_STAGE_1"
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    assert any("MAR-023" in e for e in errors)


def test_mar_024_validate_does_not_mutate_registry(mod, tmp_path):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    registry = mod.build_skeleton(inventory, classified)
    target = tmp_path / "manufacturing_authority_registry.json"
    payload = json.dumps(registry, indent=2, sort_keys=True)
    target.write_text(payload, encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified
    )
    after = target.read_text(encoding="utf-8")
    assert errors == []
    assert after == before
    # The helper has no write path; committed registry must also be untouched.
    committed_before = REGISTRY_PATH.read_bytes()
    _ = mod.validate_registry(json.loads(committed_before))
    assert REGISTRY_PATH.read_bytes() == committed_before


def test_health_is_not_a_machine_output_candidate(mod):
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    paths = {c["path"] for c in classified["candidates"]}
    assert "/health" not in paths


def test_acoustic_binding_groups_under_binding(mod):
    from fastapi import FastAPI

    app = FastAPI()

    @app.post("/api/cam/guitar/acoustic/{style}/binding/gcode")
    def acoustic_binding():
        return "ok"

    @app.post("/api/cam/guitar/acoustic/{style}/body/gcode")
    def acoustic_body():
        return "ok"

    @app.post("/api/cam/binding/channel/gcode")
    def cam_binding():
        return "ok"

    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    grouped = mod.group_capabilities(classified["candidates"])
    bind_paths = {i["path"] for i in grouped.get("binding", [])}
    assert "/api/cam/binding/channel/gcode" in bind_paths
    assert any("/binding/" in p and "/acoustic/" in p for p in bind_paths)
    guitar_paths = {i["path"] for i in grouped.get("cam-guitar", [])}
    assert not any("/binding/" in p for p in guitar_paths)
    assert any("/body/" in p for p in guitar_paths)


def test_naive_top_level_walk_undercounts_included_routers(mod):
    """Witness that Stage 1 must recurse ``_IncludedRouter``, not ``app.routes``."""
    app = _mini_app()
    from fastapi.routing import APIRoute

    naive = [r for r in app.routes if isinstance(r, APIRoute)]
    walked = list(mod.iter_mounted_routes(app))
    assert len(walked) > len(naive)


def test_live_app_registry_reconciles(mod):
    """MAR-004/006 against the real mounted table (requires API import)."""
    pytest.importorskip("sqlalchemy")
    from app.main import app

    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = mod.validate_registry(
        registry, inventory=inventory, classified=classified, schema=schema
    )
    assert errors == [], errors
    assert inventory["unique_mounted_paths"] > 100
    assert len(classified["candidates"]) >= 14


def _app_without_retract() -> FastAPI:
    """The mini app with the retract family absent, as a failed mount leaves it."""
    app = FastAPI()

    @app.post("/api/cam/profiling/gcode")
    def profiling_gcode():
        return "ok"

    return app


def test_mar_027_unmounted_family_reports_once_not_per_route(mod):
    """A router family that did not mount is one cause, not N stale routes.

    The CAM aggregator mounts each family behind ``try: import / except
    ImportError: router = None``. A missing dependency therefore removes a whole
    manufacturing family silently, and the routes resurface here looking like
    unrelated stale registry entries. MAR-027 names the mechanism once.
    """
    full = _mini_app()
    inventory = mod.collect_inventory(full)
    classified = mod.classify_routes(inventory["routes"])
    skeleton = mod.build_skeleton(inventory, classified)

    reduced = mod.collect_inventory(_app_without_retract())
    reduced_classified = mod.classify_routes(reduced["routes"])
    errors = mod.validate_registry(
        skeleton, inventory=reduced, classified=reduced_classified
    )

    family = [e for e in errors if e.startswith("MAR-027")]
    assert len(family) == 1, errors
    assert "/api/cam/retract" in family[0]
    assert "import guard" in family[0]
    # The four routes must not also be reported individually.
    assert not [e for e in errors if e.startswith("MAR-004")], errors


def test_mar_004_still_fires_for_a_single_stale_route(mod):
    """One dead route inside a family that IS mounted stays a MAR-004."""
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    skeleton = mod.build_skeleton(inventory, classified)
    retract = next(
        c for c in skeleton["capabilities"] if c["capability_id"] == "retract"
    )
    retract["routes"].append(
        {
            "path": "/api/cam/retract/gcode_ancient",
            "methods": ["POST"],
            "mount_state": "MOUNTED",
            "route_role": "alias",
            "historical_or_dead": False,
        }
    )
    errors = mod.validate_registry(
        skeleton, inventory=inventory, classified=classified
    )
    assert any("MAR-004" in e and "gcode_ancient" in e for e in errors), errors
    assert not [e for e in errors if e.startswith("MAR-027")], errors


def test_mar_026_blind_walk_cannot_report_agreement(mod):
    """An OpenAPI cross-check that did not run must not read as 'no discrepancy'."""
    app = _mini_app()
    inventory = mod.collect_inventory(app)
    classified = mod.classify_routes(inventory["routes"])
    skeleton = mod.build_skeleton(inventory, classified)

    assert inventory["openapi_available"] is True
    assert inventory["in_openapi_not_walked"] == []

    blinded = dict(inventory)
    blinded["openapi_available"] = False
    blinded["openapi_error"] = "TypeAdapter is not fully defined"
    blinded["in_openapi_not_walked"] = None
    blinded["in_walked_not_openapi"] = None

    errors = mod.validate_registry(
        skeleton, inventory=blinded, classified=classified
    )
    assert any(e.startswith("MAR-026") for e in errors), errors
    assert any("not fully defined" in e for e in errors), errors
