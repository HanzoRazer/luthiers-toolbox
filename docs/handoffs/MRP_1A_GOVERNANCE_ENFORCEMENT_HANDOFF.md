# MRP-1A: Governance Enforcement Infrastructure Handoff

**Date:** 2026-05-11  
**Status:** COMPLETE  
**Sprint:** MRP-1A  
**Domain:** Morphology Reconstruction Platform

---

## Summary

MRP-1A converts Phase 0 governance documentation into machine-readable, checkable enforcement infrastructure. Future sessions cannot silently modify protected Blueprint Reader, IBG, DXF, or governance spine files without tripping a governance check.

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/governance/governance_manifest.json` | Machine-readable registry of protected systems |
| `scripts/check_protected_paths.py` | Detect changes to protected paths in staged files |
| `scripts/check_sprint_namespace.py` | Warn on unnamespaced dev order references |
| `tests/regression_corpus/manifest.json` | Declared regression artifacts (not yet populated) |

---

## Files Modified

| File | Change |
|------|--------|
| `.pre-commit-config.yaml` | Added governance-protected-paths and sprint-namespace-check hooks |
| `services/api/app/routers/blueprint/vectorize_router.py` | Added governance header |
| `services/api/app/services/blueprint_orchestrator.py` | Added governance header |
| `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py` | Added governance header |
| `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py` | Added governance header |
| `services/api/app/util/dxf_compat.py` | Added governance header |
| `services/api/app/cam/dxf_writer.py` | Added governance header |

---

## Protected Systems Registered

| System ID | Protection Level | Path Count |
|-----------|------------------|------------|
| `BLUEPRINT_READER_MVP` | LOCKED | 7 paths |
| `RESTORED_BASELINE_MODE` | LOCKED | 2 paths |
| `DXF_COMPAT_LAYER` | LOCKED | 3 paths |
| `IBG_CORE` | LOCKED | 4 paths |
| `MORPHOLOGY_GOVERNANCE_DOCS` | STABILIZED | 1 path |

---

## Enforcement Behavior

### Protected Path Check (`check_protected_paths.py`)

**Trigger:** Pre-commit hook runs on every commit attempt.

**Detection:** Scans staged files (`git diff --cached`) against protected paths in `governance_manifest.json`.

**Failure mode:**
```
[FAIL] Protected system modified without approval:

  System: BLUEPRINT_READER_MVP
  File: services/api/app/services/blueprint_extract.py
  Protection level: LOCKED
  Governance doc: docs/governance/BLUEPRINT_READER_PROTECTION_RULES.md

To approve these changes, set:
  GOVERNANCE_APPROVED_CHANGE=1
```

**Exit code:** 1 on violation, 0 if clean or approved.

### Sprint Namespace Check (`check_sprint_namespace.py`)

**Trigger:** Pre-commit hook runs on every commit attempt.

**Detection:** Scans `docs/handoffs/` and `docs/governance/` for patterns like "Dev Order 24" without namespace prefix.

**Failure mode:** Warning only (exit 0).

---

## How to Override Intentionally

To approve changes to protected paths:

```bash
# Option 1: Environment variable (recommended)
GOVERNANCE_APPROVED_CHANGE=1 git commit -m "message"

# Option 2: PowerShell
$env:GOVERNANCE_APPROVED_CHANGE = "1"; git commit -m "message"
```

The check will pass with an informational notice:
```
[INFO] Governance approval detected (GOVERNANCE_APPROVED_CHANGE=1)
[INFO] Allowing changes to 2 protected file(s):
  - services/api/app/services/blueprint_extract.py (BLUEPRINT_READER_MVP)
```

---

## What Is NOT Enforced Yet

| Enforcement | Status | Notes |
|-------------|--------|-------|
| Commit message approval marker | NOT IMPLEMENTED | Environment variable only for now |
| CI/CD integration | NOT IMPLEMENTED | Pre-commit hooks only |
| Regression test gating | NOT IMPLEMENTED | Corpus manifest declares artifacts only |
| Governance header validation | NOT IMPLEMENTED | Headers added but not checked programmatically |

---

## Governance Headers Added

6 files received governance headers:

```python
# GOVERNANCE:
# SYSTEM: BLUEPRINT_READER_MVP
# STATUS: PROTECTED_PRODUCTION_BASELINE
# DOC: docs/governance/BLUEPRINT_READER_PROTECTION_RULES.md
# RULE: Do not alter production behavior without GOVERNANCE_APPROVED_CHANGE.
```

| System | Files |
|--------|-------|
| BLUEPRINT_READER_MVP | `vectorize_router.py`, `blueprint_orchestrator.py` |
| IBG_CORE | `instrument_body_generator.py`, `body_contour_solver.py` |
| DXF_COMPAT_LAYER | `dxf_compat.py`, `dxf_writer.py` |

---

## Regression Corpus Status

`tests/regression_corpus/manifest.json` declares 5 artifacts:

| Artifact ID | Status | System |
|-------------|--------|--------|
| `MELODY_MAKER_PDF` | REQUIRED_FUTURE | BLUEPRINT_READER_MVP |
| `DREADNOUGHT_REFERENCE` | REQUIRED_FUTURE | BLUEPRINT_READER_MVP |
| `CUATRO_REFERENCE` | REQUIRED_FUTURE | BLUEPRINT_READER_MVP |
| `LES_PAUL_REFERENCE` | REQUIRED_FUTURE | BLUEPRINT_READER_MVP |
| `DREADNOUGHT_IBG_VALIDATION` | REQUIRED_FUTURE | IBG_CORE |

Artifacts are declared but not populated. Actual test files will be added in future sprints.

---

## Next Recommended Phase

### MRP-1B: CI Integration (Optional)

- Add governance checks to GitHub Actions workflow
- Block PR merge if protected paths modified without approval
- Add governance status to PR checks

### MRP-2A: Regression Test Wiring

- Populate regression corpus with actual test artifacts
- Wire regression tests to governance manifest
- Add automated dimension validation

---

## Verification

To verify enforcement is active:

```bash
# Install pre-commit hooks
pre-commit install

# Test protected path detection (should fail)
echo "# test" >> services/api/app/services/blueprint_orchestrator.py
git add services/api/app/services/blueprint_orchestrator.py
pre-commit run governance-protected-paths

# Expected: [FAIL] Protected system modified without approval

# Clean up
git checkout services/api/app/services/blueprint_orchestrator.py
```

---

## Guardrails Maintained

This sprint did NOT:
- Change Blueprint Reader behavior
- Change IBG math
- Change vectorizer modes
- Change DXF output
- Implement Loop 1, Loop 2, or Loop 3
- Implement AGE
- Move files
- Rename production routes
- Refactor protected systems

Enforcement infrastructure only.

---

*MRP-1A complete. Governance enforcement infrastructure active.*
