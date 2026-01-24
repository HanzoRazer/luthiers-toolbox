#!/usr/bin/env python3
"""
ToolBox ingest smoke: validate Analyzer demo artifacts against Analyzer contracts.
No Analyzer code is imported; we only read JSON and validate via jsonschema.

Usage:
  python scripts/analyzer_ingest_smoke.py \
      --contracts-root analyzer/contracts \
      --chladni-dir analyzer/out/DEMO/chladni \
      --phase2-dir  analyzer/runs_phase2/DEMO/session_0001 \
      --moe-dir     analyzer/out/DEMO/moe
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Dict, Tuple, List
from jsonschema import Draft202012Validator

def load_registry(contracts_root: Path) -> Dict[Tuple[str, str], dict]:
    reg_path = contracts_root / "schema_registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"Missing registry: {reg_path}")
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    index: Dict[Tuple[str, str], dict] = {}
    schemas = data.get("schemas", {})
    # Handle both dict format (keyed by schema_id) and list format
    if isinstance(schemas, dict):
        items = [(k, v) for k, v in schemas.items()]
    else:
        items = [(ent["schema_id"], ent) for ent in schemas]
    for sid, ent in items:
        ver = ent["version"]
        fp = ent.get("path") or ent["file"]
        schema_path = contracts_root.parent / fp if not Path(fp).is_absolute() else Path(fp)
        if not schema_path.exists():
            schema_path = contracts_root / "schemas" / Path(fp).name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {fp}")
        schema_content = json.loads(schema_path.read_text(encoding="utf-8"))
        index[(sid, ver)] = schema_content
        # Also key by schema_version_const if present
        if "schema_version_const" in ent:
            index[(sid, ent["schema_version_const"])] = schema_content
    return index

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

# Aliases for schema_id inference from schema_version
_SCHEMA_ALIASES = {
    "measurement_manifest": "manifest",
}

def _infer_schema_id(schema_version: str) -> str:
    """Infer schema_id from schema_version const like 'phase2_session_meta_v1'."""
    # Strip trailing version: phase2_session_meta_v1 -> phase2_session_meta
    if "_v" in schema_version:
        return schema_version.rsplit("_v", 1)[0]
    return ""

def validate_doc(doc: dict, reg: Dict[Tuple[str, str], dict]) -> List[str]:
    sid = str(doc.get("schema_id") or "")
    ver = str(doc.get("schema_version") or "")
    errs: List[str] = []
    # If no schema_id, try to infer from schema_version
    if not sid and ver:
        sid = _infer_schema_id(ver)
    # Apply aliases
    sid = _SCHEMA_ALIASES.get(sid, sid)
    if not sid or not ver:
        return [f"missing schema_id/version: {sid}/{ver}"]
    key = (sid, ver)
    if key not in reg:
        return [f"no schema for ({sid}, {ver}) in registry"]
    v = Draft202012Validator(reg[key])
    for e in sorted(v.iter_errors(doc), key=lambda e: e.path):
        path = "/".join(map(str, e.path)) or "<root>"
        errs.append(f"{path}: {e.message}")
    return errs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contracts-root", required=True)
    ap.add_argument("--chladni-dir", required=True)
    ap.add_argument("--phase2-dir", required=True)
    ap.add_argument("--moe-dir", required=True)
    args = ap.parse_args()

    contracts_root = Path(args.contracts_root)
    chladni_dir   = Path(args.chladni_dir)
    phase2_dir    = Path(args.phase2_dir)
    moe_dir       = Path(args.moe_dir)

    reg = load_registry(contracts_root)

    targets = [
        chladni_dir / "chladni_run.json",
        phase2_dir  / "ods_snapshot.json",
        phase2_dir  / "wolf_candidates.json",
        moe_dir     / "moe_result.json",
    ]

    bad, ok = [], 0
    for p in targets:
        if not p.exists():
            bad.append(f"missing artifact: {p}")
            continue
        doc = read_json(p)
        errs = validate_doc(doc, reg)
        if errs:
            bad.append(f"{p} invalid:\n  - " + "\n  - ".join(errs))
        else:
            ok += 1

    if bad:
        print("❌ ToolBox ingest smoke failed:")
        for b in bad: print(" -", b)
        return 1

    man = chladni_dir / "manifest.json"
    if not man.exists():
        print("⚠️  Chladni manifest.json not found (optional but recommended).")

    print(f"✅ ToolBox ingest smoke passed ({ok}/{len(targets)} validated).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
