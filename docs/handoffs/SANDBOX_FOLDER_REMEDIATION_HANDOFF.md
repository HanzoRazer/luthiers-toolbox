# Developer Handoff: Sandbox Folder Remediation

**Date:** 2026-05-20  
**Status:** Ready for remediation  
**Priority:** Medium (hygiene)  
**Depends On:** PR-2 → PR-1 → PR-3 remediation sprint (per VECTORIZER_SANDBOX_MIGRATION_PLAN.md)  
**Estimated Effort:** 2-4 hours

---

## Executive Summary

The repository contains multiple `sandbox/` directories from historical R&D phases. An audit on 2026-05-20 identified:

| Category | Git-Tracked | Local-Only | Action |
|----------|-------------|------------|--------|
| Orphaned code (importable) | 3 files | — | Migrate or delete |
| Experimental artifacts | 0 files | ~240 MB | Already gitignored |
| Active governance | 5 files | — | Keep |

**Total git-tracked sandbox files requiring action: 3**

---

## 1. Orphaned Sandbox Code (Requires Action)

### Location
```
[repo-root]/sandbox/arc_reconstructor/
├── body_contour_solver.py      (git-tracked)
├── instrument_body_generator.py (git-tracked)
├── reference_outline_bridge.py  (git-tracked)
└── [~150 MB gitignored artifacts]
```

### Original Intent
These files were R&D prototypes for the **arc reconstruction** and **body contour solving** systems developed during the IBG (Instrument Body Generator) incubation phase (circa March-April 2026). They were intended to:

- `body_contour_solver.py` — Solve body outline constraints from partial DXF data
- `instrument_body_generator.py` — Generate parametric body models from solved constraints
- `reference_outline_bridge.py` — Bridge between reference outlines and the solver

### Current Condition

**Status: ORPHANED — No imports, no callers**

Verification performed 2026-05-20:
```bash
# Search for any imports of these modules
grep -r "from sandbox" --include="*.py" .
grep -r "import body_contour_solver" --include="*.py" .
grep -r "import instrument_body_generator" --include="*.py" .
grep -r "import reference_outline_bridge" --include="*.py" .
# Result: 0 matches in production code
```

The functionality these files prototyped has been **promoted to production** at:
- `services/api/app/instrument_geometry/body/ibg/` — Production IBG implementation (ACTIVE, 25+ importers)
- `services/api/app/instrument_geometry/body/ibg/constraint_extractor.py` — Production constraint extraction
- `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py` — Production solver (same code, proper package structure)

**The production IBG files are actively used.** The sandbox versions are the original R&D prototypes that were copied to production and properly packaged. Key differences:

| Aspect | Sandbox (orphaned) | Production (active) |
|--------|-------------------|---------------------|
| Imports | Local (`from body_contour_solver`) | Package (`from .body_contour_solver`) |
| Governance | None | `PROTECTED_PRODUCTION_BASELINE` |
| LayerConsolidator | `sys.path.insert` hack | Proper `from app.cam` import |
| Importers | 0 files | 25+ files (router, tests, scripts) |

### Recommended Action

**MIGRATION COMPLETE (2026-05-20)**

Files migrated to `vectorizer-sandbox` repo:

| Source (luthiers-toolbox) | Destination (vectorizer-sandbox) |
|---------------------------|----------------------------------|
| `sandbox/arc_reconstructor/body_contour_solver.py` | `src/archaeology/arc_reconstructor/` |
| `sandbox/arc_reconstructor/instrument_body_generator.py` | `src/archaeology/arc_reconstructor/` |
| `sandbox/arc_reconstructor/reference_outline_bridge.py` | `src/archaeology/arc_reconstructor/` |

**Commit:** `5b07cbc` on branch `feat/tier-a-semantic-lineage-import`  
**Remote:** https://github.com/HanzoRazer/vectorizer-sandbox

**Remaining action — delete from luthiers-toolbox:**

```bash
git rm sandbox/arc_reconstructor/body_contour_solver.py
git rm sandbox/arc_reconstructor/instrument_body_generator.py
git rm sandbox/arc_reconstructor/reference_outline_bridge.py
git commit -m "chore: remove migrated sandbox prototypes

Migrated to vectorizer-sandbox/src/archaeology/arc_reconstructor/
per VECTORIZER_SANDBOX_MIGRATION_PLAN.md (commit 5b07cbc)."
```

### Justification

1. **Dead code accumulates confusion** — Developers searching for "body_contour_solver" find two files with the same name, one orphaned
2. **No runtime path** — These files are not imported, tested, or executed
3. **Superseded by production** — The production IBG implementation is the authority
4. **Migration plan exists** — `VECTORIZER_SANDBOX_MIGRATION_PLAN.md` already designates these for migration
5. **Grep-gate enforcement** — CI check `scripts/governance/check_semantic_sandbox_imports.py` prevents re-importing sandbox code

---

## 2. Gitignored Local Artifacts (No Action Required)

### Location
```
sandbox/                                    (~157 MB local)
├── arc_reconstructor/
│   ├── results/                           (DXF test outputs)
│   ├── Inst_body_generator/               (consolidated DXF outputs)
│   └── SESSION_AUDITS.md
├── body_curvature_constraints.csv
└── test_body_solver_manual.py

services/api/test_temp/sandbox_diagnostic/  (~32 MB local)
└── melody_maker_debug/                    (debug PNGs)

services/api/test_temp/sandbox_vs_engineer_comparison/ (~51 MB local)
├── dreadnought/sandbox_output/
├── gibson_l0/sandbox_output/
├── melody_maker/sandbox_output/
└── double_neck/sandbox_output/

services/blueprint-import/sandbox/          (~2.8 GB local)
├── text_geometry_eval/
│   ├── outputs/                           (2.8 GB - gitignored)
│   ├── corpus/                            (gitignored)
│   └── [evaluation scripts]
└── adaptive_reconstruction/
```

