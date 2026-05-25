# Review Decision Record

## Overview

The review decision record CLI records human review decisions for staged CAM Assist strategy packages.

The decision record is written as a **sibling file** to the package directory. Package contents are never modified.

This is **non-execution infrastructure**. It does not generate G-code, produce machine output, or authorize machine execution.

## Usage

### Record Approval

```bash
python scripts/record_review_decision.py staged_packages/fret_slot_strategy_package \
    --decision approve_for_downstream_cam \
    --reviewer "Human Reviewer" \
    --notes "Reviewed scale, fret count, kerf, and workholding assumptions."
```

Output: `staged_packages/fret_slot_strategy_package.review_decision.json`

### Record Rejection

```bash
python scripts/record_review_decision.py staged_packages/fret_slot_strategy_package \
    --decision reject \
    --reviewer "Human Reviewer" \
    --notes "Kerf assumption incompatible with available tooling."
```

### Request Revision

```bash
python scripts/record_review_decision.py staged_packages/fret_slot_strategy_package \
    --decision needs_revision \
    --reviewer "Human Reviewer" \
    --notes "Scale length needs verification."
```

### Custom Output Path

```bash
python scripts/record_review_decision.py <package_dir> \
    --decision approve_for_downstream_cam \
    --reviewer "Reviewer" \
    --out /tmp/decision.json
```

### Quiet Mode

```bash
python scripts/record_review_decision.py <package_dir> \
    --decision approve_for_downstream_cam \
    --reviewer "Reviewer" \
    --quiet
```

## CLI Options

| Option | Description |
|--------|-------------|
| `package_dir` | Path to the staged package directory (required) |
| `--decision` | Review decision: `approve_for_downstream_cam`, `reject`, or `needs_revision` (required) |
| `--reviewer` | Name or identifier of the human reviewer (required) |
| `--notes` | Optional reviewer notes |
| `--out <path>` | Output path for decision record (default: `<package_dir>.review_decision.json`) |
| `--force` | Overwrite existing decision record |
| `--quiet`, `-q` | Only print pass/fail summary |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Decision record created |
| 1 | Package validation or decision validation failure |
| 2 | File/read/write error |

## Decision Types

| Decision | Meaning |
|----------|---------|
| `approve_for_downstream_cam` | Package approved for downstream CAM processing. **Does NOT authorize machine execution.** |
| `reject` | Package rejected. Not suitable for downstream use. |
| `needs_revision` | Package requires revision before approval. |

## Decision Record Format

```json
{
  "record_type": "cam_assist_review_decision",
  "record_version": "1.0.0",
  "package_path": "staged_packages/fret_slot_strategy_package",
  "package_manifest_id": "fret_slot_strategy:fret-slots-25500-22f-sample",
  "operation_type": "fret_slot_strategy",
  "decision": "approve_for_downstream_cam",
  "reviewer": "Human Reviewer",
  "reviewed_at": "2026-05-23T12:00:00Z",
  "notes": "Reviewed scale, fret count, kerf, and workholding assumptions.",
  "authority": {
    "does_not_authorize_machine_execution": true,
    "requires_downstream_cam_verification": true,
    "human_review_recorded": true
  }
}
```

## Authority Constraints

Every decision record includes an `authority` block that explicitly states:

- `does_not_authorize_machine_execution`: **Always true**
- `requires_downstream_cam_verification`: **Always true**
- `human_review_recorded`: **Always true**

**Important**: `approve_for_downstream_cam` does **NOT** authorize machine execution. It only indicates that the package has been reviewed and is suitable for downstream CAM tooling.

## Validation Rules

Decision recording fails if:

- Package directory missing
- Package inspection fails (invalid package)
- Decision not in allowed set
- Reviewer missing or empty
- Output exists and `--force` not provided

## Package Integrity

The decision recorder:

- Never modifies package contents
- Writes decision as sibling file
- Does not add files to the package directory
- Preserves package as received

## Integration

Full workflow:

```bash
# Stage package
python scripts/stage_strategy_package.py package.zip --out ./staging/

# Generate review queue
python scripts/index_staged_packages.py ./staging/

# Record decision
python scripts/record_review_decision.py ./staging/package \
    --decision approve_for_downstream_cam \
    --reviewer "Reviewer Name" \
    --notes "All checks passed."
```

## What This Is Not

The decision recorder does **NOT**:

- Generate G-code
- Authorize machine execution
- Create manufacturing authority
- Modify package contents
- Bypass downstream verification

It records a **human review decision** adjacent to a staged package.

## See Also

- [STAGED_PACKAGE_REVIEW_QUEUE.md](STAGED_PACKAGE_REVIEW_QUEUE.md) — Review queue generator
- [STRATEGY_PACKAGE_IMPORT_STAGING.md](STRATEGY_PACKAGE_IMPORT_STAGING.md) — Import staging CLI
- [STRATEGY_PACKAGE_INSPECTION.md](STRATEGY_PACKAGE_INSPECTION.md) — Package inspection CLI
