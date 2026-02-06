# CBSP21 — Complete Boundary-Safe Processing Protocol

**Policy Classification:** Repository Quality Control / Input Processing Governance  
**Version:** 2.0  
**Effective Date:** 2026-01-20  
**Owner:** tap_tone_pi Governance  
**Review Cycle:** Quarterly or upon major release  
**Applies To:** AI agents AND human contributors

---

## 1. Purpose

CBSP21 defines the **minimum completeness standard** for any automated system or human contributor scanning, processing, or modifying content in this repository. It is a **quality control gate** that prevents:

- Partial-capture errors leading to incomplete implementations
- Hallucinated or fabricated content fill-ins
- Scoping drift from incomplete context
- Software defects from incomplete code extraction
- Measurement contract violations from incomplete schema review

This protocol applies **equally to AI coding agents and human developers** as a shared quality standard.

---

## 2. Core Principle

> **Do not reason from partial inputs.**  
> **Do not summarize, transform, or implement code until ≥95% of the source has been fully scanned and verified.**

This principle is **non-negotiable** for both AI and human actors operating in this repository.

---

## 3. Scope

CBSP21 applies when **any actor** (AI or human) is instructed to:

- Scan or review files
- Summarize content
- Refactor or modify code
- Generate output based on existing files
- Extract code or data
- Implement features from specifications
- Validate schemas or contracts

### 3.1 Repository Structure Subject to CBSP21

```
tap_tone_pi/
├── tap_tone/              # Phase 1 CLI (stable) — single-channel tap tone
│   ├── analysis.py        # Pure DSP functions (frozen dataclass output)
│   ├── capture.py         # Audio recording (sounddevice → numpy)
│   ├── storage.py         # File writes, session log
│   └── main.py            # CLI entrypoint
├── scripts/
│   └── phase2/            # Phase 2 — 2-channel ODS, coherence, wolf metrics
│       ├── dsp.py         # TFResult dataclass, compute_transfer_and_coherence()
│       ├── metrics.py     # WSI curve computation
│       ├── export_viewer_pack_v1.py  # Evidence ZIP export
│       └── validate_viewer_pack_v1.py
├── modes/                 # Measurement modes (entry points only)
│   ├── _shared/
│   │   ├── wav_io.py      # ONLY WAV I/O module (enforced repo-wide)
│   │   └── emit_manifest.py  # Provenance + SHA-256 hashing
│   ├── acquisition/       # Serial sensor capture + simulators
│   ├── bending_rig/       # MOE from load+displacement
│   └── chladni/           # Pattern frequency indexing
├── contracts/             # Schema registry + *.schema.json output contracts
│   ├── schema_registry.json  # Authoritative schema index
│   └── schemas/           # Individual contract schemas
├── docs/                  # Governance and specification documents
│   ├── GOVERNANCE.md      # Master governance policy
│   ├── MEASUREMENT_BOUNDARY.md  # Scope policy
│   ├── BOUNDARY_RULES.md  # Import boundary rules
│   └── ADR-*.md           # Architecture Decision Records
├── tests/                 # pytest suite
├── examples/              # Hardware-free demos
├── cbsp21/                # CBSP21 ground truth and scanned content
│   ├── full_source/       # Immutable ground truth (read-only)
│   ├── scanned_source/    # Scanned/captured representation
│   └── patch_packets/     # Structured patch input files
└── logs/                  # Audit logs (cbsp21_audit.jsonl)
```

---

## 4. Coverage Requirement

### 4.1 Required Minimum

Any actor (AI or human) MUST:

- Attempt to process **100% of the provided content**
- Confirm **no less than 95% actual coverage** before producing output

### 4.2 Prohibited Actions

Actors MUST NOT:

| Prohibited Action | Rationale |
|-------------------|-----------|
| Generate conclusions from excerpts | Leads to incomplete implementations |
| Fill in gaps based on inference | Violates measurement-only doctrine |
| Treat missing sections as irrelevant | May miss critical constraints |
| Execute code from partial extracts | Safety hazard |
| Guess missing content | Breaks determinism |
| Treat prose outside code blocks as optional | Governance text is binding |
| Infer structure beyond what is explicit | Violates explicit contract principle |

---

## 5. Verification Procedure

### 5.1 Unit Enumeration

All relevant units MUST be identified:

