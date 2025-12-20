# Runs Advisory Integration - Reference Documentation

**Status:** REFERENCE ONLY - NOT FOR IMPORT

**Date:** December 20, 2025

---

## Purpose

This folder contains **reference implementations** that were used as design templates
during the RMOS Runs V2 migration. These files are preserved for documentation purposes
but should **NOT be imported or used in production code**.

---

## Production Implementations

The actual production code lives in:

| Reference File | Production Location |
|----------------|---------------------|
| `schemas.py` | `services/api/app/rmos/runs_v2/schemas.py` |
| `store.py` | `services/api/app/rmos/runs_v2/store.py` |
| `router.py` | `services/api/app/rmos/runs_v2/api_runs.py` |
| `hashing.py` | `services/api/app/rmos/runs_v2/hashing.py` |
| (orchestration) | `services/api/app/services/rmos_run_service.py` |
| (orchestration) | `services/api/app/services/saw_lab_service.py` |

---

## Key Differences: Reference vs Production

### 1. Immutability

**Reference (here):** Allows `patch_meta()` and mutable updates

**Production:** Strict immutability - write-once, append-only advisory links

### 2. Required Fields

**Reference (here):** `feasibility_sha256` and `risk_level` are optional

**Production:** Both are REQUIRED - missing fields trigger completeness guard

### 3. Storage Structure

**Reference (here):** Single-file per run (`{run_id}.json`)

**Production:** Date-partitioned (`{YYYY-MM-DD}/{run_id}.json`)

### 4. Completeness Guard

**Reference (here):** None - accepts incomplete artifacts

**Production:** Creates BLOCKED artifact if invariants violated

---

## When to Reference These Files

- Understanding the original design intent
- Comparing v1 patterns vs v2 improvements
- Historical context for architecture decisions

---

## When NOT to Use These Files

- Do not import from this folder in production code
- Do not copy-paste without checking production implementations
- Do not treat as current API documentation

---

## Related Documentation

- `docs/governance/ARCHITECTURE_INVARIANTS.md` - 6-layer architecture
- `docs/governance/HOW_TO_ADD_A_NEW_CALCULATION.md` - Developer guide
- `docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md` - Contract spec

---

*These files are preserved for reference only. Always use the production implementations.*
