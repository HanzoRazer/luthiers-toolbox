# Strategy Package Inspection

## Overview

The strategy package inspection CLI provides human-readable summaries of assembled CAM Assist packages.

This is a **read-only** inspection tool. It does not mutate, regenerate, repair, or normalize package contents.

## Usage

### Basic Inspection

```bash
python scripts/inspect_strategy_package.py examples/packages/fret_slot_strategy_example/
```

### JSON Output

```bash
python scripts/inspect_strategy_package.py <package_dir> --json
```

### Quiet Mode

```bash
python scripts/inspect_strategy_package.py <package_dir> --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `package_dir` | Path to the strategy package directory (required) |
| `--json` | Output machine-readable JSON |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Inspection successful |
| 1 | Validation failure |
| 2 | File/read error |

## Example Output

```
CAM Assist Strategy Package Inspection
=======================================

Package Type:
  cam_assist_strategy_package

Operation Type:
  fret_slot_strategy

Manifest Version:
  1.0.0

Authority Status:
  NON-EXECUTION PACKAGE
  Human review required
  Execution authority denied

Files:
  [OK] strategy
  [OK] review_packet
  [OK] manifest

Provenance:
  created_by: cam-assist-assembly
  source_spec_id: fret-slots-25500-22f-sample
  created_at: 2026-05-21T20:43:00Z

Warnings:
  none

---------------------------------------
This package is advisory only.
No machine execution authority is present.
Human review is required before downstream CAM use.
```

## JSON Output Format

```json
{
  "valid": true,
  "package_type": "cam_assist_strategy_package",
  "operation_type": "fret_slot_strategy",
  "manifest_version": "1.0.0",
  "authority": {
    "non_execution_declaration": true,
    "execution_authority_claim": false,
    "requires_human_review": true
  },
  "files": {
    "strategy": "present",
    "review_packet": "present",
    "manifest": "present"
  },
  "provenance": {
    "created_by": "cam-assist-assembly",
    "source_spec_id": "...",
    "created_at": "..."
  },
  "warnings": []
}
```

## Validation Rules

### Must Fail If

- `manifest.json` is missing
- Manifest is invalid JSON
- Strategy file referenced in manifest is missing
- Review packet file referenced in manifest is missing
- `execution_authority_claim` is `true`
- `non_execution_declaration` is not `true`
- `requires_human_review` is not `true`

### Should Warn If

- `source_geometry_files` is empty
- `provenance.derivation_notes` is empty
- Review packet is unusually small (< 1 KB)
- Manifest version is not `"1.0.0"`

## Integration

The inspector works with packages assembled by CAM-A5:

```bash
# Assemble a package
python scripts/assemble_strategy_package.py examples/valid/fret_slot_strategy.json

# Inspect the assembled package
python scripts/inspect_strategy_package.py ./fret_slot_strategy_package/
```

## What This Is Not

The inspection CLI does **not**:

- Mutate package contents
- Regenerate missing files
- Repair invalid manifests
- Normalize data formats
- Generate G-code
- Authorize machine execution

It is a **read-only inspection tool** for human review workflows.

## See Also

- [STRATEGY_PACKAGE_MANIFEST.md](STRATEGY_PACKAGE_MANIFEST.md) — Manifest format
- [STRATEGY_PACKAGE_ASSEMBLY.md](STRATEGY_PACKAGE_ASSEMBLY.md) — Package assembly CLI
- [STRATEGY_PACKAGE_INDEX.md](STRATEGY_PACKAGE_INDEX.md) — Package index generator
- [STRATEGY_PACKAGE_ARCHIVE.md](STRATEGY_PACKAGE_ARCHIVE.md) — Package archive CLI