| Unit Type | Example |
|-----------|---------|
| Files | `modes/_shared/wav_io.py` |
| Sections | `## 4. Coverage Requirement` |
| Code blocks | Python functions, JSON schemas |
| Schema fields | `freq_hz`, `H_mag`, `coherence` |

### 5.2 Coverage Measurement

Coverage MUST be measured by character or block count:

```
coverage = scanned_units / total_units
```

### 5.3 Coverage Confirmation

Output MAY proceed **only if**:

```
coverage >= 0.95
```

### 5.4 Audit Logging

All processing MUST log one of:

```
CBSP21 Coverage: 97.3% — All completeness conditions satisfied.
CBSP21 Coverage: 83.4% — Output halted. Missing content required.
```

Logs are appended to `logs/cbsp21_audit.jsonl`.

---

## 6. Mandatory Stop Conditions

Processing MUST **immediately stop and request clarification** when:

| Condition | Action |
|-----------|--------|
| Content appears truncated | STOP — request remainder |
| Code blocks are incomplete | STOP — request closure |
| File reference listed but content absent | STOP — request file |
| Fence marker opened but not closed | STOP — request closure |
| Binary or unreadable content detected | STOP — request clarification |
| Coverage cannot reach ≥95% | STOP — no output permitted |
| Missing dependency content | STOP — request dependencies |

**Failure to meet coverage = NO OUTPUT.**

The only permitted response is a request for the missing content.

---

## 7. Safety & Boundary Rules

These rules apply to **all actors** (AI and human):

| Rule | Enforcement |
|------|-------------|
| Never invent missing code or text | Code review + CI guard |
| Never assume omitted content is irrelevant | CBSP21 gate |
| Never merge partial fragments into runnable logic | Test coverage requirement |
| Never treat commentary as authoritative unless structured | Schema validation |

### 7.1 Cross-Reference: Governance Documents

CBSP21 operates in conjunction with:

| Document | Purpose | Path |
|----------|---------|------|
| `GOVERNANCE.md` | Master governance policy | [docs/GOVERNANCE.md](docs/GOVERNANCE.md) |
| `MEASUREMENT_BOUNDARY.md` | Measurement-only scope | [docs/MEASUREMENT_BOUNDARY.md](docs/MEASUREMENT_BOUNDARY.md) |
| `BOUNDARY_RULES.md` | Import boundary rules | [docs/BOUNDARY_RULES.md](docs/BOUNDARY_RULES.md) |
| `.github/copilot-instructions.md` | AI agent instructions | [.github/copilot-instructions.md](.github/copilot-instructions.md) |
| `contracts/schema_registry.json` | Schema version authority | [contracts/schema_registry.json](contracts/schema_registry.json) |

---

## 8. Structured Input & Immutability

### 8.1 Preferred Input Formats

To reduce scan ambiguity, inputs SHOULD use:

```
FILE: path/to/file.py
<full content>
```

Or unified diffs with explicit paths.

### 8.2 Immutable Ground Truth (`cbsp21/full_source/`)

The directory `cbsp21/full_source/` represents the **authoritative, immutable copy** of material being evaluated.

| Rule | Enforcement |
|------|-------------|
| `full_source/` MUST NOT be modified by AI or automation | CI guard |
| Only human-controlled processes may update `full_source/` | CODEOWNERS |
| All coverage calculations treat `full_source/` as read-only | Script enforcement |
| Automation writing to `full_source/` is a policy violation | CI failure |

Derived or scanned content goes to `cbsp21/scanned_source/` and may be regenerated.

### 8.3 Input File Structure

```
cbsp21/
├── full_source/           # Ground truth (immutable)
│   ├── tap_tone/          # Mirror of production code
│   ├── modes/
│   ├── contracts/
│   └── docs/
├── scanned_source/        # Scanned representation (mutable)
│   └── ...                # Same structure as full_source/
├── patch_packets/         # Structured patch inputs
│   ├── packet_001.md      # FILE: path + content format
│   └── manifest.json      # Packet index with coverage
└── logs/
    └── cbsp21_audit.jsonl # Append-only audit log
```

---

## 9. Output Timing

Output MAY only be produced **after ALL conditions are true**:

- [ ] Coverage ≥ 95%
- [ ] No unresolved missing content
- [ ] No unclosed code blocks
- [ ] No skipped embedded code regions
- [ ] All STOP CONDITIONS cleared
- [ ] Governance documents reviewed (for schema/contract changes)

