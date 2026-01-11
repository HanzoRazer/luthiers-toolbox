#!/usr/bin/env python3
"""
Validator: Smart Guitar -> ToolBox Telemetry v1

Validates a telemetry payload JSON against:
  contracts/smart_guitar_toolbox_telemetry_v1.schema.json

Exit codes:
  0 = valid
  1 = invalid payload
  2 = execution error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import jsonschema


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="Path to telemetry payload JSON")
    ap.add_argument(
        "--schema",
        default="contracts/smart_guitar_toolbox_telemetry_v1.schema.json",
        help="Path to schema JSON (default: contracts/...)",
    )
    args = ap.parse_args()

    try:
        payload_path = Path(args.payload).resolve()
        schema_path = Path(args.schema).resolve()

        if not payload_path.exists():
            print(f"[sg-telemetry] ERROR: payload not found: {payload_path}", file=sys.stderr)
            return 2
        if not schema_path.exists():
            print(f"[sg-telemetry] ERROR: schema not found: {schema_path}", file=sys.stderr)
            return 2

        payload = load_json(payload_path)
        schema = load_json(schema_path)

        # Draft 2020-12 validator
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

        if errors:
            print(f"[sg-telemetry] FAIL: {len(errors)} validation errors", file=sys.stderr)
            for e in errors[:50]:
                loc = "$"
                if e.path:
                    loc += "." + ".".join(str(p) for p in e.path)
                print(f"  - {loc}: {e.message}", file=sys.stderr)
            if len(errors) > 50:
                print("  (output truncated)", file=sys.stderr)
            return 1

        print("[sg-telemetry] PASS: payload is valid")
        return 0

    except json.JSONDecodeError as e:
        print(f"[sg-telemetry] ERROR: invalid JSON: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[sg-telemetry] ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
