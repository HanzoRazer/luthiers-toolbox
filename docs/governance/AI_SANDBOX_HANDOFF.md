# AI Sandbox Governance Handoff

**Date:** December 20, 2025
**From:** AI Guitar Vision Sandbox
**To:** AI Sandbox Enforcement CI

---

## Summary

The AI Guitar Vision system evaluation has been consolidated into the AI Sandbox Enforcement CI pipeline. All governance checks are now enforced via CI scripts rather than separate documentation.

---

## What Changed

| Before | After |
|--------|-------|
| Two separate documents | Single CI pipeline |
| Manual review checklists | Automated enforcement |
| Architecture reference docs | Code-as-documentation |

---

## CI Enforcement Scripts

All governance is now enforced by scripts in `ci/ai_sandbox/`:

| Script | Purpose | From |
|--------|---------|------|
| `check_ai_import_boundaries.py` | RMOS cannot import AI code | Original |
| `check_ai_forbidden_calls.py` | AI cannot call `approve()`, `persist_run()` | Original |
| `check_ai_write_paths.py` | AI cannot write to `rmos/runs/` | Original |
| `check_rmos_completeness_guard.py` | RunArtifact must use `validate_and_persist()` | **NEW** (from Guitar Vision) |

---

## The Trust Boundary

```
┌─────────────────────────────────────────┐
│           AI SANDBOX                     │
│         (_experimental/)                 │
│                                          │
│  • Can generate images                   │
│  • Can suggest parameters                │
│  • Can create AdvisoryAsset              │
│  • CANNOT approve workflows              │
│  • CANNOT create RunArtifact             │
│  • CANNOT write to RMOS paths            │
└─────────────────────────────────────────┘
                    │
          TRUST BOUNDARY (CI enforced)
                    │
                    ▼
┌─────────────────────────────────────────┐
│        AUTHORITATIVE LAYER              │
│      (rmos/, workflow/, services/)      │
│                                          │
│  • Computes feasibility (server-side)   │
│  • Approves/rejects workflows           │
│  • Creates RunArtifact via guard        │
│  • Persists immutable audit trail       │
└─────────────────────────────────────────┘
```

---

## Key Invariants (Now CI-Enforced)

### 1. Completeness Guard
**Script:** `check_rmos_completeness_guard.py`

All RunArtifact creation MUST go through `validate_and_persist()` which enforces:
- `feasibility_sha256` is present
- `risk_level` is present
- Missing fields → BLOCKED artifact (audit preserved)

### 2. Import Boundaries
**Script:** `check_ai_import_boundaries.py`

```python
# BLOCKED by CI
# rmos/any_file.py
from app._experimental.ai_graphics import anything  # ❌ FAILS CI
```

### 3. Forbidden Calls
**Script:** `check_ai_forbidden_calls.py`

AI sandbox code cannot call:
- `approve()`, `approve_workflow()`
- `generate_toolpaths()`
- `create_run()`, `persist_run()`
- `save_session()`

### 4. Write Path Restrictions
**Script:** `check_ai_write_paths.py`

AI sandbox code cannot write to:
- `rmos/runs/`
- `rmos/toolpaths/`
- `rmos/workflow/`

---

## Legacy Exceptions

These files bypass the completeness guard (tracked for cleanup):

| File | Reason | TODO |
|------|--------|------|
| `rosette_rmos_adapter.py` | Pre-existing direct RunArtifact use | Refactor to `validate_and_persist()` |
| `rmos_toolpaths_router.py` | Pre-existing direct RunArtifact use | Refactor to `validate_and_persist()` |

---

## Running Governance Checks Locally

```bash
# All AI sandbox checks
python ci/ai_sandbox/check_ai_import_boundaries.py
python ci/ai_sandbox/check_ai_forbidden_calls.py
python ci/ai_sandbox/check_ai_write_paths.py
python ci/ai_sandbox/check_rmos_completeness_guard.py

# Fortran Rule (no math in routers)
pytest tests/test_route_governance.py::TestFortranRule -v
```

---

## GitHub Actions Workflow

File: `.github/workflows/ai_sandbox_enforcement.yml`

Triggers on:
- Push to `main` or `develop`
- All pull requests

---

## What Was Retired

The following documents have been deleted (their content is now in CI):

- `AI Sandbox Enforcement CI.md`
- `AI_Guitar_Vision_SANDBOX_SYSTEM_EVALUATION.md`

---

## Developer Responsibilities

### When Adding AI Features

1. Place code in `_experimental/ai_*` directories
2. Use `AdvisoryAsset` for AI-generated content
3. Never import from `rmos/`, `workflow/`
4. Never call authority functions (`approve`, `persist_run`)

### When Adding RMOS Features

1. Use `validate_and_persist()` for all RunArtifact creation
2. Never import from `_experimental/`
3. Ensure `feasibility_sha256` and `risk_level` are provided

### When Modifying Governance

1. Update scripts in `ci/ai_sandbox/`
2. Add exceptions to allowlists with TODO comments
3. Run all checks locally before pushing

---

## Contact

For governance questions, check:
- `docs/governance/ARCHITECTURE_INVARIANTS.md`
- `docs/governance/HOW_TO_ADD_A_NEW_CALCULATION.md`
- `ci/ai_sandbox/*.py` (the scripts are the source of truth)

---

*Governance is enforced by CI, not documentation.*
