# Architecture Migration Assessment

**Date:** 2026-02-23
**Type:** Third-Party Consultant Assessment
**Subject:** Multi-Repo Extraction Readiness
**Verdict:** Option 3 (Hybrid) — After Prerequisites Complete

---

## Executive Summary

The target architecture (Hybrid: Core + Plugins with standalone designer extraction) is correct. However, **the codebase is not ready for extraction**. Attempting to extract now will create two broken codebases instead of one working one.

**Recommendation:** Complete remediation and add internal package boundaries before extraction.

---

## Current State Assessment

| Issue | Evidence | Impact on Extraction |
|-------|----------|---------------------|
| 992+ routes | No clear core vs. optional | Can't identify what goes where |
| 691 broad exceptions | Error handling crosses boundaries | Extraction breaks error paths |
| 14+ god objects (>500 LOC) | Logic tangled across modules | Can't extract without rewriting |
| No internal package boundaries | `from app.rmos import...` everywhere | Imports create dependency chains |

---

## Why Extraction Would Fail Today

Example: Extracting `neck-designer` currently requires:

```python
# Current state: services/api/app/instrument_geometry/neck/taper.py
from app.calculators.fret_slots_cam import compute_slots  # Pulls in CAM
from app.rmos.feasibility import check_neck_params        # Pulls in RMOS
from app.cam.rosette.pattern_generator import ...         # Pulls in god object
```

**Result:** Extracting one designer pulls in the entire CAM/RMOS stack.

---

## The Sequence That Works

```
PHASE 1: Finish Remediation (Current)
    ↓
PHASE 2: Internal Package Boundaries (New)
    ↓
PHASE 3: Extract to Standalone Repos (Later)
```

---

## Phase 1: Finish Remediation (4-6 weeks)

### Progress Tracking

| Metric | Baseline | Current | Target |
|--------|----------|---------|--------|
| Routes | 992 | 669 | <400 |
| Broad exceptions | 725 | 540 | <200 |
| Files >500 LOC | 14 | 11 | 0 |
| main.py LOC | 905 | 236 | ✅ Done |

### Remaining Work
- Exception hardening in safety-critical paths (rmos/, cam/, saw_lab/)
- God-object decomposition (11 files remaining)
- Route consolidation to <400

---

## Phase 2: Internal Package Boundaries (4-6 weeks)

### Target Structure

```
services/api/app/
├── core/                    # Shared types, math, geometry
│   └── __init__.py         # Exports only stable interfaces
├── cam/                     # CAM pipeline
│   ├── __init__.py         # Public API only
│   └── _internal/          # Not importable from outside
├── rmos/                    # Safety system
│   ├── __init__.py
│   └── _internal/
├── saw_lab/                 # Batch operations
├── analyzer/                # Audio/visual (returning)
├── business/                # Business suite (new)
├── designers/               # Extractable standalone tools
│   ├── neck/
│   ├── bridge/
│   ├── headstock/
│   └── fingerboard/
└── boundary_spec.json       # Enforces import rules
```

### Boundary Rules

```python
# ci/check_package_boundaries.py
ALLOWED_IMPORTS = {
    "designers.neck": ["core"],           # Can only import core
    "designers.bridge": ["core"],
    "cam": ["core", "rmos"],              # Can import core + rmos
    "rmos": ["core"],                     # Can only import core
    "analyzer": ["core"],                 # Isolated
    "business": ["core", "calculators"],  # Limited access
}

FORBIDDEN_IMPORTS = {
    "designers.*": ["cam", "rmos", "saw_lab"],  # Designers can't touch production
}
```

### Why Boundaries First
- Test boundaries BEFORE extraction
- CI catches violations immediately
- Extraction becomes mechanical once boundaries are clean

---

## Phase 3: Extract When Ready (2-4 weeks)

### Target Architecture

```
luthiers-toolbox/                    # Golden Master (Production Station)
├── services/api/app/
│   ├── core/                        # Always included
│   ├── cam/                         # Production CAM
│   ├── rmos/                        # Safety system
│   ├── saw_lab/                     # Batch operations
│   ├── analyzer/                    # Plugin (enabled)
│   └── business/                    # Plugin (enabled)
└── Feature flags control edition builds

ltb-standalone-designers/            # Separate repo (~20K LOC)
├── neck-designer/                   # Extracted from designers/neck/
├── bridge-designer/                 # Extracted from designers/bridge/
├── headstock-designer/
└── fingerboard-designer/
→ npm packages for distribution
→ Gumroad/Etsy sales
→ CANNOT import cam/rmos/saw_lab (enforced at source)
```

### Clean Extraction (After Phase 2)

```bash
# With boundaries enforced, extraction is copy-paste:
cp -r services/api/app/designers/neck ltb-standalone-designers/neck-designer/
cp -r services/api/app/core ltb-standalone-designers/shared/
# Done. No surgery required.
```

---

## New Additions Assessment

### Audio/Visual Analyzer (Returning)

| Aspect | Assessment |
|--------|------------|
| Source | tap_tone_pi repository |
| Boundary status | Clean (`boundary_spec.json` exists) |
| Integration method | `viewer_pack_v1` contract (HTTP/file), not code merge |
| Phase | Add in Phase 2 as plugin |
| Risk | Low — already isolated |

### Business Startup Suite (New)

| Aspect | Assessment |
|--------|------------|
| Location | Create in `services/api/app/business/` |
| Boundaries | Can only import `core` and `calculators` |
| Features | COGS, pricing, BOM, break-even, cash flow |
| Phase | Build in Phase 2 with boundaries from day one |
| Risk | Low — greenfield with clean architecture |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 4-6 weeks | Remediation complete (exceptions, god objects, routes <400) |
| **Phase 2** | 4-6 weeks | Internal boundaries with CI enforcement |
| **Phase 3** | 2-4 weeks | Standalone designer extraction |
| **Total** | **10-16 weeks** | Clean extraction capability |

---

## Decision Matrix

| Approach | When Appropriate | Your Situation |
|----------|-----------------|----------------|
| **Option 1** (Multi-repo now) | Team with DevOps capacity | ❌ Solo dev, too much overhead |
| **Option 2** (Monolith only) | Never plan to sell standalone | ❌ Gumroad/Etsy sales planned |
| **Option 3** (Hybrid) | After boundaries exist | ✅ Correct — after Phase 2 |

---

## Conclusion

**The architecture decision is correct. The timing is not.**

Option 3 (Hybrid) with luthiers-toolbox as golden master and standalone designers extracted to a separate repo is the right target. However, extraction without internal boundaries will create maintenance hell.

**Sequence:**
1. Finish remediation (you're here)
2. Add internal package boundaries
3. Then extract — it will be trivial

---

*Assessment conducted 2026-02-23*
