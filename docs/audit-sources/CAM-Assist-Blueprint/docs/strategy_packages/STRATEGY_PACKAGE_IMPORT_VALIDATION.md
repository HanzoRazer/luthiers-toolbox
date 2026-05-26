# Strategy Package Import Validation

## Overview

The strategy package archive validator CLI validates `.zip` archives before import or review.

This is **non-execution infrastructure**. It does not generate G-code, produce machine output, execute archive contents, or modify the archive.

## Usage

### Basic Usage

```bash
python scripts/validate_package_archive.py package.zip
```

Success output:

```
PASS: archive is a valid CAM Assist strategy package
```

Failure output:

```
FAIL: archive validation failed
```

### JSON Output

```bash
python scripts/validate_package_archive.py package.zip --json
```

### Quiet Mode

```bash
python scripts/validate_package_archive.py package.zip --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `archive` | Path to the .zip archive to validate (required) |
| `--json` | Output machine-readable JSON |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Archive is valid |
| 1 | Validation failure |
| 2 | File/read/archive error |

## Validation Rules

### Must Fail If

- Archive missing or unreadable
- Not a valid zip file
- Archive contains absolute paths
- Archive contains path traversal entries (`../`)
- Archive missing `manifest.json`
- Archive missing `strategy.json`
- Archive missing `review_packet.md`
- Manifest invalid
- `execution_authority_claim` is `true`
- `non_execution_declaration` is not `true`
- `requires_human_review` is not `true`

### Warns But Allows

- Archive contains unexpected files (not in manifest or core set)
- Suspicious executable files (`.py`, `.exe`, `.sh`, `.bat`, `.cmd`, `.ps1`) — HIGH severity warning
- `review_packet.md` < 1024 bytes
- `manifest_version` != "1.0.0"
- `source_geometry_files` empty

## Security Rules

The validator:

- Never extracts directly into the repository
- Uses a temporary directory for extraction
- Rejects path traversal before extraction
- Rejects absolute paths before extraction
- Does not execute any file
- Does not import Python modules from archive
- Does not repair archive contents
- Deletes temp files after validation

## JSON Output Format

```json
{
  "archive_valid": true,
  "package_valid": true,
  "archive_path": "/path/to/package.zip",
  "archive_errors": [],
  "archive_warnings": [],
  "package": {
    "package_type": "cam_assist_strategy_package",
    "operation_type": "fret_slot_strategy",
    "manifest_version": "1.0.0",
    "authority": {
      "non_execution_declaration": true,
      "execution_authority_claim": false,
      "requires_human_review": true
    },
    "files": {
      "manifest": "present",
      "strategy": "present",
      "review_packet": "present"
    },
    "provenance": {
      "source_spec_id": "...",
      "created_by": "...",
      "derivation_notes": "..."
    }
  },
  "package_warnings": []
}
```

## Integration

Full workflow:

```bash
# Assemble
python scripts/assemble_strategy_package.py examples/valid/fret_slot_strategy.json --out /tmp/fret_slot_strategy_package --force

# Archive
python scripts/archive_strategy_package.py /tmp/fret_slot_strategy_package --out /tmp/fret_slot_strategy_package.zip --force

# Validate
python scripts/validate_package_archive.py /tmp/fret_slot_strategy_package.zip

# Run tests
pytest
```

Inspect archive manually:

```bash
python -m zipfile -l /tmp/fret_slot_strategy_package.zip
```

## Core Allowed Files

These files are always allowed in archives:

- `manifest.json`
- `strategy.json`
- `review_packet.md`
- `README.md`

Additionally, any files referenced in the manifest are allowed:

- `strategy_file`
- `review_packet_file`
- `source_geometry_files[]`

All other files trigger warnings.

## What This Is Not

The archive validator does **not**:

- Generate G-code
- Authorize machine execution
- Create toolpaths
- Import or install packages
- Execute archive contents
- Repair invalid archives

It validates archives for **safe review and inspection**.

## See Also

- [STRATEGY_PACKAGE_IMPORT_STAGING.md](STRATEGY_PACKAGE_IMPORT_STAGING.md) — Import staging CLI
- [STRATEGY_PACKAGE_ARCHIVE.md](STRATEGY_PACKAGE_ARCHIVE.md) — Archive creation CLI
- [STRATEGY_PACKAGE_INSPECTION.md](STRATEGY_PACKAGE_INSPECTION.md) — Package inspection CLI
- [STRATEGY_PACKAGE_ASSEMBLY.md](STRATEGY_PACKAGE_ASSEMBLY.md) — Package assembly CLI
