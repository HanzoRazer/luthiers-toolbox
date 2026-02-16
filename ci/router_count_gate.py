#!/usr/bin/env python3
"""CI gate: enforce router file count with ratchet baseline.

Usage:
    python ci/router_count_gate.py              # Check against baseline
    python ci/router_count_gate.py --update     # Update baseline
    python ci/router_count_gate.py --strict     # No baseline tolerance

Exit codes:
    0 - Router count within limits
    1 - Router count exceeds baseline
    2 - Script error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Baseline file location
BASELINE_FILE = Path(__file__).parent / "router_count_baseline.json"

# Patterns that indicate a router file
ROUTER_PATTERNS = ["*router*.py", "*_routes.py"]


def count_routers(root: Path) -> dict[str, list[str]]:
    """Count router files by directory."""
    app_dir = root / "services" / "api" / "app"
    if not app_dir.exists():
        return {}

    routers_by_dir: dict[str, list[str]] = {}

    for pattern in ROUTER_PATTERNS:
        for f in app_dir.rglob(pattern):
            if f.is_file() and not f.name.startswith("__"):
                rel_dir = str(f.parent.relative_to(app_dir))
                rel_file = str(f.relative_to(app_dir))
                if rel_dir not in routers_by_dir:
                    routers_by_dir[rel_dir] = []
                routers_by_dir[rel_dir].append(rel_file)

    return routers_by_dir


def count_routes(root: Path) -> int:
    """Count @router.* decorators."""
    app_dir = root / "services" / "api" / "app"
    count = 0

    for f in app_dir.rglob("*.py"):
        try:
            content = f.read_text(encoding="utf-8")
            count += content.count("@router.")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {f}: {e}", file=sys.stderr)

    return count


def load_baseline() -> dict:
    """Load baseline from JSON file."""
    if not BASELINE_FILE.exists():
        return {"router_files": 999, "route_decorators": 999}
    try:
        return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"router_files": 999, "route_decorators": 999}


def save_baseline(data: dict) -> None:
    """Save baseline to JSON file."""
    BASELINE_FILE.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Router count gate")
    parser.add_argument("--update", action="store_true", help="Update baseline")
    parser.add_argument("--strict", action="store_true", help="No baseline tolerance")
    parser.add_argument("--target-files", type=int, default=100, help="Target router file count")
    parser.add_argument("--target-routes", type=int, default=600, help="Target route count")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    routers_by_dir = count_routers(root)
    total_files = sum(len(files) for files in routers_by_dir.values())
    total_routes = count_routes(root)

    if args.update:
        baseline = {
            "router_files": total_files,
            "route_decorators": total_routes,
            "by_directory": {k: len(v) for k, v in sorted(routers_by_dir.items())},
        }
        save_baseline(baseline)
        print(f"Baseline updated:")
        print(f"  Router files: {total_files}")
        print(f"  Route decorators: {total_routes}")
        print(f"\nTop directories:")
        for dir_name, count in sorted(baseline["by_directory"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {count:3d}  {dir_name}")
        return 0

    baseline = load_baseline()
    baseline_files = baseline.get("router_files", 999)
    baseline_routes = baseline.get("route_decorators", 999)

    if args.strict:
        target_files = args.target_files
        target_routes = args.target_routes
    else:
        target_files = baseline_files
        target_routes = baseline_routes

    errors = []

    if total_files > target_files:
        errors.append(f"Router files: {total_files} > {target_files} (baseline)")

    if total_routes > target_routes:
        errors.append(f"Route decorators: {total_routes} > {target_routes} (baseline)")

    if errors:
        print("FAIL: Router count regression")
        for err in errors:
            print(f"  {err}")
        print(f"\nCurrent state:")
        print(f"  Router files: {total_files}")
        print(f"  Route decorators: {total_routes}")
        print(f"\nTo fix: consolidate routers before adding new ones")
        print(f"Or run with --update to accept new baseline (requires justification)")
        return 1

    # Check for improvements
    improvements = []
    if total_files < baseline_files:
        improvements.append(f"Router files improved: {total_files} < {baseline_files}")
    if total_routes < baseline_routes:
        improvements.append(f"Route decorators improved: {total_routes} < {baseline_routes}")

    if improvements:
        print(f"OK: Improvements detected (run --update to lock in gains)")
        for imp in improvements:
            print(f"  {imp}")
    else:
        print(f"OK: Router counts within baseline")

    print(f"\nCurrent state:")
    print(f"  Router files: {total_files} (baseline: {baseline_files})")
    print(f"  Route decorators: {total_routes} (baseline: {baseline_routes})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
