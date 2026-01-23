#!/usr/bin/env python3
"""
Deprecation Sunset Enforcer
===========================

CI check that fails when deprecated routes exceed their sunset date.

This makes removal **self-executing**: if you don't remove a deprecated
route by its sunset date, CI fails and blocks merges.

Usage:
  python -m app.ci.check_deprecation_sunset              # Normal mode
  python -m app.ci.check_deprecation_sunset --warn-only  # Warning mode (no failure)
  python -m app.ci.check_deprecation_sunset --upcoming 30  # Warn about routes sunsetting in 30 days

Exit codes:
  0 = OK (no overdue sunsets)
  1 = Overdue sunsets found (BLOCKING)
  2 = Configuration error
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


def load_registry() -> Dict[str, Any]:
    """Load the deprecation registry."""
    registry_path = Path(__file__).parent / "deprecation_registry.json"
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}")
        sys.exit(2)

    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_module_exists(module_path: str) -> bool:
    """Check if a module still exists (route not yet removed)."""
    # Convert module path to file path
    # e.g., "app.routers.legacy.guitar_legacy_router" -> "app/routers/legacy/guitar_legacy_router.py"
    parts = module_path.split(".")
    file_path = Path(__file__).parent.parent / "/".join(parts[1:])  # Skip "app."
    file_path = file_path.with_suffix(".py")

    return file_path.exists()


def check_sunsets(registry: Dict[str, Any], warn_days: int = 0) -> tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Check for overdue and upcoming sunsets.

    Returns:
        (overdue, upcoming, removed) - lists of route entries
    """
    today = datetime.now().date()
    warn_threshold = today + timedelta(days=warn_days)

    overdue = []
    upcoming = []
    removed = []

    for route in registry.get("routes", []):
        sunset_str = route.get("sunset_date")
        if not sunset_str:
            continue

        sunset_date = datetime.strptime(sunset_str, "%Y-%m-%d").date()
        module = route.get("module", "")

        # Check if the module still exists
        if not check_module_exists(module):
            removed.append(route)
            continue

        # Module exists - check if it's overdue
        if sunset_date < today:
            overdue.append({**route, "_days_overdue": (today - sunset_date).days})
        elif sunset_date <= warn_threshold:
            upcoming.append({**route, "_days_until": (sunset_date - today).days})

    return overdue, upcoming, removed


def main():
    parser = argparse.ArgumentParser(description="Check deprecation sunset dates")
    parser.add_argument("--warn-only", action="store_true", help="Warn but don't fail")
    parser.add_argument("--upcoming", type=int, default=30, help="Warn about sunsets within N days")
    args = parser.parse_args()

    registry = load_registry()
    overdue, upcoming, removed = check_sunsets(registry, warn_days=args.upcoming)

    print("=" * 60)
    print("  DEPRECATION SUNSET CHECK")
    print("=" * 60)
    print()

    # Report removed (good)
    if removed:
        print(f"[OK] REMOVED ({len(removed)} routes successfully sunset):")
        for route in removed:
            print(f"   - {route['id']}: {route['module']}")
        print()

    # Report upcoming (warning)
    if upcoming:
        print(f"[WARN] UPCOMING ({len(upcoming)} routes sunsetting soon):")
        for route in upcoming:
            days = route["_days_until"]
            print(f"   - {route['id']}: {days} days until {route['sunset_date']}")
            print(f"     Module: {route['module']}")
            print(f"     Old: {route['old_prefix']} -> New: {route['new_prefix']}")
        print()

    # Report overdue (blocking)
    if overdue:
        print(f"[FAIL] OVERDUE ({len(overdue)} routes past sunset date):")
        for route in overdue:
            days = route["_days_overdue"]
            print(f"   - {route['id']}: {days} days overdue (sunset was {route['sunset_date']})")
            print(f"     Module: {route['module']}")
            print(f"     Action: REMOVE THIS MODULE")
        print()

    # Summary
    print("=" * 60)
    total = len(registry.get("routes", []))
    print(f"  Total registered: {total}")
    print(f"  Removed:          {len(removed)}")
    print(f"  Upcoming:         {len(upcoming)}")
    print(f"  Overdue:          {len(overdue)}")
    print("=" * 60)

    if overdue and not args.warn_only:
        print()
        print("[FAIL] Overdue deprecations must be removed before merge.")
        print("   To fix: Remove the overdue modules listed above.")
        print("   To extend: Update sunset_date in deprecation_registry.json (requires governance label).")
        sys.exit(1)

    if overdue and args.warn_only:
        print()
        print("[WARN] Overdue deprecations found (--warn-only mode).")
        sys.exit(0)

    print()
    print("[OK] PASSED: No overdue deprecations.")
    sys.exit(0)


if __name__ == "__main__":
    main()
