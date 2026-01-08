# Art Studio Scope Governance v1.0

**Status:** Normative (Enforced by CI)  
**Effective Date:** 2026-01-07  
**Owner:** Architecture Board  
**Review Cycle:** Quarterly

---

## Executive Summary

This contract defines **what Art Studio is allowed to design**, **what it must never design**, and **how ornamental intent may be safely applied to other domains** without introducing feature creep, authority confusion, or manufacturing risk.

**Enforcement**: This document is backed by automated CI gates (`check_art_studio_scope.py`) that block PRs violating scope boundaries.

---

## Part I: Architectural Contract

### Core Principle (Non-Negotiable)

> **Art Studio is the sole authority for ornamental design intent.  
> It is not an authority for structure, geometry ownership, or manufacturing decisions.**

---

### Definitions

#### Ornament

A **planar, decorative pattern** intended to be embedded, engraved, or inlaid into a host surface, without carrying structural load.

**Examples:**
* Rosette rings
* Mosaic tile patterns
* Inlay strips
* Decorative motifs
* Color/material sequences

#### Host Geometry

A **structural or functional surface** that may receive ornamentation, but whose shape, load, and constraints are defined elsewhere.

**Examples:**
* Soundboard regions
* Headstock faces
* Bridge non-load zones
* Fingerboard surfaces

---

### Art Studio Authority (Explicitly Allowed)

Art Studio **MAY**:

#### 1. Create Ornament Intent

* `RosetteParamSpec`
* `InlayPatternSpec`
* Mosaic/tile generators
* Decorative macros and fix-its

#### 2. Manage Ornament Iteration

* Undo/redo history
* Snapshots and comparisons
* Versioned design evolution
* Human-driven refinement

#### 3. Express Ornament Feasibility Awareness

* Display RMOS-computed risk
* Highlight problematic regions
* Suggest corrective actions
* Block unsafe edits **at the UI layer only**

#### 4. Remain Host-Agnostic

* Ornament specs must be valid **without knowing the host**
* No ornament spec may assume:
  * Thickness
  * Load
  * Structural function

---

### Art Studio Prohibitions (Hard Line)

Art Studio **MUST NOT**:

#### 1. Define Host Geometry

* ❌ No outlines for headstocks, bridges, necks, bodies
* ❌ No tuner holes, pin holes, or structural cutouts
* ❌ No string tension modeling
* ❌ No saddle or bridge pin positioning

#### 2. Encode Structural Knowledge

* ❌ No string tension calculations
* ❌ No acoustic coupling models
* ❌ No stress or load modeling
* ❌ No material strength assumptions

#### 3. Decide Manufacturability

* ❌ No final "safe/unsafe" decisions
* ❌ No toolpath validation
* ❌ No CAM authority
* ❌ No G-code generation

#### 4. Bypass RMOS Governance

* ❌ No direct promotion
* ❌ No authority creation
* ❌ No implicit approval states
* ❌ No run ID creation

**Violation of any item above constitutes feature creep and will fail CI.**

---

### Ornament Placement (Allowed Integration Point)

Ornament may be applied to host geometry **only through a placement adapter**.

#### Placement Adapter Characteristics

The placement adapter:

* ✅ Projects ornament intent onto a host surface
* ✅ Clips ornament to allowed regions
* ✅ Applies scale, rotation, and orientation
* ❌ Does **not** modify:
  * Ornament definition
  * Host geometry definition

The adapter is:

* Thin
* Stateless
* Non-authoritative

---

### RMOS Authority (Clarified)

RMOS is the **sole authority** for:

* Feasibility computation
* Risk classification
* Review / rejection
* Promotion to manufacturing
* Decision traceability

**Art Studio consumes RMOS output; it never replaces it.**

---

### Spanish-Style Mosaic Rosettes (Explicit Scope)

Spanish-style mosaic rosettes are:

* Tile-based
* Ring-constrained
* Ornamental
* Planar

They are **explicitly in scope** for Art Studio.

Support for them does **not** constitute feature creep.

---

### Anti-Creep Test (Use This)

Before adding a feature, ask:

