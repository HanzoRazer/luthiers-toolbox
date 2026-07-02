#!/usr/bin/env python3
"""
Manifest-discipline bleed-stop (CI-RED-015-D follow-on, item 6).

PROBLEM
    ~49% of router files (the "143 unmanifested") define @router endpoints but
    are never registered via a RouterSpec in app/router_registry/manifests/.
    Re-architecting those is a deferred sprint (CI-RED-016 / retirement). This
    check does NOT try to fix them — it RATCHETS: it fails CI when a NET-NEW
    router file appears unmanifested, so the percentage stops climbing while the
    repo winds down. Same shape as wiring check_execution_class_compliance.py
    after a deletion: freeze the known set, block regressions.

HOW
    1. Find every app/**/*.py containing `@router.<verb>(`.
    2. Resolve the set of manifested module files (RouterSpec(module=...)).
    3. Treat files reachable via a known aggregator as mounted (best-effort;
       see KNOWN_AGGREGATOR_PKGS — composition is not statically resolved, so
       this is an allow-prefix, not a proof).
    4. unmanifested = router files - manifested - aggregator-covered.
    5. Compare against a committed baseline (scripts/manifest_discipline_baseline.txt).
       FAIL only on files NOT in the baseline (net-new bleed).

BASELINE BOOTSTRAP
    First run (no baseline file) writes the current unmanifested set to the
    baseline and PASSES with a notice. Commit that baseline. To intentionally
    accept new unmanifested files later, re-run with --update-baseline.

STATUS
    Materialized and baseline-backed. CI-RED-016-A (2026-07-01) wires this into
    Core CI (api-tests job, before API boot / full pytest) as a bleed-stop.
    The known unmanifested set is grandfathered by
    scripts/manifest_discipline_baseline.txt; only NET-NEW unmanifested router
    files fail. This does NOT close CI-RED-016 endpoint consolidation.

RUN
    cd services/api && python scripts/check_manifest_discipline.py
    cd services/api && python scripts/check_manifest_discipline.py --update-baseline
    # CI: fail hard instead of re-bootstrapping if the baseline is missing
    cd services/api && python scripts/check_manifest_discipline.py --require-baseline

DETECTION
    @router.<verb>( where verb is any FastAPI route method incl. websocket/api_route.
    Programmatic registration (add_api_route / app.websocket) is NOT detected — a
    known limitation; such routers must still be routed via router_registry.
"""
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent
APP_ROOT = API_ROOT / "app"
MANIFEST_DIR = APP_ROOT / "router_registry" / "manifests"
BASELINE_PATH = SCRIPT_DIR / "manifest_discipline_baseline.txt"

_ROUTER_DECORATOR = re.compile(
    r"@router\.(get|post|put|patch|delete|head|options|trace|websocket|api_route)\(",
    re.IGNORECASE,
)
_MODULE_RE = re.compile(r"module\s*=\s*[\"']([^\"']+)[\"']")

# Packages whose sub-routers are composed via include_router(...) into a mounted
# aggregator. Files under these are treated as reachable (best-effort allowlist,
# NOT a static proof of composition). Keep this list tight and reviewed.
KNOWN_AGGREGATOR_PKGS = (
    "app.cam.routers",       # cam/routers/aggregator.py composes the CAM tree
    "app.routers.instrument_geometry",  # __init__ include_router(soundhole/nut_fret)
)


def module_to_relpath(module: str) -> str:
    """app.foo.bar -> foo/bar (relative to app/, no extension)."""
    parts = module.split(".")
    if parts and parts[0] == "app":
        parts = parts[1:]
    return "/".join(parts)


def find_router_files() -> set[str]:
    """Relative-to-app posix paths (no extension) of files with @router decorators."""
    found = set()
    for py in APP_ROOT.rglob("*.py"):
        # Every .py (incl. __init__.py, which can compose routers) is scanned and
        # counted only if it actually carries an @router endpoint decorator.
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        if _ROUTER_DECORATOR.search(text):
            rel = py.relative_to(APP_ROOT).with_suffix("")
            found.add(rel.as_posix())
    return found


def find_manifested_relpaths() -> set[str]:
    manifested = set()
    if not MANIFEST_DIR.exists():
        return manifested
    for mf in MANIFEST_DIR.glob("*_manifest.py"):
        try:
            content = mf.read_text(encoding="utf-8")
        except Exception:
            continue
        for block in content.split("RouterSpec(")[1:]:
            m = _MODULE_RE.search(block)
            if m:
                manifested.add(module_to_relpath(m.group(1)))
    return manifested


def aggregator_covered(relpath: str) -> bool:
    for pkg in KNOWN_AGGREGATOR_PKGS:
        if relpath.startswith(module_to_relpath(pkg) + "/") or relpath == module_to_relpath(pkg):
            return True
    return False


def compute_unmanifested() -> set[str]:
    router_files = find_router_files()
    manifested = find_manifested_relpaths()
    return {
        rel
        for rel in router_files
        if rel not in manifested and not aggregator_covered(rel)
    }


def load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        return set()
    return {
        line.strip()
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def write_baseline(items: set[str]) -> None:
    header = (
        "# Manifest-discipline baseline (CI-RED-015-D bleed-stop).\n"
        "# Router files that define @router endpoints but are NOT manifested.\n"
        "# This freezes the KNOWN unmanifested set; CI fails on net-new additions.\n"
        "# Regenerate intentionally with: python scripts/check_manifest_discipline.py --update-baseline\n"
    )
    body = "\n".join(sorted(items))
    BASELINE_PATH.write_text(header + body + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    update = "--update-baseline" in argv
    require_baseline = "--require-baseline" in argv
    current = compute_unmanifested()

    if update:
        write_baseline(current)
        print(f"Updated baseline with {len(current)} unmanifested router file(s): {BASELINE_PATH}")
        return 0

    if not BASELINE_PATH.exists():
        # Bootstrap is convenient locally but dangerous in CI: a missing baseline
        # (bad checkout, path mistake, refactor) would silently re-bootstrap and
        # PASS, masking the ratchet entirely. --require-baseline makes that a hard
        # failure so CI never green-lights a check that isn't really running.
        if require_baseline:
            print(
                f"FAIL: baseline file missing at {BASELINE_PATH} and --require-baseline "
                "is set (CI must not silently re-bootstrap). Restore the committed "
                "baseline, or regenerate intentionally with --update-baseline.",
                file=sys.stderr,
            )
            return 2
        write_baseline(current)
        print(f"Bootstrapped baseline with {len(current)} unmanifested router file(s): {BASELINE_PATH}")
        print("First-run bootstrap — commit this baseline; future runs ratchet against it.")
        return 0

    baseline = load_baseline()
    new_bleed = sorted(current - baseline)
    healed = sorted(baseline - current)  # files that became manifested/removed

    if healed:
        print(f"NOTE: {len(healed)} file(s) left the unmanifested set (manifested or removed):")
        for rel in healed:
            print(f"  - {rel}")
        print("Consider --update-baseline to tighten the ratchet.\n")

    if new_bleed:
        print("FAIL: net-new unmanifested router file(s) detected:", file=sys.stderr)
        for rel in new_bleed:
            print(f"  + {rel}", file=sys.stderr)
        print(
            "\nAdd a RouterSpec in router_registry/manifests/, route it through a "
            "known aggregator, or (if intentional) run --update-baseline with review.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: no net-new unmanifested router files (baseline holds {len(baseline)}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
