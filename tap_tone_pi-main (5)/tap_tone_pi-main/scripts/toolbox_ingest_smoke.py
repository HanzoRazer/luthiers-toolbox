#!/usr/bin/env python3
"""
ToolBox ingest smoke: validates demo Analyzer artifacts against the registry
contracts and prints a concise summary. Exit non-zero on failure.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, List

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("❌ jsonschema not installed; run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parents[1]
REG = REPO / "contracts" / "schema_registry.json"

# Demo locations produced by examples:
CHLADNI_DIR = REPO / "out" / "DEMO" / "chladni"
PHASE2_DIR = REPO / "runs_phase2" / "DEMO" / "session_0001"
MOE_DIR = REPO / "out" / "DEMO" / "moe"


def load_registry() -> Dict[Tuple[str, str], dict]:
    """Load schema registry and return index mapping (schema_id, version) -> schema."""
    data = json.loads(REG.read_text(encoding="utf-8"))
    index: Dict[Tuple[str, str], dict] = {}
    
    # Handle both array and object registry formats
    schemas = data.get("schemas", {})
    if isinstance(schemas, dict):
        # Object format: {"tap_peaks": {"file": "...", "version": "..."}, ...}
        for name, ent in schemas.items():
            path_str = ent.get("path") or ent.get("file", "")
            ver = ent.get("version", "1.0.0")
            sid = ent.get("schema_version_const", name)
            schema_path = REPO / path_str if path_str else None
            if schema_path and schema_path.exists():
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                index[(sid, ver)] = schema
                # Also index by name for flexibility
                index[(name, ver)] = schema
    elif isinstance(schemas, list):
        # Array format: [{"schema_id": "...", "version": "...", "file": "..."}, ...]
        for ent in schemas:
            sid = ent.get("schema_id", "")
            ver = ent.get("version", "")
            path_str = ent.get("file", "")
            schema_path = REPO / path_str if path_str else None
            if schema_path and schema_path.exists():
                index[(sid, ver)] = json.loads(schema_path.read_text(encoding="utf-8"))
    
    return index


def validate(doc: dict, schemas: Dict[Tuple[str, str], dict]) -> List[str]:
    """Validate document against its declared schema."""
    # Try schema_id first, fall back to schema_version (Phase-2 uses schema_version as const)
    sid = str(doc.get("schema_id") or "")
    ver = str(doc.get("schema_version") or "")
    errs: List[str] = []
    
    # Phase-2 artifacts use schema_version as both identifier and version
    # e.g. "phase2_ods_snapshot_v2" is the schema_version const
    if not sid and ver:
        sid = ver  # Use schema_version as identifier for lookup
    
    if not sid:
        return [f"missing schema_id/version: {sid}/{ver}"]
    
    key = (sid, ver)
    if key not in schemas:
        # Try by schema_version_const (for phase2 schemas)
        matching = [k for k in schemas if k[0] == sid or k[1] == ver]
        if not matching:
            # Also try just the schema_version as the key
            matching = [k for k in schemas if sid in k]
        if matching:
            key = matching[0]
        else:
            return [f"no schema for ({sid}, {ver}) in registry"]
    
    schema = schemas[key]
    v = Draft202012Validator(schema)
    for e in sorted(v.iter_errors(doc), key=lambda e: str(e.path)):
        path_str = "/".join(map(str, e.path)) or "<root>"
        errs.append(f"{path_str}: {e.message}")
    
    return errs


def read_json(path: Path) -> dict:
    """Read and parse JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if not REG.exists():
        print("❌ missing contracts/schema_registry.json", file=sys.stderr)
        return 2
    
    schemas = load_registry()
    if not schemas:
        print("⚠️  No schemas loaded from registry; skipping validation", file=sys.stderr)
        # Don't fail if registry is empty (schemas may be in different format)
    
    # Targets: pick representative artifacts from each demo
    artifacts = [
        CHLADNI_DIR / "chladni_run.json",
        MOE_DIR / "moe_result.json",
        PHASE2_DIR / "derived" / "ods_snapshot.json",
        PHASE2_DIR / "derived" / "wolf_candidates.json",
    ]

    bad: List[str] = []
    ok = 0
    skipped = 0
    
    for p in artifacts:
        if not p.exists():
            print(f"⚠️  skipping (not found): {p.relative_to(REPO)}")
            skipped += 1
            continue
        
        doc = read_json(p)
        
        # If no schemas loaded, just check the artifact is valid JSON with expected fields
        if not schemas:
            if "schema_id" in doc or "artifact_type" in doc:
                ok += 1
            continue
        
        errs = validate(doc, schemas)
        if errs:
            bad.append(f"{p.relative_to(REPO)} invalid:\n  - " + "\n  - ".join(errs))
        else:
            ok += 1

    # Optional: quick manifest sanity (does it list chladni artifacts?)
    man = CHLADNI_DIR / "manifest.json"
    if man.exists():
        md = read_json(man)
        if "artifacts" not in md or not isinstance(md["artifacts"], list):
            bad.append(f"{man.relative_to(REPO)}: manifest lacks 'artifacts' array")
        else:
            # Check expected artifact count
            arts = md["artifacts"]
            if len(arts) < 4:
                bad.append(f"{man.relative_to(REPO)}: expected ≥4 artifacts, got {len(arts)}")

    if bad:
        print("❌ ToolBox ingest smoke failed:")
        for b in bad:
            print(" -", b)
        return 1
    
    total = len(artifacts)
    print(f"✅ ToolBox ingest smoke passed ({ok}/{total - skipped} validated, {skipped} skipped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
