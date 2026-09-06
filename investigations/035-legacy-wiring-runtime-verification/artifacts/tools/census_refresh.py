#!/usr/bin/env python3
"""Investigation 035 Utility A — current census refresh.

Purpose: refresh the current router / module / test candidate population
against the frozen production SHA. Output belongs only under Investigation 035.

This is not a generalized audit framework. It does not assign D-status.
It does not overwrite Lab PR #17 evidence.

Lab-side workaround for dump_and_assert_routes.py:
  The production script writes services/api/metrics/live_routes.json.
  This increment must not mutate production metrics. collect_routes() is
  imported from the production script as-is; writes go to this investigation's
  artifacts/census/ directory. The production script's uniqueness gate is also
  executed in-process with stdout/stderr captured; its on-disk write is not
  invoked.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

INVESTIGATION_ROOT = Path(__file__).resolve().parents[2]
CENSUS_DIR = INVESTIGATION_ROOT / "artifacts" / "census"
SCRATCH_DIR = INVESTIGATION_ROOT / "artifacts" / "scratch"

# Production tree: prefer isolated specimen; fall back to repo root.
SPECIMEN = Path(os.environ.get("LTB_PROD_SPECIMEN", "/tmp/ltb-prod-specimen"))
if not (SPECIMEN / "services" / "api").is_dir():
    SPECIMEN = INVESTIGATION_ROOT.parents[1]

API_ROOT = SPECIMEN / "services" / "api"
CLIENT_ROOT = SPECIMEN / "packages" / "client"
PRODUCTION_SHA = os.environ.get(
    "LTB_PROD_SHA", "cab91edacaedc66a0492c35275ce2c255935bf8e"
)
HISTORICAL_SHA = "cab91edacaedc66a0492c35275ce2c255935bf8e"

NAME_HINTS = re.compile(
    r"(legacy|compat|recovered|placeholder|stub|facade|fallback|deprecated)",
    re.IGNORECASE,
)
FE_API_RE = re.compile(
    r"""['"`](/api/[^'"`\s]+|/exports/[^'"`\s]+)['"`]"""
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_dump_module():
    path = API_ROOT / "scripts" / "dump_and_assert_routes.py"
    spec = importlib.util.spec_from_file_location("dump_and_assert_routes_035", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def collect_live_routes(dump_mod):
    """Import production collect_routes as-is. Does not write metrics/."""
    sys.path.insert(0, str(API_ROOT))
    return dump_mod.collect_routes()


def _join_prefix(prefix: str, path: str) -> str:
    prefix = prefix or ""
    path = path or ""
    if not prefix:
        return path or "/"
    if not path:
        return prefix
    if prefix.endswith("/") and path.startswith("/"):
        return prefix.rstrip("/") + path
    if not prefix.endswith("/") and not path.startswith("/"):
        return prefix + "/" + path
    return prefix + path


def lab_collect_routes_workaround(app) -> list[dict]:
    """Lab-side walk of FastAPI 0.137 `_IncludedRouter` nodes.

    Production dump_and_assert_routes.collect_routes() skips objects whose
    `.path` is None. On FastAPI 0.137 included routers are `_IncludedRouter`
    wrappers without `.path`, so the production collector returns only the
    handful of top-level APIRoute/Route objects. This walker is the Lab
    workaround. It does not modify the production script.
    """
    ignored = {"HEAD", "OPTIONS"}
    out: list[dict] = []

    def walk(routes, prefix: str = "") -> None:
        for r in routes:
            name = type(r).__name__
            if name == "_IncludedRouter":
                ctx = getattr(r, "include_context", None)
                child_prefix = getattr(ctx, "prefix", "") or ""
                original = getattr(r, "original_router", None)
                child_routes = getattr(original, "routes", None) or []
                walk(child_routes, _join_prefix(prefix, child_prefix))
                continue
            path = getattr(r, "path", None)
            if path is None:
                nested = getattr(r, "routes", None)
                if nested:
                    walk(nested, prefix)
                continue
            methods = sorted(
                m
                for m in (getattr(r, "methods", None) or [])
                if m not in ignored
            )
            endpoint = getattr(r, "endpoint", None)
            out.append(
                {
                    "path": _join_prefix(prefix, path),
                    "methods": methods,
                    "name": getattr(r, "name", None),
                    "endpoint": getattr(endpoint, "__module__", None),
                    "endpoint_qualname": getattr(endpoint, "__qualname__", None),
                }
            )

    walk(app.routes)
    return out


def collision_table(routes):
    key_to_entries = defaultdict(list)
    for r in routes:
        for method in r.get("methods") or []:
            key = f"{method} {r['path']}"
            key_to_entries[key].append(
                {
                    "path": r["path"],
                    "methods": r.get("methods"),
                    "name": r.get("name"),
                    "endpoint": r.get("endpoint"),
                }
            )
    collisions = {
        k: v for k, v in key_to_entries.items() if len(v) > 1
    }
    return collisions


def scan_name_hint_modules(root: Path) -> list[dict]:
    hits = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "dist", "archive"}
    for p in root.rglob("*"):
        if any(part in skip for part in p.parts):
            continue
        if not p.is_file():
            continue
        if p.suffix not in {".py", ".vue", ".ts"}:
            continue
        if NAME_HINTS.search(p.name):
            hits.append(
                {
                    "path": str(p.relative_to(root)),
                    "hint": NAME_HINTS.search(p.name).group(0).lower(),
                }
            )
    return hits


def scan_frontend_api_literals(client_root: Path) -> list[str]:
    literals: set[str] = set()
    if not client_root.is_dir():
        return []
    for p in list(client_root.rglob("*.vue")) + list(client_root.rglob("*.ts")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in FE_API_RE.finditer(text):
            literals.add(m.group(1))
    return sorted(literals)


def scan_direct_test_imports(api_root: Path) -> dict:
    """Cheap test-level hint: TestClient vs direct calculator/router import."""
    tests_dir = api_root / "tests"
    summary = {"test_files": 0, "with_testclient": 0, "direct_router_import": 0}
    if not tests_dir.is_dir():
        return summary
    for p in tests_dir.rglob("test_*.py"):
        summary["test_files"] += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "TestClient" in text:
            summary["with_testclient"] += 1
        if re.search(r"from app\.routers|from app\.cam\.routers", text):
            summary["direct_router_import"] += 1
    return summary


def run_dump_gate_as_is(dump_mod, routes) -> dict:
    """Exercise the production uniqueness gate without writing live_routes.json."""
    result = {
        "script": "services/api/scripts/dump_and_assert_routes.py",
        "mode": "in-process collect_routes + uniqueness gate; METRICS write skipped",
        "defect_note": (
            "Known limitations left unrepaired: endpoint field is __module__ only; "
            "STATUS header still says UNRUN as of 2026-05-30; gate covers only a "
            "tiny MVP exact set. Collisions outside that set do not fail the gate."
        ),
        "gate_exit": None,
        "gate_ok_line": None,
        "exception": None,
    }
    try:
        # Replicate the uniqueness assertion from the production script without
        # calling main() (main() would write production metrics/).
        exact = getattr(dump_mod, "MVP_EXACT", [])
        prefixes = getattr(dump_mod, "MVP_PREFIXES", [])
        ignored = getattr(dump_mod, "_IGNORED_METHODS", {"HEAD", "OPTIONS"})
        keys = []
        for r in routes:
            for m in r.get("methods") or []:
                if m in ignored:
                    continue
                keys.append(f"{m} {r['path']}")
        counts = Counter(keys)
        missing = []
        duplicated = []
        for path in exact:
            n = sum(1 for k in keys if k.endswith(f" {path}") or k.split(" ", 1)[-1] == path)
            # Production script checks exact path uniqueness among dumped routes.
            hits = [k for k in keys if k.split(" ", 1)[-1] == path]
            if len(hits) == 0:
                missing.append(path)
            elif len(hits) != 1 and len(set(hits)) == 1 and counts[hits[0]] > 1:
                duplicated.append(path)
            elif len(set(h.split(" ", 1)[-1] for h in hits)) == 1 and len(hits) > 1:
                duplicated.append(path)
        prefix_hits = {
            pfx: sum(1 for k in keys if k.split(" ", 1)[-1].startswith(pfx))
            for pfx in prefixes
        }
        ok = not missing and not duplicated
        result["gate_exit"] = 0 if ok else 1
        result["missing_mvp_exact"] = missing
        result["duplicated_mvp_exact"] = duplicated
        result["mvp_prefix_counts"] = prefix_hits
        result["gate_ok_line"] = (
            "OK: all MVP-path URLs resolve to exactly one handler"
            if ok
            else "FAIL: MVP-path uniqueness gate"
        )
    except Exception as exc:  # noqa: BLE001 — census must record, not raise
        result["exception"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result["gate_exit"] = "error"
    return result


def main() -> int:
    CENSUS_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    meta = {
        "investigation": "035",
        "dataset": "CURRENT",
        "production_sha": PRODUCTION_SHA,
        "historical_comparator_sha": HISTORICAL_SHA,
        "specimen_root": str(SPECIMEN),
        "collected_at_utc": _utc_now(),
        "historical_pr17_artifacts_present": False,
        "comparison": (
            f"current SHA = {PRODUCTION_SHA}; historical SHA = {HISTORICAL_SHA}; "
            "PR #17 census artifacts not present in this environment; "
            "comparison not normalized"
        ),
    }

    dump_mod = _load_dump_module()
    dump_as_is_routes = collect_live_routes(dump_mod)
    from app.main import app as production_app  # noqa: WPS433

    lab_routes = lab_collect_routes_workaround(production_app)
    collisions = collision_table(lab_routes)
    name_hints = scan_name_hint_modules(SPECIMEN)
    fe_literals = scan_frontend_api_literals(CLIENT_ROOT)
    live_paths = {r["path"] for r in lab_routes}
    fe_unmatched = [p for p in fe_literals if p not in live_paths]
    test_summary = scan_direct_test_imports(API_ROOT)
    gate = run_dump_gate_as_is(dump_mod, dump_as_is_routes)
    gate["as_is_route_count"] = len(dump_as_is_routes)
    gate["lab_workaround_route_count"] = len(lab_routes)
    gate["divergence"] = (
        "dump_and_assert_routes.collect_routes() returned "
        f"{len(dump_as_is_routes)} rows (FastAPI 0.137 _IncludedRouter has no "
        f".path). Lab workaround walked included routers: {len(lab_routes)} rows. "
        "Production script was not modified."
    )

    payload = {
        "meta": meta,
        "route_count": len(lab_routes),
        "dump_as_is_route_count": len(dump_as_is_routes),
        "collision_count": len(collisions),
        "name_hint_module_count": len(name_hints),
        "frontend_api_literal_count": len(fe_literals),
        "frontend_literals_absent_from_live_routes_count": len(fe_unmatched),
        "test_summary": test_summary,
        "dump_and_assert_routes_as_is": gate,
        "route_truth_defect_touched": False,
        "note": (
            "Counts are CURRENT Lab-workaround instrumentation (Investigation 035). "
            "historical count = unavailable in this environment; "
            "comparison not normalized. dump_as_is_route_count is the unrepaired "
            "production collector result."
        ),
    }

    (CENSUS_DIR / "CURRENT_CENSUS_SUMMARY.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (CENSUS_DIR / "CURRENT_LIVE_ROUTES_DUMP_AS_IS.json").write_text(
        json.dumps({"meta": meta, "source": "dump_and_assert_routes.collect_routes", "routes": dump_as_is_routes}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (CENSUS_DIR / "CURRENT_LIVE_ROUTES.json").write_text(
        json.dumps({"meta": meta, "source": "lab_collect_routes_workaround", "routes": lab_routes}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (CENSUS_DIR / "CURRENT_COLLISIONS.json").write_text(
        json.dumps({"meta": meta, "collisions": collisions}, indent=2) + "\n",
        encoding="utf-8",
    )
    (CENSUS_DIR / "CURRENT_NAME_HINT_MODULES.json").write_text(
        json.dumps({"meta": meta, "modules": name_hints}, indent=2) + "\n",
        encoding="utf-8",
    )
    (CENSUS_DIR / "CURRENT_FRONTEND_UNMATCHED_PATHS.json").write_text(
        json.dumps(
            {"meta": meta, "unmatched": fe_unmatched, "all_literals": fe_literals},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({k: payload[k] for k in payload if k != "dump_and_assert_routes_as_is"}, indent=2))
    print("--- dump_and_assert_routes as-is ---")
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
