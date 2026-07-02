"""Focused unit tests for scripts/check_manifest_discipline.py (CI-RED-016-A).

These build a miniature app/ tree in tmp_path and monkeypatch the checker's
module-level path globals (APP_ROOT / MANIFEST_DIR / BASELINE_PATH). The real
app.main is never imported, so the tests stay fast and hermetic.

Negative fixtures (net-new unmanifested routers) are constructed under tmp_path
only — a real unmanifested router file is never added to the repo tree.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check_manifest_discipline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_manifest_discipline_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    # Fresh import per test so monkeypatched globals never leak between tests.
    return _load_module()


@pytest.fixture
def tree(tmp_path, mod, monkeypatch):
    app_root = tmp_path / "app"
    manifest_dir = app_root / "router_registry" / "manifests"
    manifest_dir.mkdir(parents=True)
    baseline = tmp_path / "manifest_discipline_baseline.txt"
    monkeypatch.setattr(mod, "APP_ROOT", app_root)
    monkeypatch.setattr(mod, "MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(mod, "BASELINE_PATH", baseline)
    return SimpleNamespace(app_root=app_root, manifest_dir=manifest_dir, baseline=baseline, mod=mod)


def _write_router(app_root: Path, relpath: str, verb: str = "get") -> Path:
    p = app_root / (relpath + ".py")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"@router.{verb}('/x')\ndef handler():\n    return None\n", encoding="utf-8")
    return p


def _write_plain(app_root: Path, relpath: str) -> Path:
    p = app_root / (relpath + ".py")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("def helper():\n    return 1\n", encoding="utf-8")
    return p


def _write_manifest(manifest_dir: Path, name: str, module: str) -> Path:
    p = manifest_dir / f"{name}_manifest.py"
    p.write_text(f'SPECS = [RouterSpec(module="{module}", prefix="/x")]\n', encoding="utf-8")
    return p


def _baseline_entries(baseline: Path) -> list[str]:
    return [
        line.strip()
        for line in baseline.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


# --- module_to_relpath -------------------------------------------------------

def test_module_to_relpath_strips_app_prefix(mod):
    assert mod.module_to_relpath("app.routers.foo") == "routers/foo"


def test_module_to_relpath_keeps_nested_modules_stable(mod):
    assert mod.module_to_relpath("app.a.b.c") == "a/b/c"


def test_module_to_relpath_without_app_prefix_unchanged(mod):
    assert mod.module_to_relpath("routers.foo") == "routers/foo"


# --- router detection --------------------------------------------------------

def test_router_decorator_detected_common_verbs(tree):
    _write_router(tree.app_root, "routers/foo_get", verb="get")
    _write_router(tree.app_root, "routers/foo_post", verb="post")
    found = tree.mod.find_router_files()
    assert "routers/foo_get" in found
    assert "routers/foo_post" in found


def test_files_without_router_decorators_ignored(tree):
    _write_router(tree.app_root, "routers/foo", verb="get")
    _write_plain(tree.app_root, "routers/plain_helper")
    unmanifested = tree.mod.compute_unmanifested()
    assert "routers/foo" in unmanifested
    assert "routers/plain_helper" not in unmanifested


# --- manifest / aggregator exclusion ----------------------------------------

def test_manifested_router_excluded(tree):
    _write_router(tree.app_root, "routers/foo", verb="get")
    _write_manifest(tree.manifest_dir, "cam", "app.routers.foo")
    assert tree.mod.compute_unmanifested() == set()


def test_aggregator_covered_module_excluded(tree):
    # app.cam.routers is a KNOWN_AGGREGATOR_PKG -> cam/routers/* is treated mounted.
    _write_router(tree.app_root, "cam/routers/sub_router", verb="post")
    assert tree.mod.compute_unmanifested() == set()


# --- CLI / ratchet behaviour -------------------------------------------------

def test_net_new_unmanifested_fails(tree, capsys):
    tree.mod.write_baseline(set())  # baseline exists but grandfathers nothing
    _write_router(tree.app_root, "routers/brand_new", verb="get")
    rc = tree.mod.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "FAIL: net-new unmanifested router file(s) detected" in err
    assert "routers/brand_new" in err


def test_healed_baseline_entry_reported_but_passes(tree, capsys):
    _write_router(tree.app_root, "routers/still_here", verb="get")
    tree.mod.write_baseline({"routers/still_here", "routers/now_healed"})
    rc = tree.mod.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "left the unmanifested set" in out
    assert "routers/now_healed" in out


def test_update_baseline_writes_sorted_entries_with_header(tree):
    _write_router(tree.app_root, "routers/zeta", verb="get")
    _write_router(tree.app_root, "routers/alpha", verb="post")
    rc = tree.mod.main(["--update-baseline"])
    assert rc == 0
    assert _baseline_entries(tree.baseline) == ["routers/alpha", "routers/zeta"]
    assert tree.baseline.read_text(encoding="utf-8").startswith("# Manifest-discipline baseline")


def test_clean_no_new_state_passes(tree, capsys):
    _write_router(tree.app_root, "routers/foo", verb="get")
    tree.mod.write_baseline({"routers/foo"})
    rc = tree.mod.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK: no net-new unmanifested router files" in out


def test_missing_baseline_bootstraps(tree, capsys):
    assert not tree.baseline.exists()
    _write_router(tree.app_root, "routers/foo", verb="get")
    rc = tree.mod.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Bootstrapped baseline" in out
    assert tree.baseline.exists()
    assert _baseline_entries(tree.baseline) == ["routers/foo"]


# --- broadened decorator detection (websocket / api_route) -------------------

def test_router_decorator_detects_websocket_and_api_route(tree):
    # A websocket-only or api_route-only router file must still be counted — the
    # narrow (get|post|put|patch|delete) regex would have missed these.
    _write_router(tree.app_root, "routers/ws_only", verb="websocket")
    _write_router(tree.app_root, "routers/generic", verb="api_route")
    found = tree.mod.find_router_files()
    assert "routers/ws_only" in found
    assert "routers/generic" in found


# --- AST detection: strings/comments, programmatic forms, receiver scope ------

def test_declares_route_ignores_comments_and_strings(mod):
    # AST parse must NOT count route decorators that appear only inside a
    # docstring/string or a comment (the old regex false-positived on these —
    # 6 such phantom entries were in the committed baseline before CI-RED-016-A).
    text = '''"""Usage example:

    @router.get("/patterns")
    def list_patterns():
        ...