---

## 10. Integrity Guarantees

CBSP21 ensures:

| Guarantee | Mechanism |
|-----------|-----------|
| Deterministic processing | Coverage gate |
| No accidental truncation | Stop conditions |
| No hallucinated fill-ins | Prohibition rules |
| Stable reproducibility | Audit logging |
| Clear safety boundaries | Explicit rules |

---

## 11. Audit Statement Format

### 11.1 Pass Statement

```
CBSP21 Coverage: 98.2% — All completeness conditions satisfied.
```

### 11.2 Fail Statement

```
CBSP21 Coverage: 83.5% — Output prohibited. Please provide remaining content.
Missing:
  - contracts/schemas/phase2_ods_snapshot.schema.json (referenced but not provided)
  - docs/ADR-0007_PHASE2_ODS_COHERENCE.md (lines 45-120 truncated)
```

---

## 12. CI Enforcement

### 12.1 Workflow Integration

CBSP21 is enforced via CI as a **merge-blocking gate**:

```yaml
# .github/workflows/cbsp21_gate.yml
name: CBSP21 Coverage Gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  cbsp21:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: CBSP21 Coverage Check
        run: |
          python scripts/cbsp21/cbsp21_coverage_check.py \
            --full-path cbsp21/full_source \
            --scanned-path cbsp21/scanned_source \
            --threshold 0.95
```

### 12.2 CI Workflow Summary

| Workflow | Purpose | Blocking |
|----------|---------|----------|
| `cbsp21_gate.yml` | Coverage ≥95% enforcement | ✅ Yes |
| `test.yml` | pytest suite (DSP, WAV I/O) | ✅ Yes |
| `wav-io-guard.yml` | Block direct `wavfile` usage | ✅ Yes |
| `schemas-validate.yml` | Schema validation | ✅ Yes |
| `boundary-guard.yml` | Import boundary enforcement | ✅ Yes |

See [docs/GOVERNANCE.md](docs/GOVERNANCE.md) Section 8 for complete CI minimum bar.

---

## 13. Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **AI Agents** | Verify coverage before producing output; halt on stop conditions |
| **Human Contributors** | Provide complete inputs; review AI outputs for compliance |
| **Code Reviewers** | Verify CBSP21 audit statements in PRs |
| **CI System** | Enforce coverage gates automatically |
| **Governance Owner** | Maintain policy; conduct periodic reviews |

---

## 14. Exceptions

Exceptions require:

1. Documented justification in PR description
2. Explicit coverage acknowledgment (e.g., "CBSP21 waiver: 87% coverage acceptable because...")
3. Approval from CODEOWNERS for affected paths

Exceptions are logged in `logs/cbsp21_exceptions.jsonl`.

---

## 15. Compliance with Measurement Doctrine

CBSP21 reinforces the **measurement-only doctrine**:

| CBSP21 Principle | Measurement Doctrine Alignment |
|------------------|--------------------------------|
| No fabricated content | No hallucinated measurements |
| Complete coverage before output | Complete data before analysis |
| Explicit stop conditions | Explicit admissibility gates |
| Audit logging | Provenance tracking |

Cross-reference: [docs/MEASUREMENT_BOUNDARY.md](docs/MEASUREMENT_BOUNDARY.md)

---

## 16. Implementation Scripts

### 16.1 Coverage Check Script

**Path:** `scripts/cbsp21/cbsp21_coverage_check.py`

