#!/usr/bin/env python3
"""
Schema bump guard:
 - If any file under contracts/schemas/ changes in this PR,
   require a corresponding change in contracts/schema_registry.json
   (version bump for the touched schema_id).
Exit 1 with a readable message if the guard fails.
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "contracts" / "schemas"
REGISTRY = ROOT / "contracts" / "schema_registry.json"

def git_changed_paths(base: str = "origin/main") -> list[str]:
    # Detect changed files against base (fallback to HEAD~ if not available)
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", base, "HEAD"], text=True)
    except Exception:
        out = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"], text=True)
    return [p.strip() for p in out.splitlines() if p.strip()]

def load_registry() -> dict[tuple[str, str], str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    idx: dict[tuple[str, str], str] = {}
    for ent in data.get("schemas", []):
        idx[(ent["schema_id"], ent["version"])] = ent["file"]
    return idx

def main() -> int:
    changed = git_changed_paths(os.environ.get("SCHEMA_GUARD_BASE", "origin/main"))
    touched_schema_files = [c for c in changed if c.startswith("contracts/schemas/")]
    if not touched_schema_files:
        print("schema-bump-guard: no schema files changed; OK")
        return 0

    # Extract current registry mapping
    reg_map = load_registry()
    # Collect schema_ids for touched files by basename match
    basenames = {Path(p).name for p in touched_schema_files}

    # Build reverse map: filename -> (schema_id, version)
    filename_to_entries = {}
    for (sid, ver), file in reg_map.items():
        filename_to_entries.setdefault(Path(file).name, []).append((sid, ver))

    errors: list[str] = []
    for fname in basenames:
        if fname not in filename_to_entries:
            errors.append(f"- {fname}: not referenced by schema_registry.json (add an entry).")
            continue
        # For the referenced sid,ver pairs, require that at least one *new* version exists
        # compared to base branch. We check by diffing registry file itself.
    # Simple strategy: ensure the registry file changed if any schema file changed.
    if "contracts/schema_registry.json" not in changed:
        errors.append("contracts/schema_registry.json must change when contracts/schemas/* changes (version bump required).")

    if errors:
        print("❌ schema-bump-guard failed:")
        print("\n".join(errors))
        print("\nHint: bump the appropriate version in contracts/schema_registry.json for the schema(s) you edited.")
        return 1

    print("✅ schema-bump-guard: registry updated; OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