> Can this design be fully expressed as planar ornament intent  
> and validated primarily by manufacturability rather than structural integrity?

* ✅ **Yes** → Art Studio
* ❌ **No** → Out of scope

---

## Part II: Enforcement Mechanism

### Scope Gate Overview

The `check_art_studio_scope.py` script enforces this contract by:

1. Scanning Art Studio and RMOS UI code
2. Detecting forbidden patterns (keywords, API calls)
3. Failing CI if violations are found

**This gate is intentionally conservative** — it blocks first, allows after review.

---

### Forbidden Patterns (v1)

| Category | Pattern | Rationale |
|----------|---------|-----------|
| **HOST_GEOMETRY** | `headstock`, `bridge`, `neck`, `body`, `tuner_hole`, `pin_hole`, `truss_rod` | Structural domains |
| **HOST_GEOMETRY** | `tuner(s)`, `string tension`, `saddle`, `bridge pin` | Load-bearing elements |
| **MACHINE_OUTPUT** | `gcode`, `toolpath(s)`, `post-processor`, `\bnc\b` | CAM authority |
| **AUTHORITY** | `create_run_id`, `persist_run`, `store_artifact`, `write_run_artifact` | Governance bypass |
| **AUTHORITY** | `/api/(cam\|saw)/` | Direct machine execution |
| **AUTHORITY** | `promote`, `decideManufacturingCandidate`, `bulk-review` | Decision authority |

---

### Scanned Locations

Default targets:

* `client/src/components/rmos`
* `client/src/features/art_studio`
* `client/src/features/rmos`
* `services/api/app/art_studio`

File types: `.ts`, `.tsx`, `.vue`, `.py`

---

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | ✅ No violations |
| `1` | ❌ Violations found |
| `2` | ⚠️ Execution error |

---

## Part III: Implementation

### 1. Scope Gate Script

**Location:** `scripts/ci/check_art_studio_scope.py`

