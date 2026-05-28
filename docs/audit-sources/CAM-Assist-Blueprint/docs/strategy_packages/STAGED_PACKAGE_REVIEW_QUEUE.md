# Staged Package Review Queue

## Overview

The staged package review queue CLI scans staged package directories and generates a review queue index for human operators.

This is **non-execution infrastructure**. It does not generate G-code, produce machine output, approve packages, or mutate staged content.

## Usage

### Basic Usage

```bash
python scripts/index_staged_packages.py staged_packages/
```

Output: `staged_packages/REVIEW_QUEUE.md`

### Custom Output Path

```bash
python scripts/index_staged_packages.py staged_packages/ --out /tmp/review_queue.md
```

### JSON Output

```bash
python scripts/index_staged_packages.py staged_packages/ --json-out /tmp/review_queue.json
```

### Quiet Mode

```bash
python scripts/index_staged_packages.py staged_packages/ --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `staged_root` | Path to the staged packages root directory (required) |
| `--out <path>` | Output path for Markdown queue (default: `<staged_root>/REVIEW_QUEUE.md`) |
| `--json-out <path>` | Optional output path for JSON queue |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Review queue generated |
| 1 | No packages found |
| 2 | File/read/write error |

Invalid packages do **not** fail the command if at least one package is discovered.

## Queue Output Format

### Markdown

```markdown
# CAM Assist Staged Package Review Queue

Generated at: <timestamp>

## Summary
- Total staged packages: 3
- Valid packages: 2
- Invalid packages: 1
- Packages requiring human review: 3
- Warning count: 4

## Packages
| Package | Operation | Status | Human Review Required | Warnings |
|---------|-----------|--------|----------------------|----------|
| fret_slot_strategy_package | fret_slot_strategy | valid | Yes | 1 |
| invalid_package | unknown | invalid | No [INVALID] | 0 |

## Non-Execution Notice
This review queue is advisory only.
It does not approve, authorize, execute, or modify packages.
```

### JSON

```json
{
  "generated_at": "2026-05-23T12:00:00Z",
  "summary": {
    "total": 3,
    "valid": 2,
    "invalid": 1,
    "requires_human_review": 3,
    "warnings": 4
  },
  "packages": [
    {
      "path": "fret_slot_strategy_package",
      "operation_type": "fret_slot_strategy",
      "status": "valid",
      "requires_human_review": true,
      "warnings": []
    }
  ]
}
```

## Validation Rules

The indexer:

- Recursively finds staged package directories containing `manifest.json`
- Inspects each package using CAM-A6 logic
- Includes valid and invalid packages in queue
- Continues after invalid packages
- Writes only collection-level queue output
- Never edits staged package contents

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

# Generate review queue
python scripts/index_staged_packages.py /tmp/cam_assist_staged --json-out /tmp/cam_assist_staged/review_queue.json

# Run tests
pytest
```

## What This Is Not

The review queue CLI does **not**:

- Generate G-code
- Authorize machine execution
- Approve or reject packages
- Execute staged content
- Modify staged packages
- Bypass human review

It generates a **review queue** for human operators.

## See Also

- [REVIEW_DECISION_RECORD.md](REVIEW_DECISION_RECORD.md) — Review decision recorder
- [STRATEGY_PACKAGE_IMPORT_STAGING.md](STRATEGY_PACKAGE_IMPORT_STAGING.md) — Import staging CLI
- [STRATEGY_PACKAGE_IMPORT_VALIDATION.md](STRATEGY_PACKAGE_IMPORT_VALIDATION.md) — Archive validation CLI
- [STRATEGY_PACKAGE_INDEX.md](STRATEGY_PACKAGE_INDEX.md) — Package index generator
