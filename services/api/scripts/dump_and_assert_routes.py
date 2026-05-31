#!/usr/bin/env python3
"""
CI-RED-015-D: authoritative live wire-URL dump + MVP-path uniqueness assert.

WHY THIS EXISTS
    audit_wire_urls.py is a STATIC approximation (parses source before FastAPI
    composition) and is known to over-count: it drops manifest prefixes on some
    paths and cannot resolve `include_router(child, prefix=...)` composition.
    The ONLY authoritative wire-URL set is the live `app.routes` table after the
    app is imported and composed. This script dumps that table and asserts the
    MVP-cut path resolves to exactly one handler per (method, path).

WHAT IT DOES
    1. Imports app.main:app (pure introspection; no port bind, no server start).
    2. Writes the composed route table to metrics/live_routes.json.
    3. Counts (METHOD path) collisions across the whole surface (informational).
    4. Asserts each MVP-path URL appears exactly once. Exit 1 if any MVP-path
       URL is missing or duplicated; exit 0 otherwise.

RUN
    cd services/api && python scripts/dump_and_assert_routes.py

STATUS
    UNRUN as of 2026-05-30 (authored without a working shell this session).
    Treat the committed metrics/live_routes.json as authoritative ONLY after a
    real run. Until then this is a ready-to-run artifact, not evidence.

SUPERSEDES
    The static audit (audit_wire_urls.py) and the out-of-tree C:\\tmp dump as the
    source of truth for CI-RED-015-D. The static script remains useful for triage
    only; this is the gate.
"""
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent
METRICS_DIR = API_ROOT / "metrics"

# MVP-cut path URLs that MUST resolve to exactly one handler each.
# Exact paths: literal wire URLs.
MVP_EXACT = [
    "/api/rmos/wrap/mvp/dxf-to-grbl",
    "/api/v1/fretboard/dxf",
]
# Prefix groups: at least one route must exist under each; we report (but do not
# fail on) collisions inside these so a human can eyeball them.
MVP_PREFIXES = [
    "/api/rmos/runs",
    "/api/export/",
]

_IGNORED_METHODS = {"HEAD", "OPTIONS"}


def collect_routes():
    # Imported lazily so `--help`-style inspection of this file never triggers
    # the (heavy) app import.
    from app.main import app  # noqa: WPS433 (intentional local import)

    routes = []
    for r in app.routes:
        path = getattr(r, "path", None)
        if path is None:
            continue
        methods = sorted(
            m for m in (getattr(r, "methods", None) or []) if m not in _IGNORED_METHODS
        )
        routes.append(
            {
                "path": path,
                "methods": methods,
                "name": getattr(r, "name", None),
                "endpoint": getattr(getattr(r, "endpoint", None), "__module__", None),
            }
        )
    return routes


def main() -> int:
    routes = collect_routes()

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = METRICS_DIR / "live_routes.json"
    out_path.write_text(json.dumps(routes, indent=2), encoding="utf-8")

    # Whole-surface collision count (informational; this is the real number that
    # the static "68" should be reconciled against).
    keys = [f"{m} {rt['path']}" for rt in routes for m in rt["methods"]]
    collisions = {k: c for k, c in Counter(keys).items() if c > 1}

    # MVP-path assertions.
    mvp_problems = []
    for p in MVP_EXACT:
        n = sum(1 for rt in routes if rt["path"] == p)
        if n != 1:
            mvp_problems.append({"url": p, "count": n, "kind": "exact"})
    mvp_prefix_hits = {
        prefix: sum(1 for rt in routes if rt["path"].startswith(prefix))
        for prefix in MVP_PREFIXES
    }
    for prefix, n in mvp_prefix_hits.items():
        if n == 0:
            mvp_problems.append({"url": prefix, "count": 0, "kind": "prefix-missing"})

    report = {
        "total_routes": len(routes),
        "collision_count": len(collisions),
        "collisions": collisions,
        "mvp_prefix_hits": mvp_prefix_hits,
        "mvp_problems": mvp_problems,
        "live_routes_path": str(out_path),
    }
    print(json.dumps(report, indent=2))

    if mvp_problems:
        print(
            "\nFAIL: MVP-path URL(s) not uniquely resolved — see mvp_problems above.",
            file=sys.stderr,
        )
        return 1
    print("\nOK: all MVP-path URLs resolve to exactly one handler.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
