#!/usr/bin/env python3
"""
Schema validation script for Mesh Pipeline artifacts.

Validates qa_core.json and cam_policy.json outputs against contract schemas.
Supports both the new schema_registry.json and direct schema loading.

Usage:
    python scripts/validate_schemas.py --out-root examples/retopo
    python scripts/validate_schemas.py --out-root examples/retopo --registry contracts/schema_registry.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def load_registry(reg_path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Load schema registry and return a dict keyed by (schema_id, version)."""
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    for entry in data.get("schemas", []):
        schema_id = entry["schema_id"]
        version = entry["version"]
        schema_file = reg_path.parent / entry["file"]
        
        if schema_file.exists():
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            by_key[(schema_id, version)] = schema
        else:
            print(f"[warn] Schema file not found: {schema_file}")
    
    return by_key


def load_direct_schemas(contracts_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load schemas directly from contracts directory (fallback mode)."""
    schemas: Dict[str, Dict[str, Any]] = {}
    
    # Map artifact keys to schema files
    mappings = {
        "qa_core": "qa_core.schema.json",
        "cam_policy": "cam_policy.schema.json",
    }
    
    for key, filename in mappings.items():
        schema_path = contracts_dir / filename
        if schema_path.exists():
            schemas[key] = json.loads(schema_path.read_text(encoding="utf-8"))
    
    return schemas


def validate_artifact(
    doc: Dict[str, Any],
    schema: Dict[str, Any],
    path: Path
) -> int:
    """Validate a document against a schema.
    
    Returns:
        Number of errors found
    """
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    
    if errors:
        print(f"[FAIL] {path}:")
        for err in errors:
            json_path = "/".join(str(p) for p in err.path) or "<root>"
            print(f"  - {json_path}: {err.message}")
        return len(errors)
    
    return 0


def validate_dir(out_root: Path, registry: Dict[Tuple[str, str], Dict[str, Any]]) -> int:
    """Validate all JSON artifacts in directory tree.
    
    Returns:
        Number of files with errors
    """
    n_bad = 0
    n_validated = 0
    
    for p in out_root.rglob("*.json"):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[FAIL] {p}: Invalid JSON - {e}")
            n_bad += 1
            continue
        
        # Try to determine schema from document structure
        schema_key = None
        
        # Check for version-based documents (new schema format)
        if "version" in doc:
            version = doc["version"]
            if "mesh_healing" in doc:
                schema_key = ("qa_core", "1.0")
            elif "regions" in doc and "global_defaults" in doc:
                schema_key = ("cam_policy", "1.0")
        
        # Check for schema_id-based documents (patch format)
        elif "schema_id" in doc and "schema_version" in doc:
            schema_key = (doc["schema_id"], doc["schema_version"])
        
        if not schema_key:
            # Skip files that aren't recognized artifacts
            continue
        
        schema = registry.get(schema_key)
        if not schema:
            print(f"[warn] No schema for {schema_key} (path={p})")
            continue
        
        n_validated += 1
        if validate_artifact(doc, schema, p) > 0:
            n_bad += 1
    
    print(f"\nValidated {n_validated} artifacts, {n_bad} with errors")
    return n_bad


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Validate Mesh Pipeline artifacts against contract schemas"
    )
    ap.add_argument(
        "--out-root",
        default="examples/retopo",
        help="Root directory containing artifacts to validate"
    )
    ap.add_argument(
        "--registry",
        default="contracts/schema_registry.json",
        help="Path to schema registry JSON"
    )
    ap.add_argument(
        "--contracts-dir",
        default="contracts",
        help="Path to contracts directory (fallback if registry not found)"
    )
    args = ap.parse_args()
    
    # Try to load from registry first, fall back to direct loading
    registry_path = Path(args.registry)
    if registry_path.exists():
        registry = load_registry(registry_path)
        print(f"Loaded {len(registry)} schemas from registry")
    else:
        print(f"[warn] Registry not found at {registry_path}, using direct loading")
        contracts_dir = Path(args.contracts_dir)
        direct_schemas = load_direct_schemas(contracts_dir)
        # Convert to registry format
        registry = {(k, "1.0"): v for k, v in direct_schemas.items()}
        print(f"Loaded {len(registry)} schemas directly")
    
    out_root = Path(args.out_root)
    if not out_root.exists():
        print(f"[ERROR] Output directory not found: {out_root}")
        sys.exit(1)
    
    n_bad = validate_dir(out_root, registry)
    
    if n_bad:
        print(f"\n[FAIL] {n_bad} file(s) failed validation")
        sys.exit(2)
    else:
        print("\n[OK] All schemas valid")


if __name__ == "__main__":
    main()
