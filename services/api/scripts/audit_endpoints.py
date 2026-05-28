#!/usr/bin/env python3
"""Audit @router.* endpoint counts for CI-RED-015-C."""
import json
import re
from collections import defaultdict
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent / "app"
DECORATOR = re.compile(r"@router\.(get|post|put|patch|delete)\(")
ROUTE = re.compile(
    r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'
)


def count_endpoints() -> int:
    total = 0
    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
        except OSError:
            continue
        total += len(DECORATOR.findall(content))
    return total


def audit():
    by_file: dict[str, int] = defaultdict(int)
    routes: list[tuple[str, str, str]] = []

    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = str(pyfile.relative_to(APP_ROOT))
        n = len(DECORATOR.findall(content))
        if n:
            by_file[rel] += n
        for m in ROUTE.finditer(content):
            routes.append((rel, m.group(1).upper(), m.group(2)))

    total = sum(by_file.values())
    baseline = 942
    delta = total - baseline

    print(f"TOTAL={total} baseline={baseline} delta=+{delta}")
    print(f"FILES_WITH_ROUTES={len(by_file)}")
    print("\n--- top 40 files ---")
    for f, c in sorted(by_file.items(), key=lambda x: -x[1])[:40]:
        print(f"{c:4d}  {f}")

    # Flag suspicious patterns
    debug = [r for r in routes if any(k in r[2].lower() for k in ("debug", "test", "dev", "mock"))]
    duplicate_paths: dict[str, list] = defaultdict(list)
    for rel, method, path in routes:
        duplicate_paths[f"{method} {path}"].append(rel)

    dups = {k: v for k, v in duplicate_paths.items() if len(v) > 1}

    print(f"\nDEBUG_LIKE_ROUTES={len(debug)}")
    for rel, method, path in sorted(debug)[:30]:
        print(f"  {method} {path}  ({rel})")
    if len(debug) > 30:
        print(f"  ... and {len(debug) - 30} more")

    print(f"\nDUPLICATE_ROUTE_KEYS={len(dups)}")
    for key, files in sorted(dups.items(), key=lambda x: -len(x[1]))[:25]:
        print(f"  {key}  x{len(files)}")
        for f in files[:5]:
            print(f"    - {f}")
        if len(files) > 5:
            print(f"    ... +{len(files) - 5} more")

    # Write full route list for diff
    out = Path(__file__).resolve().parent.parent / "metrics" / "endpoint_audit_current.json"
    payload = {
        "total": total,
        "baseline": baseline,
        "delta": delta,
        "by_file": dict(sorted(by_file.items(), key=lambda x: -x[1])),
        "routes": [{"file": r[0], "method": r[1], "path": r[2]} for r in sorted(routes)],
        "duplicate_keys": {k: v for k, v in sorted(dups.items(), key=lambda x: -len(x[1]))},
        "debug_like": [{"file": r[0], "method": r[1], "path": r[2]} for r in debug],
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    audit()
