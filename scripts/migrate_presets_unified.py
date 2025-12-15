#!/usr/bin/env python3
"""
Preset Migration Script - Consolidate Legacy Preset Systems

Migrates presets from 3 separate systems into unified schema:
1. data/presets/presets.json (CNC production presets with 'lane' field)
2. data/pipeline_presets.json (CAM pipeline presets)
3. data/art_presets.json (Art Studio presets)

Output: data/presets.json (unified format with 'kind' field)

Usage:
    python scripts/migrate_presets_unified.py [--dry-run] [--backup]

Options:
    --dry-run: Show what would be migrated without writing
    --backup: Create backup files before migration
"""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
LEGACY_CNC_PATH = BASE_DIR / "services" / "api" / "data" / "presets" / "presets.json"
LEGACY_PIPELINE_PATH = BASE_DIR / "services" / "api" / "app" / "data" / "pipeline_presets.json"
LEGACY_ART_PATH = BASE_DIR / "services" / "api" / "data" / "art_presets.json"
UNIFIED_PATH = BASE_DIR / "services" / "api" / "data" / "presets.json"


def load_json(path: Path) -> List[Dict[str, Any]]:
    """Load JSON file, return empty list if missing/invalid."""
    if not path.exists():
        print(f"  ⚠️  File not found: {path}")
        return []
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        print(f"  ⚠️  Not a list: {path}")
        return []
    except Exception as e:
        print(f"  ❌ Error reading {path}: {e}")
        return []


def migrate_cnc_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate CNC production preset (lane-based) to unified format.
    
    Changes:
    - 'lane' → 'kind' = 'cam'
    - 'params' → 'cam_params'
    - Add missing fields with defaults
    """
    migrated = preset.copy()
    
    # lane → kind
    if "lane" in migrated:
        migrated["kind"] = "cam"  # All CNC lanes are CAM operations
        migrated.pop("lane", None)
    else:
        migrated["kind"] = "cam"
    
    # params → cam_params
    if "params" in migrated:
        migrated["cam_params"] = migrated.pop("params")
    
    # Ensure required fields exist
    migrated.setdefault("tags", [])
    migrated.setdefault("description", "")
    migrated.setdefault("export_params", {})
    migrated.setdefault("neck_params", {})
    migrated.setdefault("source", "manual")
    
    return migrated


def migrate_pipeline_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate pipeline preset to unified format.
    
    Changes:
    - Set kind = 'cam' (pipeline presets are CAM recipes)
    - Move 'spec' → 'cam_params' if present
    """
    migrated = preset.copy()
    migrated["kind"] = "cam"
    
    # Move spec to cam_params if present
    if "spec" in migrated and migrated["spec"]:
        migrated["cam_params"] = migrated.pop("spec")
    
    # Ensure required fields
    migrated.setdefault("tags", [])
    migrated.setdefault("description", migrated.get("description", ""))
    migrated.setdefault("export_params", {})
    migrated.setdefault("neck_params", {})
    migrated.setdefault("job_source_id", None)
    migrated.setdefault("source", "manual")
    
    return migrated


def migrate_art_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate Art Studio preset to unified format.
    
    Changes:
    - 'lane' (rosette/adaptive/relief) → 'kind' = 'cam'
    - 'params' → 'cam_params'
    """
    migrated = preset.copy()
    
    # Art Studio lanes are CAM operations
    migrated["kind"] = "cam"
    migrated.pop("lane", None)
    
    # params → cam_params
    if "params" in migrated:
        migrated["cam_params"] = migrated.pop("params")
    
    # Ensure required fields
    migrated.setdefault("tags", [])
    migrated.setdefault("description", "")
    migrated.setdefault("export_params", {})
    migrated.setdefault("neck_params", {})
    migrated.setdefault("machine_id", None)
    migrated.setdefault("post_id", None)
    migrated.setdefault("job_source_id", None)
    migrated.setdefault("source", "manual")
    
    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate legacy presets to unified schema")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--backup", action="store_true", help="Create backup files")
    args = parser.parse_args()
    
    print("=== Unified Preset Migration ===\n")
    
    # Load legacy presets
    print("📂 Loading legacy presets...")
    cnc_presets = load_json(LEGACY_CNC_PATH)
    pipeline_presets = load_json(LEGACY_PIPELINE_PATH)
    art_presets = load_json(LEGACY_ART_PATH)
    
    print(f"  CNC Production: {len(cnc_presets)} presets")
    print(f"  CAM Pipeline: {len(pipeline_presets)} presets")
    print(f"  Art Studio: {len(art_presets)} presets")
    print()
    
    # Migrate each type
    print("🔄 Migrating presets...")
    unified = []
    
    for preset in cnc_presets:
        migrated = migrate_cnc_preset(preset)
        unified.append(migrated)
        print(f"  ✓ CNC: {preset.get('name', 'Unnamed')}")
    
    for preset in pipeline_presets:
        migrated = migrate_pipeline_preset(preset)
        unified.append(migrated)
        print(f"  ✓ Pipeline: {preset.get('name', 'Unnamed')}")
    
    for preset in art_presets:
        migrated = migrate_art_preset(preset)
        unified.append(migrated)
        print(f"  ✓ Art Studio: {preset.get('name', 'Unnamed')}")
    
    print(f"\n📊 Total unified presets: {len(unified)}\n")
    
    # Dry run - show sample
    if args.dry_run:
        print("🔍 DRY RUN - Sample migrated preset:\n")
        if unified:
            print(json.dumps(unified[0], indent=2))
        print("\n⚠️  No files modified (dry run mode)")
        return
    
    # Backup if requested
    if args.backup:
        print("💾 Creating backups...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for path in [LEGACY_CNC_PATH, LEGACY_PIPELINE_PATH, LEGACY_ART_PATH]:
            if path.exists():
                backup_path = path.with_suffix(f".backup_{timestamp}.json")
                shutil.copy2(path, backup_path)
                print(f"  ✓ {path.name} → {backup_path.name}")
        print()
    
    # Write unified presets
    print("💾 Writing unified presets...")
    UNIFIED_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNIFIED_PATH.write_text(
        json.dumps(unified, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  ✓ Wrote {len(unified)} presets to {UNIFIED_PATH}\n")
    
    print("✅ Migration complete!")
    print("\nNext steps:")
    print("  1. Test unified API at /api/presets")
    print("  2. Verify preset filtering (?kind=cam, ?tag=roughing)")
    print("  3. Archive legacy preset files once verified")


if __name__ == "__main__":
    main()
