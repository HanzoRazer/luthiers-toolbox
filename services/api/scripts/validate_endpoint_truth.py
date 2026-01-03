#!/usr/bin/env python3
"""
Lightweight validator for services/api/app/data/endpoint_truth.json.
Run locally or wire into CI if you want.

Usage:
    python scripts/validate_endpoint_truth.py
    python scripts/validate_endpoint_truth.py path/to/custom_truth.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "services/api/app/data/endpoint_truth.json")
    if not path.exists():
        print(f"❌ Not found: {path}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        return 2

    if not isinstance(doc, dict) or "routes" not in doc or not isinstance(doc["routes"], list):
        print("❌ endpoint_truth.json must be an object with routes: []", file=sys.stderr)
        return 2

    required = {"path", "methods", "name", "lane", "deprecated"}
    for i, r in enumerate(doc["routes"]):
        if not isinstance(r, dict):
            print(f"❌ routes[{i}] must be object", file=sys.stderr)
            return 2
        missing = required - set(r.keys())
        if missing:
            print(f"❌ routes[{i}] missing {sorted(missing)}", file=sys.stderr)
            return 2
        if not isinstance(r["methods"], list) or not all(isinstance(m, str) for m in r["methods"]):
            print(f"❌ routes[{i}].methods must be string[]", file=sys.stderr)
            return 2
        if not isinstance(r["path"], str) or not r["path"]:
            print(f"❌ routes[{i}].path must be non-empty string", file=sys.stderr)
            return 2
        if not isinstance(r["name"], str) or not r["name"]:
            print(f"❌ routes[{i}].name must be non-empty string", file=sys.stderr)
            return 2
        if not isinstance(r["lane"], str) or not r["lane"]:
            print(f"❌ routes[{i}].lane must be non-empty string", file=sys.stderr)
            return 2
        if not isinstance(r["deprecated"], bool):
            print(f"❌ routes[{i}].deprecated must be boolean", file=sys.stderr)
            return 2

    print(f"✅ OK: {path} ({len(doc['routes'])} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