"""
# router.add_api_route("/commented", handler)
ROUTE_SNIPPET = "@router.post('/from-a-string')"

def helper():
    return 1
'''
    assert mod.declares_route(text) is False


def test_declares_route_detects_programmatic_add_api_route(mod):
    text = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "def handler():\n    return {'ok': True}\n"
        "router.add_api_route('/x', handler, methods=['GET'])\n"
    )
    assert mod.declares_route(text) is True


def test_declares_route_detects_programmatic_websocket_route(mod):
    text = (
        "router = APIRouter()\n"
        "async def ws(websocket):\n    await websocket.accept()\n"
        "router.add_api_websocket_route('/ws', ws)\n"
    )
    assert mod.declares_route(text) is True


def test_declares_route_detects_non_router_receiver_name(mod):
    # Real routers are often named descriptively (analytics_router, contour_router).
    # The old `@router.` regex was blind to these — a genuine bleed hole.
    text = "@analytics_router.get('/summary')\ndef summary():\n    return []\n"
    assert mod.declares_route(text) is True


def test_declares_route_excludes_root_app_endpoints(mod):
    # Endpoints declared directly on the composition-root app (app/main.py) are
    # mounted by construction and must NOT be flagged as unmanifested routers.
    decorator = "@app.get('/health')\ndef health():\n    return {'ok': True}\n"
    programmatic = "def h():\n    return 1\napp.add_api_route('/x', h, methods=['GET'])\n"
    assert mod.declares_route(decorator) is False
    assert mod.declares_route(programmatic) is False


def test_declares_route_regex_fallback_on_syntax_error(mod):
    # Unparseable files fall back to regex, which still applies the router-scope
    # rule: a non-app receiver matches, the root app does not.
    broken_router = "def (:\n    pass\n@feature_router.post('/x')\ndef h():\n    pass\n"
    broken_app = "def (:\n    pass\n@app.post('/x')\ndef h():\n    pass\n"
    assert mod.declares_route(broken_router) is True
    assert mod.declares_route(broken_app) is False


def test_root_app_receiver_file_not_counted_in_tree(tree):
    # End-to-end through find_router_files: a main-like file with only @app routes
    # is not a manifested-router candidate.
    p = tree.app_root / "main.py"
    p.write_text("@app.get('/health')\ndef health():\n    return {}\n", encoding="utf-8")
    assert "main" not in tree.mod.find_router_files()


# --- --require-baseline hard-fail (no silent CI re-bootstrap) -----------------

def test_require_baseline_fails_hard_when_missing(tree, capsys):
    assert not tree.baseline.exists()
    _write_router(tree.app_root, "routers/foo", verb="get")
    rc = tree.mod.main(["--require-baseline"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "baseline file missing" in err
    assert not tree.baseline.exists()  # must NOT silently re-bootstrap in CI


def test_require_baseline_ratchets_normally_when_present(tree, capsys):
    _write_router(tree.app_root, "routers/foo", verb="get")
    tree.mod.write_baseline({"routers/foo"})
    rc = tree.mod.main(["--require-baseline"])
    assert rc == 0
    assert "OK: no net-new unmanifested router files" in capsys.readouterr().out


def test_require_baseline_reports_resolved_missing_path(tree, capsys):
    # A missing baseline in CI must fail with the RESOLVED path so path/cwd
    # mistakes are triageable, not a bare filename.
    assert not tree.baseline.exists()
    rc = tree.mod.main(["--require-baseline"])
    err = capsys.readouterr().err
    assert rc == 2
    assert str(tree.baseline) in err


# --- --fail-on-healed (stale baseline is a hard, witnessed failure) -----------

def test_fail_on_healed_returns_error_and_asks_for_update(tree, capsys):
    # One baseline entry no longer exists in the tree -> stale. Without the flag
    # this only NOTEs; with it, CI must fail so the tightening is witnessed.
    _write_router(tree.app_root, "routers/still_here", verb="get")
    tree.mod.write_baseline({"routers/still_here", "routers/now_healed"})
    rc = tree.mod.main(["--require-baseline", "--fail-on-healed"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "baseline is stale" in captured.err
    assert "--update-baseline" in captured.err


def test_fail_on_healed_passes_when_baseline_current(tree, capsys):
    _write_router(tree.app_root, "routers/foo", verb="get")
    tree.mod.write_baseline({"routers/foo"})
    rc = tree.mod.main(["--require-baseline", "--fail-on-healed"])
    assert rc == 0
    assert "bleed-stop ratchet" in capsys.readouterr().out


# --- aggregator allowlist stays narrow ---------------------------------------

def test_known_aggregator_prefixes_remain_narrow(mod):
    # The prefix allowlist is a trust boundary, not a proof of composition. Beyond
    # pinning the exact tuple elsewhere, assert it stays app-scoped and never
    # widens to a whole package root (which would blanket-exempt too much).
    assert mod.KNOWN_AGGREGATOR_PKGS
    for prefix in mod.KNOWN_AGGREGATOR_PKGS:
        assert prefix.startswith("app.")
        assert prefix not in {"app", "app.routers", "app.cam"}


# --- representative checks against the REAL repo tree (not tmp_path) ----------
# These use the fresh module with its real path globals, so they exercise the
# actual app/ tree + committed baseline — catching drift the miniature tests can't.

def test_real_repo_checker_matches_committed_baseline(mod):
    # The checker's live output must equal the committed baseline: if a real
    # unmanifested router lands (or one heals) without a baseline update, this
    # fails alongside the CI step — a representative integration guard.
    assert mod.compute_unmanifested() == mod.load_baseline()


def test_geometry_authority_router_is_covered_in_real_tree(mod):
    # The baseline was tightened 108->107 by removing this entry; assert it is
    # genuinely covered (manifested by CI-RED-015-H), not prematurely dropped.
    assert "routers/cam/geometry_authority_router" not in mod.compute_unmanifested()


def test_known_aggregator_pkgs_are_pinned(mod):
    # The prefix allowlist is an explicit trust boundary (not a proof of runtime
    # composition); pin it so it cannot silently grow without a reviewed test change.
    assert mod.KNOWN_AGGREGATOR_PKGS == (
        "app.cam.routers",
        "app.routers.instrument_geometry",
    )
