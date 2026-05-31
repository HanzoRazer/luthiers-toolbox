# Three-Loop Architecture — Reframed

**Status:** SUPERSEDED — DEMOTED FROM ACTIVE GOVERNANCE (2026-05-30)
**Effective:** 2026-05-11 — **demoted 2026-05-30**

> **CONFLATION CORRECTION (2026-05-30).** This document was marked ACTIVE GOVERNANCE on the
> premise that "the three-loop architecture was approved in CLAUDE.md." Per ground truth from
> Ross (2026-05-30), that premise is false: the three-loop architecture was **experimental,
> never approved, and never implemented** in this repo — it has been **sandboxed into
> `vectorizer-sandbox`**. The CLAUDE.md "APPROVED DESIGN" status and the "approved … across
> multiple sessions" provenance were unsourced inflation (now corrected at the source). This
> document therefore cannot derive governance authority from that approval. **It is demoted to
> historical/superseded and must not be cited as active governance.** See
> `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md`.

---

## Context

The three-loop architecture was labeled "approved in CLAUDE.md (2026-04-02)" — **corrected
2026-05-30: it was experimental, never approved, sandbox-owned (see banner above).** This
document reframes the architecture within MRP governance constraints, but holds no active
authority.

---

## Architecture Overview

```
Loop 1: Intra-Frame Validation (within one extraction)
Loop 2: Cross-Image Learning (across extractions)
Loop 3: User Correction Retraining (from feedback)
```

---

## Loop 1 — Intra-Frame Validation

**Status:** PARTIAL — Scale validation only

| Component | Status |
|-----------|--------|
| `validate_scale_before_export()` | IMPLEMENTED |
| 5-check voting system | NOT IMPLEMENTED |
| Fallback retry logic | NOT IMPLEMENTED |

**Governance:** Loop 1 improvements are permitted but must not alter `restored_baseline` behavior.

---

## Loop 2 — Cross-Image Learning

**Status:** NOT IMPLEMENTED

| Component | Status |
|-----------|--------|
| `strategy_cache` | NOT IMPLEMENTED |
| `get_image_signature()` | NOT IMPLEMENTED |
| `try_all_strategies()` | NOT IMPLEMENTED |
| `pick_best()` | NOT IMPLEMENTED |

**Governance:** Loop 2 implementation requires dedicated sprint (VECTOR-2A). Must operate behind feature flag. Must not affect deterministic MVP path.

---

## Loop 3 — User Correction Retraining

**Status:** ORPHANED — Infrastructure exists, not wired

| Component | Status |
|-----------|--------|
| `FeedbackSystem` class | EXISTS (lines 1181-1267) |
| `TrainingDataCollector` class | EXISTS (lines 1273-1330) |
| API endpoint | NOT IMPLEMENTED |
| Retraining pipeline | NOT IMPLEMENTED |

**Governance:** Loop 3 activation requires API endpoint creation. Corrections must not auto-modify production extraction. Manual review gate required.

---

## Governance Constraints

### All loops must:

1. Preserve deterministic MVP baseline
2. Operate behind feature flags
3. Maintain rollback paths
4. Produce audit logs
5. Document confidence levels

### No loop may:

1. Modify `restored_baseline` behavior
2. Auto-update production extraction parameters
3. Bypass BOE authority for corrections
4. Operate without regression verification

---

## Implementation Priority

| Phase | Loop | Scope | Status |
|-------|------|-------|--------|
| 1 | Loop 1 | Complete 5-check voting | PENDING |
| 2 | Loop 2 | Strategy caching | PENDING |
| 3 | Loop 3 | Wire existing infrastructure | PENDING |

**Prerequisite:** Blueprint Reader reactivation approval required before any loop work.

---

## AGE Integration

AGE (Agentic Guidance Engine) sits above Loop 1 as decision layer.

**Status:** NOT IMPLEMENTED

**Governance:** AGE must fall back silently if API unavailable. AGE recommendations are advisory, not authoritative.

---

*Three-loop architecture within MRP governance. Deterministic MVP is protected.*
