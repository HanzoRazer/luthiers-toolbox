# Strategy Package Import Staging

## Overview

The strategy package import staging CLI validates a `.zip` archive and stages it into a local review directory.

This is **non-execution infrastructure**. It does not generate G-code, produce machine output, execute archive contents, or modify package files.

## Usage

### Basic Usage

```bash
python scripts/stage_strategy_package.py package.zip
```

Default output: `./staged_packages/<archive_stem>/`

### Custom Output Root

```bash
python scripts/stage_strategy_package.py package.zip --out ./custom_staging/
```

Output: `./custom_staging/<archive_stem>/`

### Overwrite Existing

```bash
python scripts/stage_strategy_package.py package.zip --out ./staging/ --force
```

### Quiet Mode

```bash
python scripts/stage_strategy_package.py package.zip --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `archive` | Path to the .zip archive to stage (required) |
| `--out <path>` | Output root directory for staged packages (default: `./staged_packages/`) |
| `--force` | Overwrite existing staged directory |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Package staged |
| 1 | Validation failure |
| 2 | File/read/write/extract error |

## Staged Directory Contents

Staged packages preserve archive-relative paths:

```
staged_packages/fret_slot_strategy_example/
  strategy.json
  review_packet.md
  manifest.json
  geometry/           # if present
    fret.dxf
  notes/              # if present
    note.txt
  attachments/        # if present
    photo.png
```

Subdirectories are **preserved**, not flattened.

## Validation Rules

### Must Fail If

- Archive validation fails (CAM-A9)
- Archive contains unsafe paths (traversal, absolute)
- Manifest invalid
- Strategy missing
- Review packet missing
- `execution_authority_claim` is `true`
- `non_execution_declaration` is not `true`
- `requires_human_review` is not `true`
- Output directory exists and `--force` not provided

### Warns But Allows

- Archive contains unexpected files
- Suspicious executable files (HIGH severity)
- `review_packet.md` < 1024 bytes
- `manifest_version` != "1.0.0"
- `source_geometry_files` empty

## Security Rules

The staging command:

- Validates archive before staging (CAM-A9)
- Rejects path traversal
- Rejects absolute paths
- Extracts only into controlled output directory
- Does not execute archive contents
- Does not import modules from archive
- Does not repair package contents
- Does not modify package files after extraction

## Integration

Full workflow:

```bash
# Assemble
python scripts/assemble_strategy_package.py examples/valid/fret_slot_strategy.json --out /tmp/fret_slot_strategy_package --force

# Archive
python scripts/archive_strategy_package.py /tmp/fret_slot_strategy_package --out /tmp/fret_slot_strategy_package.zip --force

# Validate
python scripts/validate_package_archive.py /tmp/fret_slot_strategy_package.zip

# Stage
python scripts/stage_strategy_package.py /tmp/fret_slot_strategy_package.zip --out /tmp/cam_assist_staged --force

# Run tests
pytest
```

Inspect staged package:

```bash
# Windows
dir /s /tmp/cam_assist_staged

# Unix
find /tmp/cam_assist_staged -maxdepth 3 -type f
```

## What This Is Not

The staging CLI does **not**:

- Generate G-code
- Authorize machine execution
- Create toolpaths
- Execute archive contents
- Repair invalid packages
- Automatically approve strategies

It stages validated archives for **human review**.

## See Also

- [STAGED_PACKAGE_REVIEW_QUEUE.md](STAGED_PACKAGE_REVIEW_QUEUE.md) — Review queue generator
- [STRATEGY_PACKAGE_IMPORT_VALIDATION.md](STRATEGY_PACKAGE_IMPORT_VALIDATION.md) — Archive validation CLI
- [STRATEGY_PACKAGE_ARCHIVE.md](STRATEGY_PACKAGE_ARCHIVE.md) — Archive creation CLI
- [STRATEGY_PACKAGE_INSPECTION.md](STRATEGY_PACKAGE_INSPECTION.md) — Package inspection CLI
