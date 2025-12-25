from __future__ import annotations

import sys
from typing import Dict, List, Tuple

from fastapi.routing import APIRoute

from app.main import app
from app.governance.endpoint_registry import ENDPOINT_REGISTRY, EndpointStatus, lookup_endpoint


def main() -> int:
    routes: List[APIRoute] = [r for r in app.routes if isinstance(r, APIRoute)]

    # Build set of (method, path_pattern) present in actual app
    actual: Dict[Tuple[str, str], APIRoute] = {}
    for r in routes:
        for m in sorted(getattr(r, "methods") or []):
            actual[(m.upper(), r.path)] = r

    failures: List[str] = []

    # 1) Registry entries must exist in app
    for (method, path_pattern), info in sorted(ENDPOINT_REGISTRY.items()):
        if (method, path_pattern) not in actual:
            failures.append(
                f"Registry lists {method} {path_pattern} as {info.status.value}, but route not found in app."
            )

    # 2) Legacy/Shadow routes should be annotated OR explicitly exempted
    #    (We only enforce this for routes that appear in ENDPOINT_REGISTRY.)
    for (method, path_pattern), route in sorted(actual.items()):
        info = lookup_endpoint(method, path_pattern)
        if not info:
            continue  # not governed yet

        if info.status in {EndpointStatus.LEGACY, EndpointStatus.SHADOW}:
            endpoint = getattr(route, "endpoint", None)
            anno = getattr(endpoint, "__endpoint_status__", None) if endpoint else None
            if not anno:
                failures.append(
                    f"{method} {path_pattern} is {info.status.value} in registry, but endpoint is missing @endpoint_meta(...) annotation."
                )

    if failures:
        print("[check_endpoint_governance] FAIL")
        for f in failures:
            print(f" - {f}")
        return 2

    print("[check_endpoint_governance] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
