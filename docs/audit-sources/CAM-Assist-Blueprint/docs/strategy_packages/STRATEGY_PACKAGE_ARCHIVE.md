# Strategy Package Archive

## Overview

The strategy package archive CLI creates portable `.zip` files from validated strategy packages.

This is **non-execution infrastructure**. It does not generate G-code, produce machine output, or mutate package contents.

## Usage

### Basic Usage

```bash
python scripts/archive_strategy_package.py examples/packages/fret_slot_strategy_example/
```

Output: `examples/packages/fret_slot_strategy_example.zip`

### Custom Output Path

```bash
python scripts/archive_strategy_package.py <package_dir> --out /tmp/archive.zip
```

### Overwrite Existing Archive

```bash
python scripts/archive_strategy_package.py <package_dir> --out /tmp/archive.zip --force
```

### Quiet Mode

```bash
python scripts/archive_strategy_package.py <package_dir> --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `package_dir` | Path to the strategy package directory (required) |
| `--out <path>` | Output path for the archive |
| `--force` | Overwrite existing archive |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Archive created |
| 1 | Validation failure |
| 2 | File/read/write/archive error |

## Archive Contents

Archives contain all files from the package directory with package-relative paths:

```
strategy.json
review_packet.md
manifest.json
geometry.dxf        # if present
README.md           # if present
notes/              # if present
  note.txt
```

Paths are **flat** (not nested in a folder):

```
# Correct:
strategy.json

# Not:
fret_slot_strategy_example/strategy.json
```

## Validation Rules

### Must Fail If

- Package directory missing
- `manifest.json` missing
- Manifest invalid
- `strategy.json` missing
- `review_packet.md` missing
- `execution_authority_claim` is `true`
- `non_execution_declaration` is not `true`
- `requires_human_review` is not `true`
- Archive exists and `--force` not provided

### Warns But Allows

- `source_geometry_files` empty
- `review_packet.md` < 1024 bytes
- `manifest_version` != "1.0.0"

## Integration

The archiver uses A6 inspection logic for validation:

```bash
# Full workflow
python scripts/assemble_strategy_package.py strategy.json --out ./my_package
python scripts/inspect_strategy_package.py ./my_package
python scripts/archive_strategy_package.py ./my_package

# Validate archive before import
python scripts/validate_package_archive.py my_package.zip

# Verify archive contents manually
python -m zipfile -l my_package.zip
```

## Package Integrity

The archiver:

- Does **not** mutate package contents
- Does **not** repair invalid packages
- Does **not** normalize data formats
- Only reads and archives existing files

## What This Is Not

The archive CLI does **not**:

- Generate G-code
- Authorize machine execution
- Create toolpaths
- Modify package contents

It creates **portable archives** for sharing, attachment, and storage.

## See Also

- [STRATEGY_PACKAGE_IMPORT_VALIDATION.md](STRATEGY_PACKAGE_IMPORT_VALIDATION.md) — Archive import validator
- [STRATEGY_PACKAGE_INSPECTION.md](STRATEGY_PACKAGE_INSPECTION.md) — Package inspection CLI
- [STRATEGY_PACKAGE_INDEX.md](STRATEGY_PACKAGE_INDEX.md) — Package index generator
- [STRATEGY_PACKAGE_ASSEMBLY.md](STRATEGY_PACKAGE_ASSEMBLY.md) — Package assembly CLI
