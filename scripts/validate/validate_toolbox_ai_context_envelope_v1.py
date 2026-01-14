#!/usr/bin/env python3
"""
Validator CLI for toolbox_ai_context_envelope_v1.

Usage:
    python scripts/validate/validate_toolbox_ai_context_envelope_v1.py --envelope envelope.json
    python scripts/validate/validate_toolbox_ai_context_envelope_v1.py --envelope envelope.json --schema path/to/schema.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import jsonschema
except ImportError:
    jsonschema = None


def load_json(p: Path) -> Dict[str, Any]:
    """Load JSON file."""
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate toolbox_ai_context_envelope_v1 JSON"
    )
    ap.add_argument(
        "--envelope",
        required=True,
        help="Path to envelope JSON file",
    )
    ap.add_argument(
        "--schema",
        default="contracts/toolbox_ai_context_envelope_v1.schema.json",
        help="Path to schema JSON file",
    )
    args = ap.parse_args()

    env_path = Path(args.envelope).resolve()
    schema_path = Path(args.schema).resolve()

    # Check files exist
    if not env_path.exists():
        print(f"[ai-context] ERROR: envelope not found: {env_path}", file=sys.stderr)
        return 2

    if not schema_path.exists():
        print(f"[ai-context] ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 2

    if jsonschema is None:
        print(
            "[ai-context] ERROR: jsonschema not installed in this environment",
            file=sys.stderr,
        )
        return 2

    # Load files
    envelope = load_json(env_path)
    schema = load_json(schema_path)

    # Validate against schema
    try:
        jsonschema.validate(instance=envelope, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"[ai-context] FAIL: schema validation failed: {e.message}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ai-context] FAIL: schema validation failed: {e}", file=sys.stderr)
        return 1

    # Extra invariants (belt + suspenders)
    caps = envelope.get("capabilities", {})

    if caps.get("allow_sensitive_manufacturing") is not False:
        print(
            "[ai-context] FAIL: allow_sensitive_manufacturing must be false",
            file=sys.stderr,
        )
        return 1

    if caps.get("allow_pii") is not False:
        print("[ai-context] FAIL: allow_pii must be false", file=sys.stderr)
        return 1

    # Check redaction mode
    redaction = envelope.get("redaction", {})
    if redaction.get("mode") != "strict":
        print("[ai-context] FAIL: redaction.mode must be 'strict'", file=sys.stderr)
        return 1

    if redaction.get("ruleset") != "toolbox_ai_redaction_strict_v1":
        print(
            "[ai-context] FAIL: redaction.ruleset must be 'toolbox_ai_redaction_strict_v1'",
            file=sys.stderr,
        )
        return 1

    print("[ai-context] PASS: envelope validates (v1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
