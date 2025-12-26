from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

from .feature_hunt_types import Endpoint, safe_json
from .inventory_endpoints import _collect_endpoints_from_openapi, _load_app
from .parse_truth_map import DEFAULT_TRUTH_MAP_PATH, parse_truth_map_file
from .scan_frontend_api_usage import scan_frontend_api_paths, summarize_frontend_paths

DEFAULT_OUT = os.getenv("FEATURE_HUNT_REPORT_PATH", "")

# Exit codes
EXIT_OK = 0
EXIT_MISSING_FROM_APP = 2
EXIT_EXTRA_IN_APP = 3
EXIT_FRONTEND_CALLS_MISSING = 4


def _to_set(eps: List[Endpoint]) -> Set[str]:
    return {e.key() for e in eps}


def _endpoint_key_to_path(k: str) -> str:
    # "GET /api/..." -> "/api/..."
    parts = k.split(" ", 1)
    return parts[1] if len(parts) == 2 else k


def main(argv: List[str]) -> int:
    """
    Usage:
      python -m app.ci.feature_hunt --truth ENDPOINT_TRUTH_MAP.md --out report.json

    Env:
      APP_MODULE (default: app.main:app)
      ENDPOINT_TRUTH_MAP_PATH (default: ENDPOINT_TRUTH_MAP.md)
      FEATURE_HUNT_REPORT_PATH (optional)
    """
    truth_path = DEFAULT_TRUTH_MAP_PATH
    out_path = DEFAULT_OUT

    if "--truth" in argv:
        i = argv.index("--truth")
        truth_path = argv[i + 1]
    if "--out" in argv:
        i = argv.index("--out")
        out_path = argv[i + 1]

    app = _load_app()
    app_eps = _collect_endpoints_from_openapi(app)
    truth_eps = parse_truth_map_file(truth_path)

    app_set = _to_set(app_eps)
    truth_set = _to_set(truth_eps)

    missing_from_app = sorted(truth_set - app_set)
    extra_in_app = sorted(app_set - truth_set)

    # frontend scan: paths only (method-agnostic)
    fe_paths = scan_frontend_api_paths()
    app_paths = {_endpoint_key_to_path(k) for k in app_set}
    fe_missing = sorted([p for p in fe_paths if p.startswith("/api/") and p not in app_paths])

    report: Dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "truth_map_path": truth_path,
        "counts": {
            "truth_endpoints": len(truth_eps),
            "app_endpoints": len(app_eps),
            "missing_from_app": len(missing_from_app),
            "extra_in_app": len(extra_in_app),
            "frontend_api_paths": len(fe_paths),
            "frontend_missing_paths": len(fe_missing),
        },
        "missing_from_app": missing_from_app,
        "extra_in_app": extra_in_app,
        "frontend": {
            "roots": ["packages/client/src", "packages/sdk/src"],
            "summary_by_domain": summarize_frontend_paths(fe_paths),
            "missing_paths": fe_missing,
        },
    }

    text = json.dumps(safe_json(report), indent=2, sort_keys=True) + "\n"

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(out_path)
    else:
        print(text)

    # Gate logic (non-breaking but enforceable):
    # - missing_from_app is serious (truth says it should exist)
    # - frontend_missing means UI calls endpoints that app doesn't have
    # - extra_in_app might be okay if truth map is stale; still flag with code 3
    if missing_from_app:
        return EXIT_MISSING_FROM_APP
    if fe_missing:
        return EXIT_FRONTEND_CALLS_MISSING
    if extra_in_app:
        return EXIT_EXTRA_IN_APP
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