```python
#!/usr/bin/env python3
"""
Art Studio Scope Gate (v1)

Goal:
  Prevent feature creep by ensuring Art Studio remains ornament-authority only.

This is intentionally conservative and simple:
  - keyword/regex scanning across Art Studio + RMOS UI lane files
  - blocks on structural host-geometry intent or manufacturing authority calls

Exit codes:
  0 = pass
  1 = violations found
  2 = execution error
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


# --- Config ------------------------------------------------------------------

DEFAULT_TARGETS = [
    "client/src/components/rmos",
    "client/src/features/art_studio",
    "client/src/features/rmos",
    "services/api/app/art_studio",
]

INCLUDE_EXTS = {".ts", ".tsx", ".vue", ".py"}

# Things Art Studio must not *authoritatively* do.
# Keep these focused to avoid noise.
FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    # Host geometry creep (structural domains)
    ("HOST_GEOMETRY", r"\b(headstock|bridge|neck|body|tuner_hole|pin_hole|truss_rod)\b"),
    ("HOST_GEOMETRY", r"\b(tuner(s)?|string\s*tension|saddle|bridge\s*pin)\b"),

    # CAM / machine execution creep
    ("MACHINE_OUTPUT", r"\b(gcode|toolpath(s)?|post[-_ ]?processor|nc\b)\b"),

    # Authority creation (ledger / governance bypass)
    ("AUTHORITY", r"\b(create_run_id|persist_run|store_artifact|write_run_artifact)\b"),
    ("AUTHORITY", r"\b(/api/(cam|saw)/)\b"),  # calling CAM/SAW directly from Art Studio lane
    ("AUTHORITY", r"\b(promote|decideManufacturingCandidate|bulk-review|review)\b"),
]

# Allow-list exceptions (v1): places where words appear but are acceptable.
# Keep this minimal—prefer fixing wording if possible.
ALLOW_CONTEXT_PATTERNS: List[Tuple[str, str]] = [
    # Future: Add inline allow mechanism: # SCOPE_ALLOW: <TAG> <reason>
]


# --- Implementation -----------------------------------------------------------

@dataclass
class Finding:
    tag: str
    relpath: str
    line_no: int
    line: str
    pattern: str


def iter_files(root: Path, targets: Iterable[str]) -> Iterable[Path]:
    for t in targets:
        p = (root / t).resolve()
        if not p.exists():
            continue
        if p.is_file():
            if p.suffix in INCLUDE_EXTS:
                yield p
            continue
        for fp in p.rglob("*"):
            if fp.is_file() and fp.suffix in INCLUDE_EXTS:
                yield fp


def is_allowed(rel: str) -> bool:
    # Placeholder for file allowlists if you choose to use them later
    for _tag, pat in ALLOW_CONTEXT_PATTERNS:
        if re.search(pat, rel):
            return True
    return False


def scan_file(root: Path, fp: Path) -> List[Finding]:
    rel = str(fp.relative_to(root)).replace("\\", "/")
    if is_allowed(rel):
        return []

    findings: List[Finding] = []
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        findings.append(Finding("READ_ERROR", rel, 0, f"<read failed: {e}>", ""))
        return findings

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # quick skip for empty lines
        if not line.strip():
            continue
        for tag, pat in FORBIDDEN_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                findings.append(Finding(tag, rel, i, line.rstrip(), pat))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Targets to scan (default: Art Studio/RMOS UI + art_studio backend)",
    )
    ap.add_argument("--max-findings", type=int, default=200, help="Limit output")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()

    all_findings: List[Finding] = []
    for fp in iter_files(root, args.targets):
        all_findings.extend(scan_file(root, fp))

    # Filter out read errors from counting as violations? No — fail fast.
    violations = [f for f in all_findings if f.tag != "READ_ERROR"]
    read_errors = [f for f in all_findings if f.tag == "READ_ERROR"]

    if read_errors:
        print("[art-studio-scope] ERROR: failed to read some files:", file=sys.stderr)
        for f in read_errors[: args.max_findings]:
            print(f"  {f.relpath}: {f.line}", file=sys.stderr)
        return 2

    if not violations:
        print("[art-studio-scope] PASS: no scope violations found")
        return 0

    print(f"[art-studio-scope] FAIL: {len(violations)} scope violations found\n", file=sys.stderr)

    # Group by file for readability
    by_file: dict[str, List[Finding]] = {}
    for f in violations:
        by_file.setdefault(f.relpath, []).append(f)

    printed = 0
    for rel, fs in sorted(by_file.items()):
        print(f"--- {rel} ---", file=sys.stderr)
        for f in fs:
            print(f"{f.line_no:4d} [{f.tag}] {f.line}", file=sys.stderr)
            printed += 1
            if printed >= args.max_findings:
                print(f"\n[art-studio-scope] output truncated at {args.max_findings}", file=sys.stderr)
                return 1

    print(
        "\n[art-studio-scope] Guidance: Art Studio may author ornament intent only "
        "(rosette/inlay/mosaic). Host geometry + CAM + authority creation must live elsewhere.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"[art-studio-scope] ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)
```

---

### 2. Pytest Integration

**Location:** `services/api/tests/test_art_studio_scope_gate.py`

```python
"""
Art Studio Scope Gate - Pytest Wrapper

Ensures Art Studio code respects architectural boundaries.
Fails if ornament-only code attempts to define host geometry,
create manufacturing authority, or bypass RMOS governance.
"""

import subprocess
import sys
from pathlib import Path


def test_art_studio_scope_gate_v1():
    """
    Run Art Studio scope gate as blocking test.
    
    This enforces:
    - No host geometry (headstock, bridge, neck, body)
    - No CAM/machine output authority
    - No RMOS governance bypass
    """
    repo_root = Path(__file__).resolve().parents[3]  # services/api/tests/ -> repo
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "ci" / "check_art_studio_scope.py"),
        "--repo-root",
        str(repo_root),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        raise AssertionError(f"Art Studio scope gate failed:\n{out}")
```

---

### 3. CI Integration

Add to `.github/workflows/art_studio_scope_gate.yml`:

