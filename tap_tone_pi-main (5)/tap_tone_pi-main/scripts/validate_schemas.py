#!/usr/bin/env python3
"""
Walks out/** for JSON artifacts, validates them against contracts/schemas
by (schema_id, schema_version). Fails non-zero on any invalid file.

Usage:
  python scripts/validate_schemas.py --out-root out --schemas-root contracts/schemas

Options:
  --strict    Fail on artifacts missing schema_id/schema_version (default: skip them)
  --verbose   Show skipped files
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Dict, Tuple

from jsonschema import Draft202012Validator, validate

# Fallback map for environments where registry is unavailable
_FALLBACK_SCHEMA_MAP: Dict[Tuple[str, str], str] = {
    ("tap_peaks", "1.0"): "tap_peaks.schema.json",
    ("moe_result", "1.0"): "moe_result.schema.json",
    ("measurement_manifest", "1.0"): "manifest.schema.json",
    ("chladni_run", "1.0"): "chladni_run.schema.json",
}


def load_registry(schemas_root: Path) -> Dict[Tuple[str, str], dict]:
    """Load schemas from schema_registry.json (authoritative source)."""
    registry_path = schemas_root.parent / "schema_registry.json"
    if not registry_path.exists():
        # Fallback to hardcoded map if registry not present
        return _load_from_fallback(schemas_root)
    
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    loaded = {}
    schemas = reg["schemas"]
    # Handle both list format and dict format
    if isinstance(schemas, dict):
        items = [(k, v) for k, v in schemas.items()]
    else:
        items = [(ent["schema_id"], ent) for ent in schemas]
    for sid, ent in items:
        ver, f = ent["version"], ent.get("path") or ent["file"]
        schema_path = Path(f)
        if not schema_path.exists():
            raise FileNotFoundError(f"Registry references missing schema: {f}")
        schema_content = json.loads(schema_path.read_text(encoding="utf-8"))
        # Key by (schema_id, version)
        loaded[(sid, ver)] = schema_content
        # Also key by schema_version_const if present (phase2 uses these)
        if "schema_version_const" in ent:
            loaded[(sid, ent["schema_version_const"])] = schema_content
    return loaded


def _load_from_fallback(schemas_root: Path) -> Dict[Tuple[str, str], dict]:
    """Fallback loader using hardcoded map."""
    loaded = {}
    for (schema_id, version), fname in _FALLBACK_SCHEMA_MAP.items():
        p = schemas_root / fname
        if not p.exists():
            raise FileNotFoundError(f"Missing schema file: {p}")
        loaded[(schema_id, version)] = json.loads(p.read_text(encoding="utf-8"))
    return loaded


def load_schema_index(schemas_root: Path) -> Dict[Tuple[str, str], dict]:
    """Load schemas - prefer registry, fallback to hardcoded map."""
    return load_registry(schemas_root)

def discover_json_files(out_root: Path):
    for p in out_root.rglob("*.json"):
        yield p

# Aliases: map output schema_id to registry key
_SCHEMA_ALIASES = {
    "measurement_manifest": "manifest",
}

def _normalize_version(v: str) -> str:
    """Normalize version: 1.0 -> 1.0.0, but leave version consts unchanged."""
    # If it looks like a version const (contains letters after numbers), don't normalize
    if not v or not v[0].isdigit():
        return v
    parts = v.split(".")
    # Only normalize if all parts are numeric
    if not all(p.isdigit() for p in parts):
        return v
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:3])

def identify(doc: dict) -> Tuple[str, str]:
    # Flexible: MOE uses artifact_type 'bending_moe' but schema_id 'moe_result'
    schema_id = str(doc.get("schema_id") or "").strip()
    version = str(doc.get("schema_version") or "").strip()

    # Some legacy artifacts may lack schema_id; try to infer by artifact_type
    if not schema_id and "artifact_type" in doc:
        at = str(doc["artifact_type"]).strip()
        if at == "bending_moe":
            schema_id = "moe_result"
        elif at == "chladni_run":
            schema_id = "chladni_run"
        elif at == "chladni_peaks":
            schema_id = "tap_peaks"
        elif at == "measurement_manifest":
            schema_id = "measurement_manifest"

    # Apply aliases
    schema_id = _SCHEMA_ALIASES.get(schema_id, schema_id)
    # Normalize version
    if version:
        version = _normalize_version(version)

    return schema_id, version

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default="out")
    ap.add_argument("--schemas-root", default="contracts/schemas")
    ap.add_argument("--strict", action="store_true",
                    help="Fail on artifacts missing schema_id/schema_version")
    ap.add_argument("--verbose", action="store_true",
                    help="Show skipped files")
    args = ap.parse_args()

    out_root = Path(args.out_root)
    schemas_root = Path(args.schemas_root)

    if not out_root.exists():
        print(f"[validate] out root not found: {out_root}")
        sys.exit(0)  # nothing to validate

    schemas = load_schema_index(schemas_root)

    bad = []
    skipped = []
    total = 0
    for jf in discover_json_files(out_root):
        try:
            doc = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            bad.append((jf, f"Invalid JSON: {e}"))
            continue

        schema_id, version = identify(doc)
        if not schema_id or not version:
            if args.strict:
                bad.append((jf, "Missing schema_id/schema_version (and could not infer)"))
            else:
                skipped.append(jf)
            continue

        key = (schema_id, version)
        if key not in schemas:
            bad.append((jf, f"No schema registered for ({schema_id}, {version})"))
            continue

        schema = schemas[key]
        validator = Draft202012Validator(schema)
        errs = sorted(validator.iter_errors(doc), key=lambda e: e.path)
        if errs:
            for e in errs:
                bad.append((jf, f"{'/'.join(map(str, e.path))}: {e.message}"))
        total += 1

    if args.verbose and skipped:
        print(f"⚠️  Skipped {len(skipped)} files without schema_id/schema_version:")
        for path in skipped[:10]:  # Limit output
            print(f"   - {path}")
        if len(skipped) > 10:
            print(f"   ... and {len(skipped) - 10} more")
        print()

    if bad:
        print("❌ Schema validation failed:")
        for path, msg in bad:
            print(f" - {path}: {msg}")
        sys.exit(1)
    else:
        print(f"✅ Schema validation passed ({total} artifacts validated, {len(skipped)} skipped).")
        sys.exit(0)

if __name__ == "__main__":
    main()