```python
#!/usr/bin/env python
"""
CBSP21 Coverage Check — Enforces ≥95% coverage before output.

Usage:
    python scripts/cbsp21/cbsp21_coverage_check.py \
        --full-path cbsp21/full_source \
        --scanned-path cbsp21/scanned_source \
        --threshold 0.95
"""

import argparse
from pathlib import Path


def total_bytes_in_dir(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def compute_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="CBSP21 Coverage Check")
    ap.add_argument("--full-path", required=True, help="Immutable ground truth path")
    ap.add_argument("--scanned-path", required=True, help="Scanned content path")
    ap.add_argument("--threshold", type=float, default=0.95, help="Coverage threshold")
    args = ap.parse_args()

    full = Path(args.full_path)
    scanned = Path(args.scanned_path)

    if not full.exists():
        raise SystemExit(f"CBSP21 ERROR: Full path does not exist: {full}")
    if not scanned.exists():
        raise SystemExit(f"CBSP21 ERROR: Scanned path does not exist: {scanned}")

    if full.is_file() != scanned.is_file():
        raise SystemExit("CBSP21 ERROR: Paths must both be files or both be directories.")

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        raise SystemExit("CBSP21 ERROR: Full source appears empty.")

    coverage = scanned_bytes / full_bytes

    print(f"CBSP21 Coverage: {coverage * 100:.2f}%")
    print(f"  full_bytes    = {full_bytes}")
    print(f"  scanned_bytes = {scanned_bytes}")
    print(f"  threshold     = {args.threshold * 100:.2f}%")

    if coverage < args.threshold:
        print("CBSP21 FAIL: Coverage below threshold. Output prohibited.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 16.2 Audit Logger Script

**Path:** `scripts/cbsp21/cbsp21_audit_log.py`

```python
#!/usr/bin/env python
"""
CBSP21 Audit Logger — Appends coverage results to JSONL audit log.

Usage:
    python scripts/cbsp21/cbsp21_audit_log.py \
        --full cbsp21/full_source \
        --scanned cbsp21/scanned_source \
        --log logs/cbsp21_audit.jsonl
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def total_bytes(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--scanned", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--log", default="logs/cbsp21_audit.jsonl")
    args = ap.parse_args()

    full = Path(args.full)
    scanned = Path(args.scanned)
    log_path = Path(args.log)

    full_bytes = total_bytes(full)
    scanned_bytes = total_bytes(scanned)
    coverage = scanned_bytes / full_bytes if full_bytes else 0
    status = "pass" if coverage >= args.threshold else "fail"

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "CBSP21",
        "version": "2.0",
        "full_path": str(full),
        "scanned_path": str(scanned),
        "full_bytes": full_bytes,
        "scanned_bytes": scanned_bytes,
        "coverage_percent": round(coverage * 100, 2),
        "threshold_percent": args.threshold * 100,
        "status": status,
        "ci": {
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "sha": os.getenv("GITHUB_SHA"),
            "ref": os.getenv("GITHUB_REF"),
        },
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"CBSP21 {status.upper()}: {coverage * 100:.2f}% (logged to {log_path})")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 17. Makefile Integration

```makefile
# CBSP21 Coverage Targets

cbsp21-check:
	@python scripts/cbsp21/cbsp21_coverage_check.py \
	  --full-path cbsp21/full_source \
	  --scanned-path cbsp21/scanned_source \
	  --threshold 0.95

cbsp21-audit:
	@python scripts/cbsp21/cbsp21_audit_log.py \
	  --full cbsp21/full_source \
	  --scanned cbsp21/scanned_source \
	  --log logs/cbsp21_audit.jsonl

.PHONY: cbsp21-check cbsp21-audit
```

---

## 18. Revision History

| Rev | Date | Changes |
|-----|------|---------|
| 1.0 | 2026-01-01 | Initial release |
| 2.0 | 2026-01-20 | **Major rewrite**: Unified AI/human policy; repo-wide scope; governance cross-references; removed external system references; added file structure documentation |

---

## 19. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    CBSP21 Quick Reference                       │
├─────────────────────────────────────────────────────────────────┤
│  COVERAGE THRESHOLD: ≥95%                                       │
│  APPLIES TO: AI agents AND human contributors                   │
│  IMMUTABLE: cbsp21/full_source/ (read-only)                     │
│  MUTABLE: cbsp21/scanned_source/ (regenerable)                  │
│  AUDIT LOG: logs/cbsp21_audit.jsonl                             │
├─────────────────────────────────────────────────────────────────┤
│  STOP CONDITIONS:                                               │
│    • Truncated content                                          │
│    • Incomplete code blocks                                     │
│    • Missing file references                                    │
│    • Coverage < 95%                                             │
├─────────────────────────────────────────────────────────────────┤
│  RELATED DOCS:                                                  │
│    • docs/GOVERNANCE.md                                         │
│    • docs/MEASUREMENT_BOUNDARY.md                               │
│    • .github/copilot-instructions.md                            │
│    • contracts/schema_registry.json                             │
└─────────────────────────────────────────────────────────────────┘
```

---

*Adopted: 2026-01-01*  
*Last Updated: 2026-01-20*  
*Owner: tap_tone_pi Governance*
