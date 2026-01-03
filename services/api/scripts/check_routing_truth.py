#!/usr/bin/env python3
"""
Routing Truth CI Gate (Contract v1)

Compares:
  - expected endpoints from services/api/app/data/endpoint_truth.json
  - runtime endpoints from GET /api/_meta/routing-truth

Outputs:
  - ❌ missing: documented but not mounted (fail for required lanes)
  - ⚠️  undocumented: mounted but not documented (warning by default)

Lane policy:
  - Fail lanes (default): CORE,META,OPERATION,RMOS
  - Warn lanes (default): CAM,TOOLING,ART,COMPARE,SIMULATION,UTILITY
  - LEGACY is never "required" unless an entry explicitly sets required=true

Env overrides:
  ROUTING_TRUTH_API_URL            (default http://127.0.0.1:8000)
  ROUTING_TRUTH_TRUTH_FILE         (default services/api/app/data/endpoint_truth.json)
  ROUTING_TRUTH_ENDPOINT_PATH      (optional: force endpoint path, e.g. /api/_meta/routing-truth)
  ROUTING_TRUTH_FAIL_LANES         (csv)
  ROUTING_TRUTH_WARN_ON_UNDOC      (true/false, default true)
  ROUTING_TRUTH_FAIL_ON_UNDOC      (true/false, default false)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import urllib.request


DEFAULT_FAIL_LANES = {"CORE", "META", "OPERATION", "RMOS"}
DEFAULT_WARN_LANES = {"CAM", "TOOLING", "ART", "COMPARE", "SIMULATION", "UTILITY"}


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _csv_env(name: str, default: Set[str]) -> Set[str]:
    v = os.getenv(name)
    if not v:
        return set(default)
    return {x.strip().upper() for x in v.split(",") if x.strip()}


def _norm_path(p: str) -> str:
    # Normalize path for comparison:
    # - strip trailing slashes (except root "/")
    # - normalize fastapi {param} names to "{}" to avoid drift noise
    p = (p or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    p = re.sub(r"\{[^}]+\}", "{}", p)  # {id} -> {}
    return p


def _fetch_json(url: str, timeout_s: int = 10) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON from {url}: {e}\nRaw: {raw[:4000]}")


def _try_fetch_any(api_url: str, paths: List[str]) -> Tuple[str, Dict[str, Any]]:
    """Try multiple endpoint paths and return the first that works."""
    last_err: Optional[Exception] = None
    for p in paths:
        u = f"{api_url}{p}"
        try:
            return p, _fetch_json(u)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch routing-truth from any endpoint paths {paths}. Last error: {last_err}")


def _read_truth_file(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON truth file at {path}: {e}")


def _validate_truth_shape(doc: Dict[str, Any]) -> None:
    """Validate endpoint_truth.json schema - fails loudly if anything is wrong."""
    if not isinstance(doc, dict):
        raise RuntimeError("endpoint_truth.json must be an object")
    if "routes" not in doc or not isinstance(doc["routes"], list):
        raise RuntimeError("endpoint_truth.json must contain 'routes': []")
    for i, r in enumerate(doc["routes"]):
        if not isinstance(r, dict):
            raise RuntimeError(f"routes[{i}] must be an object")
        # Check required fields
        for k in ("path", "methods", "name", "lane", "deprecated"):
            if k not in r:
                raise RuntimeError(f"routes[{i}] missing required field '{k}'")
        # Type validation
        if not isinstance(r["methods"], list) or not all(isinstance(m, str) for m in r["methods"]):
            raise RuntimeError(f"routes[{i}].methods must be string[]")
        if not isinstance(r["path"], str) or not r["path"]:
            raise RuntimeError(f"routes[{i}].path must be non-empty string")
        if not isinstance(r["name"], str) or not r["name"]:
            raise RuntimeError(f"routes[{i}].name must be non-empty string")
        if not isinstance(r["lane"], str) or not r["lane"]:
            raise RuntimeError(f"routes[{i}].lane must be non-empty string")
        if not isinstance(r["deprecated"], bool):
            raise RuntimeError(f"routes[{i}].deprecated must be boolean")


def _expected_sets(
    doc: Dict[str, Any],
    fail_lanes: Set[str],
) -> Tuple[Set[str], Set[str]]:
    """
    Returns (expected_required_paths, expected_all_paths)
    Required = route.required==true OR lane in fail_lanes (except LEGACY).
    """
    required: Set[str] = set()
    allp: Set[str] = set()
    for r in doc["routes"]:
        path = _norm_path(str(r.get("path", "")))
        lane = str(r.get("lane", "")).upper()
        allp.add(path)

        explicit_required = r.get("required")
        if explicit_required is True:
            required.add(path)
            continue

        if lane == "LEGACY":
            # legacy is never required unless explicitly required=true
            continue

        if lane in fail_lanes:
            required.add(path)
    return required, allp


def _runtime_paths(runtime_doc: Dict[str, Any]) -> Set[str]:
    routes = runtime_doc.get("routes")
    if not isinstance(routes, list):
        raise RuntimeError("routing-truth response missing 'routes' list")
    out: Set[str] = set()
    for r in routes:
        if not isinstance(r, dict):
            continue
        out.add(_norm_path(str(r.get("path", ""))))
    return out


def main() -> int:
    api_url = os.getenv("ROUTING_TRUTH_API_URL", "http://127.0.0.1:8000").rstrip("/")
    truth_path = Path(os.getenv("ROUTING_TRUTH_TRUTH_FILE", "services/api/app/data/endpoint_truth.json"))
    fail_lanes = _csv_env("ROUTING_TRUTH_FAIL_LANES", DEFAULT_FAIL_LANES)

    warn_on_undoc = _bool_env("ROUTING_TRUTH_WARN_ON_UNDOC", True)
    fail_on_undoc = _bool_env("ROUTING_TRUTH_FAIL_ON_UNDOC", False)

    if not truth_path.exists():
        print(f"❌ Truth file not found: {truth_path}", file=sys.stderr)
        return 2

    truth = _read_truth_file(truth_path)
    _validate_truth_shape(truth)
    expected_required, expected_all = _expected_sets(truth, fail_lanes=fail_lanes)

    # Auto-detect routing truth endpoint (or use forced path)
    forced = os.getenv("ROUTING_TRUTH_ENDPOINT_PATH")
    candidate_paths = [forced] if forced else [
        "/api/_meta/routing-truth",
        "/meta/router-truth",
        "/api/meta/router-truth",
    ]
    candidate_paths = [p for p in candidate_paths if p]

    used_path, rt = _try_fetch_any(api_url, candidate_paths)
    runtime = _runtime_paths(rt)

    missing_required = sorted(expected_required - runtime)
    missing_any = sorted(expected_all - runtime)
    undocumented = sorted(runtime - expected_all)

    exit_code = 0

    if missing_required:
        print("❌ MISSING REQUIRED ENDPOINTS (documented but not mounted):")
        for p in missing_required:
            print(f"  - {p}")
        exit_code = 1

    # Optional: display non-required missing as FYI (does not fail)
    missing_non_required = [p for p in missing_any if p not in set(missing_required)]
    if missing_non_required:
        print("ℹ️  MISSING NON-REQUIRED ENDPOINTS (documented but not mounted):")
        for p in missing_non_required:
            print(f"  - {p}")

    if undocumented:
        msg = "⚠️  UNDOCUMENTED ENDPOINTS (mounted but not in truth file):"
        if fail_on_undoc:
            msg = "❌ UNDOCUMENTED ENDPOINTS (mounted but not in truth file):"
        if warn_on_undoc or fail_on_undoc:
            print(msg)
            for p in undocumented:
                print(f"  - {p}")
        if fail_on_undoc:
            exit_code = 1

    # Summary (always)
    print("\n--- Routing Truth Summary ---")
    print(f"API_URL: {api_url}")
    print(f"Routing truth endpoint: {used_path}")
    print(f"Truth file: {truth_path}")
    print(f"Expected(all): {len(expected_all)}")
    print(f"Expected(required): {len(expected_required)}")
    print(f"Runtime: {len(runtime)}")
    print(f"Missing(required): {len(missing_required)}")
    print(f"Undocumented: {len(undocumented)}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
