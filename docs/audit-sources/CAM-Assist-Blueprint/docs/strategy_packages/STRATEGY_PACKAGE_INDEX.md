# Strategy Package Index

## Overview

The strategy package index generator scans directories for CAM Assist packages and produces a navigable index.

This is a **read-only** utility. It does not mutate individual package contents. It may write collection-level metadata (`INDEX.md`, `index.json`) to the input directory.

## Usage

### Basic Usage

```bash
python scripts/index_strategy_packages.py examples/packages/
```

Output: `examples/packages/INDEX.md`

### Custom Output Path

```bash
python scripts/index_strategy_packages.py examples/packages/ --out /tmp/index.md
```

### JSON Output

```bash
python scripts/index_strategy_packages.py examples/packages/ --json-out index.json
```

### Quiet Mode

```bash
python scripts/index_strategy_packages.py examples/packages/ --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `packages_dir` | Directory containing strategy packages (required) |
| `--out <path>` | Output path for Markdown index |
| `--json-out <path>` | Output path for JSON index |
| `--quiet`, `-q` | Only print summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Index generated (even if some packages invalid) |
| 1 | No packages found |
| 2 | File/read/write error |

## Package Discovery

The indexer recursively searches for `manifest.json` files under the input directory. Each directory containing a manifest is treated as a package.

Directories without `manifest.json` are silently ignored.

## Markdown Index Format

```markdown
# CAM Assist Strategy Package Index

Generated at: 2026-05-22T12:00:00Z

## Summary

- Total packages: 3
- Valid packages: 2
- Invalid packages: 1
- Total warnings: 4

## Packages

| Package | Operation | Status | Human Review | Warnings |
|---------|-----------|--------|--------------|----------|
| pkg1 | fret_slot_strategy | valid | required | none |
| pkg2 | fret_slot_strategy | valid | required | 2 |
| pkg3 | unknown | INVALID | unknown | 2 |

---

## Non-Execution Notice

These packages are advisory only.
They do not authorize machine execution.
Human review and downstream CAM verification are required.
```

## JSON Index Format

```json
{
  "generated_at": "2026-05-22T12:00:00Z",
  "summary": {
    "total": 3,
    "valid": 2,
    "invalid": 1,
    "warnings": 4
  },
  "packages": [
    {
      "path": "pkg1",
      "name": "pkg1",
      "operation_type": "fret_slot_strategy",
      "status": "valid",
      "requires_human_review": true,
      "warnings": []
    }
  ]
}
```

## Integration

The indexer uses CAM-A6 inspection logic internally:

```bash
# Full workflow
python scripts/assemble_strategy_package.py strategy.json --out ./packages/pkg1
python scripts/inspect_strategy_package.py ./packages/pkg1
python scripts/index_strategy_packages.py ./packages/
```

## What This Is Not

The index generator does **not**:

- Mutate individual package contents
- Repair invalid packages
- Generate G-code
- Authorize machine execution

It produces **collection-level metadata** for navigating multiple packages.

## See Also

- [STRATEGY_PACKAGE_INSPECTION.md](STRATEGY_PACKAGE_INSPECTION.md) — Package inspection CLI
- [STRATEGY_PACKAGE_ASSEMBLY.md](STRATEGY_PACKAGE_ASSEMBLY.md) — Package assembly CLI
- [STRATEGY_PACKAGE_ARCHIVE.md](STRATEGY_PACKAGE_ARCHIVE.md) — Package archive CLI
- [STRATEGY_PACKAGE_MANIFEST.md](STRATEGY_PACKAGE_MANIFEST.md) — Manifest format