### Original Intent

These directories contain **generated artifacts** from R&D experiments:
- DXF outputs from arc reconstruction experiments
- Debug PNG images from vectorizer comparison runs
- Text geometry evaluation corpus and outputs

### Current Condition

**Status: GITIGNORED — Not in repository**

All large artifacts are excluded via `.gitignore` rules:
```gitignore
# In services/blueprint-import/sandbox/text_geometry_eval/.gitignore
corpus/
outputs/
```

**0 files** from these directories are tracked in git.

### Recommended Action

**No git action required.**

For local cleanup (optional):
```bash
# Remove local sandbox artifacts (safe - gitignored)
rm -rf [repo-root]/sandbox/arc_reconstructor/results/
rm -rf [repo-root]/sandbox/arc_reconstructor/Inst_body_generator/
rm -rf services/api/test_temp/sandbox_diagnostic/
rm -rf services/api/test_temp/sandbox_vs_engineer_comparison/
rm -rf services/blueprint-import/sandbox/text_geometry_eval/outputs/
```

### Justification

These artifacts are:
1. **Regenerable** — Scripts exist to recreate them
2. **Not tracked** — Already excluded from git
3. **Developer-local** — Each developer may have different artifacts from their experiments
4. **Large** — 2.8 GB of text_geometry_eval outputs alone

---

## 3. Blueprint-Import Sandbox Scripts (Evaluate for Keep/Archive)

### Location
```
services/blueprint-import/sandbox/
├── text_geometry_eval/
│   ├── generate_report.py          (git-tracked, 7.7 KB)
│   ├── measure_march6_archive.py   (git-tracked, 2.4 KB)
│   ├── run_evaluation.py           (git-tracked, 8.8 KB)
│   ├── README.md                   (git-tracked)
│   └── runners/                    (git-tracked, ~65 KB)
└── adaptive_reconstruction/        (git-tracked, ~54 KB)
```

### Original Intent

**text_geometry_eval/** — Evaluation framework for measuring text preservation quality in vectorizer outputs. Used to validate the `morph_close_kernel=0` configuration for text-preserving extraction.

**adaptive_reconstruction/** — Experimental adaptive contour reconstruction algorithms.

### Current Condition

**Status: EXPERIMENTAL — Scripts present, not integrated**

These scripts are:
- Not imported by production code
- Not run by CI
- Used manually for R&D evaluation

Last modified: 2026-05-17 (runners/)

### Recommended Action

**Keep for now, evaluate after remediation sprint.**

These evaluation scripts may be useful for:
- Validating vectorizer changes
- Regression testing text preservation
- Benchmarking extraction quality

If not used within 60 days, archive per documentation policy.

### Justification

1. **Small footprint** — ~100 KB of scripts (outputs gitignored)
2. **Potential utility** — Text geometry evaluation is relevant to ongoing vectorizer work
3. **Low priority** — Not blocking anything, not causing confusion
4. **60-day rule** — Can be archived later if unused

---

## 4. Active Governance (Keep)

### Location
```
ci/ai_sandbox/
├── __init__.py
├── check_ai_forbidden_calls.py
├── check_ai_write_paths.py
├── check_ai_import_boundaries.py
└── check_rmos_completeness_guard.py
```

### Original Intent

CI enforcement checks for AI-assisted development boundaries:
- Prevent forbidden API calls in AI-generated code
- Enforce write path restrictions
- Validate import boundaries
- Guard RMOS completeness requirements

### Current Condition

**Status: ACTIVE — Used by CI**

Referenced by: `.github/workflows/ai_sandbox_enforcement.yml`

### Recommended Action

**Keep — Do not modify.**

### Justification

1. **Active CI integration** — Workflow depends on these checks
2. **Governance function** — Part of the constitutional runtime enforcement
3. **"ai_sandbox" is semantic** — The name refers to AI sandboxing, not R&D sandbox folders

---

## 5. Related Documentation

| Document | Location | Relevance |
|----------|----------|-----------|
| Migration Plan | `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md` | Defines migration strategy |
| Incubation Architecture | `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md` | Defines cognition layer separation |
| Technical Debt Inventory | `docs/governance/VECTORIZER_TECHNICAL_DEBT_INVENTORY.md` | Lists orphaned code |
| Component Lifecycle | `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` | Defines ORPHANED → ARCHIVED flow |

---

## 6. Verification Commands

After remediation, verify cleanup with:

```bash
# Should return 0 (only ci/ai_sandbox/ should remain)
git ls-files sandbox/ | grep -v "^ci/" | wc -l

# Should return only ci/ai_sandbox files
git ls-files | grep sandbox

# Confirm no imports of sandbox code
grep -r "from sandbox\." --include="*.py" services/ packages/
```

---

## 7. Acceptance Criteria

- [ ] 3 orphaned `[repo-root]/sandbox/arc_reconstructor/*.py` files migrated or deleted
- [ ] Lineage documented in `docs/archive/INDEX.md` if deleted
- [ ] No production code imports from `sandbox/`
- [ ] `ci/ai_sandbox/` remains intact and functional
- [ ] CI passes after changes

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Deleting code still needed | Low | Medium | Verify zero imports before deletion |
| Breaking ci/ai_sandbox | Low | High | Explicit exclusion from cleanup scope |
| Losing historical context | Low | Low | Git history preserves all changes |

---

*Handoff prepared by Claude Code — 2026-05-20*  
*Based on audit of sandbox directories and cross-reference with governance documentation*