```yaml
name: Art Studio Scope Gate

on:
  pull_request:
    paths:
      - "client/src/components/rmos/**"
      - "client/src/features/art_studio/**"
      - "client/src/features/rmos/**"
      - "services/api/app/art_studio/**"
      - "scripts/ci/check_art_studio_scope.py"
      - ".github/workflows/art_studio_scope_gate.yml"
  push:
    branches: [main]

jobs:
  art-studio-scope-gate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          
      - name: Run Art Studio Scope Gate
        run: |
          python scripts/ci/check_art_studio_scope.py --repo-root .
          
      - name: Summary
        if: failure()
        run: |
          echo "## ❌ Art Studio Scope Violation" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Art Studio code attempted to:" >> $GITHUB_STEP_SUMMARY
          echo "- Define host geometry (headstock/bridge/neck)" >> $GITHUB_STEP_SUMMARY
          echo "- Create manufacturing authority" >> $GITHUB_STEP_SUMMARY
          echo "- Bypass RMOS governance" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "See docs/governance/ART_STUDIO_SCOPE_GOVERNANCE_v1.md" >> $GITHUB_STEP_SUMMARY
```

Or add to existing `core_ci.yml`:

```yaml
- name: Art Studio Scope Gate
  run: |
    python scripts/ci/check_art_studio_scope.py --repo-root .
```

---

### 4. Local Testing

```bash
# Run scope gate locally
python scripts/ci/check_art_studio_scope.py --repo-root .

# Run as pytest
cd services/api
pytest tests/test_art_studio_scope_gate.py -v

# Run with custom targets
python scripts/ci/check_art_studio_scope.py \
  --repo-root . \
  --targets client/src/features/art_studio
```

---

## Part IV: Exception Mechanism (Future)

### Inline Allow Comments (v1.1 - Planned)

For rare cases where forbidden keywords appear in safe contexts (comments, documentation):

```typescript
// SCOPE_ALLOW: HOST_GEOMETRY "Documentation reference only"
// Example: Art Studio patterns can be applied to headstock surfaces
```

**Rules for inline allows:**

1. Must include reason
2. Must be on same line as violation
3. Still blocks `AUTHORITY` violations
4. Requires architecture review if used >3 times

---

## Part V: Maintenance

### When to Update Patterns

**Add patterns when:**
* New forbidden authority emerges (e.g., `createDecision`, `writeLedger`)
* New structural domain added (e.g., `bracing`, `kerfing`)

**Remove patterns when:**
* False positives exceed 10% of violations
* Pattern superseded by more precise regex

### Review Schedule

* **Quarterly**: Check for false positives
* **On violation**: Evaluate if exception needed vs code refactor
* **On new Art Studio features**: Pre-check against contract

---

## Part VI: Decision Tree

```
┌─────────────────────────────────────────────┐
│ New Art Studio Feature Proposed             │
└──────────────────┬──────────────────────────┘
                   │
                   v
         ┌─────────────────────┐
         │ Is it purely         │
         │ ornamental intent?   │
         └──────┬───────────────┘
                │
        ┌───────┴──────┐
        │              │
       YES             NO
        │              │
        v              v
  ┌──────────┐   ┌──────────┐
  │ Planar   │   │ Out of   │
  │ pattern? │   │ scope    │
  └────┬─────┘   └──────────┘
       │
   ┌───┴────┐
   │        │
  YES       NO
   │        │
   v        v
┌──────┐ ┌──────────┐
│ Art  │ │ RMOS or  │
│Studio│ │ other    │
└──────┘ └──────────┘
```

---

## Final Statement

Art Studio exists to **protect the manufacturing pipeline from ambiguous ornament intent** while empowering human creativity.

It is intentionally narrow, intentionally powerful, and intentionally separated from structural design.

Any future expansion must preserve this boundary.

---

## Related Documents

* [BOUNDARY_RULES.md](../BOUNDARY_RULES.md) - Cross-repo boundaries
* [OPERATION_EXECUTION_GOVERNANCE_v1.md](./OPERATION_EXECUTION_GOVERNANCE_v1.md) - Operation lanes
* [CBSP21.md](../../CBSP21.md) - Completeness protocol
* [ROUTER_MAP.md](../../ROUTER_MAP.md) - API organization

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-07 | Initial release with CI enforcement |
