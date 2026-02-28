# CBSP21: Code Batch Submission Protocol v2.1

**Status:** Active
**Version:** 2.1
**Purpose:** Structured code patch submission with coverage verification

---

## Overview

CBSP21 (Code Batch Submission Protocol v2.1) is an internal governance protocol for managing code patches with:

- **Coverage verification** — Ensures scanned/captured content meets minimum thresholds (default: 95%)
- **Risk assessment** — Tracks risk level per file (low/medium/high)
- **Architecture scanning** — Integrates with architecture scan findings
- **Audit trail** — Structured manifest for patch inputs

---

## Directory Structure

```
luthiers-toolbox/
├── .cbsp21/                    # Configuration
│   ├── patch_input.json        # Current patch manifest
│   ├── patch_input.schema.json # JSON Schema for validation
│   └── patch_input.json.example
├── cbsp21/                     # Data
│   ├── full_source/            # Original source content
│   ├── scanned_source/         # Scanned/captured content
│   └── patch_packets/          # Generated patch packets
└── scripts/cbsp21/             # Scripts
    ├── cbsp21_coverage_check.py
    └── cbsp21_coverage_with_audit.py
```

---

## Patch Input Schema

The `.cbsp21/patch_input.json` manifest follows this schema:

```json
{
  "schema": "cbsp21_patch_input_v1",
  "coverage_min": 0.95,
  "files": [
    {
      "path": "services/api/app/example.py",
      "intent": "Fix edge case in calculation",
      "risk": "low",
      "behavior_change": "Minor output formatting",
      "verification": ["unit_test", "integration_test"]
    }
  ],
  "architecture_scan": {
    "scan_id": "scan_2026-02-28",
    "risk_summary": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 5
    },
    "acknowledged": true
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `"cbsp21_patch_input_v1"` |
| `files` | array | List of files in the patch |
| `files[].path` | string | Relative path from repo root |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `coverage_min` | number | Minimum coverage (0-1), default 0.95 |
| `files[].intent` | string | Why this file is being changed |
| `files[].risk` | enum | `"low"`, `"medium"`, or `"high"` |
| `files[].behavior_change` | string | What behavior changes |
| `files[].verification` | array | How to verify the change |
| `architecture_scan` | object | Linked architecture scan results |

---

## Coverage Check

The coverage check ensures that scanned content represents at least 95% of the original:

```bash
python scripts/cbsp21/cbsp21_coverage_check.py \
  --full-path cbsp21/full_source \
  --scanned-path cbsp21/scanned_source \
  --threshold 0.95
```

**Exit codes:**
- `0` — Coverage requirement satisfied
- `1` — Coverage below threshold (output prohibited)

---

## CI Workflows

| Workflow | Purpose |
|----------|---------|
| `cbsp21_gate.yml` | Validates patch_input.json against schema |
| `cbsp21_coverage_gate.yml` | Enforces coverage threshold |
| `cbsp21_patch_input_gate.yml` | Validates patch input format |
| `cbsp21_patch_packet_format.yml` | Validates patch packet structure |

---

## Related Documentation

- [Architecture Invariants](governance/ARCHITECTURE_INVARIANTS.md)
- [Fence Architecture](governance/FENCE_ARCHITECTURE.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-01 | Added architecture_scan integration |
| 2.0 | 2025-12 | Added risk assessment fields |
| 1.0 | 2025-11 | Initial protocol |
