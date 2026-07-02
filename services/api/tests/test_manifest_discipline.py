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
