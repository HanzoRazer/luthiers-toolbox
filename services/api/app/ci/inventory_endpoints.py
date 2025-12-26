from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List

from .feature_hunt_types import Endpoint, endpoint_to_dict

DEFAULT_APP_MODULE = os.getenv("APP_MODULE", "app.main:app")


def _load_app():
    """
    Import the FastAPI app from APP_MODULE (default: app.main:app).

    Works in CI without running a server.
    """
    if ":" not in DEFAULT_APP_MODULE:
        raise SystemExit(f"APP_MODULE must be like 'app.main:app' (got: {DEFAULT_APP_MODULE})")

    mod, obj = DEFAULT_APP_MODULE.split(":", 1)
    module = __import__(mod, fromlist=[obj])
    app = getattr(module, obj)
    return app


def _collect_endpoints_from_openapi(app) -> List[Endpoint]:
    spec: Dict = app.openapi()
    paths: Dict = spec.get("paths", {}) or {}

    out: List[Endpoint] = []
    for path, operations in paths.items():
        if not isinstance(operations, dict):
            continue
        for method, op in operations.items():
            m = (method or "").upper()
            if m in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                out.append(Endpoint(method=m, path=path))
    # Sort deterministically
    out.sort(key=lambda e: (e.path, e.method))
    return out


def main(argv: List[str]) -> int:
    """
    Usage:
      python -m app.ci.inventory_endpoints > endpoints.json
      python -m app.ci.inventory_endpoints --out /path/file.json
    """
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        try:
            out_path = argv[i + 1]
        except Exception as e:
            raise SystemExit("--out requires a path") from e

    app = _load_app()
    eps = _collect_endpoints_from_openapi(app)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "app_module": DEFAULT_APP_MODULE,
        "count": len(eps),
        "endpoints": [endpoint_to_dict(e) for e in eps],
    }

    text = json.dumps(payload, indent=2, sort_keys=True)

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(out_path)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
