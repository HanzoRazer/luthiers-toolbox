# Three-Loop Architecture — Reframed

**Status:** ACTIVE GOVERNANCE (promoted 2026-08-28)
**Effective:** 2026-05-11 — demoted 2026-05-30 — **promoted 2026-08-28**

**APPROVED BY:** Ross (repository owner), 2026-08-28, by direct instruction in session.

> **PROMOTION RECORD (2026-08-28).** This document is promoted to active governance by an
> explicit owner decision recorded here. That decision is the authority; nothing in this
> document derives its standing from CLAUDE.md, from a claim about what was approved
> previously, or from repetition across sessions.
>
> **This does not reverse the 2026-05-30 correction — it supersedes the demotion only.**
> The findings that caused the demotion remain true and are restated as constraints below:
> the *named, unified* architecture (`ValidatedExtractor`, `AdaptiveExtractor`,
> `VectorizerAGE`, `strategy_cache`) was never approved and appears in **zero files in
> either repository**; the research line is owned by `vectorizer-sandbox`. What is promoted
> is **this document's authority to govern loop work**, not a claim that the architecture
> exists or that building it is owed.
>
> Why the demotion happened, and why it cannot recur here: the previous ACTIVE GOVERNANCE
> marking rested on an unsourced provenance claim ("approved in CLAUDE.md", "identified
> repeatedly across multiple sessions") with no decision record behind it. The `APPROVED BY`
> line above is that record. A future session finding this document marked ACTIVE should
> check that line — not re-derive approval from citation count.
> See `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md` for the full
> conflation analysis, which stands unchanged.

---

## Context

The three-loop architecture was labeled "approved in CLAUDE.md (2026-04-02)" — corrected
2026-05-30: that label was experimental work presented as an approved mandate, and the
research line is sandbox-owned. This document reframes the architecture within MRP
governance constraints and, as of 2026-08-28, **holds active governance authority over loop
work** on the strength of the owner decision recorded in the banner above.

Reading rule, unchanged by the promotion:

```text
GOVERNS loop work  ≠  ASSERTS the architecture exists  ≠  MAKES building it owed
```

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
| `validate_scale_before_export()` | IMPLEMENTED — runtime; shipped, and independent of the loops |
| 5-check voting system | NOT IMPLEMENTED in runtime — built out to a **7-agent panel** in `vectorizer-sandbox/src/incubation/agentic_supervisor.py` |
| Fallback retry logic | NOT IMPLEMENTED in runtime |

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

**Status:** DORMANT — wired, and switched off by default

> **Row corrected 2026-08-28 (code-verified, both repositories).** This previously read
> "ORPHANED — Infrastructure exists, not wired." That was wrong: the wiring exists and the
> call site is live. What gates it is a default-`False` constructor flag — a different, and
> much shorter, distance from working than "not wired."

| Component | Status |
|-----------|--------|
| `FeedbackSystem` class | EXISTS — `vectorizer_phase3.py` |
| `TrainingDataCollector` class | EXISTS — `vectorizer_phase3.py` |
| Constructor flag `enable_feedback` | EXISTS, **defaults to `False`** |
| `self.feedback = FeedbackSystem(...)` | **WIRED** (guarded by the flag) |
| `self.feedback.record_classification(...)` | **WIRED** (guarded by `if self.feedback and ml_clf`) |
| API endpoint | NOT IMPLEMENTED |
| Retraining pipeline | NOT IMPLEMENTED |

The runtime (`services/blueprint-import/vectorizer_phase3.py`) and the sandbox
(`vectorizer-sandbox/src/incubation/vectorizer_phase3.py`) carry the **same** wiring at
different line offsets. There is no runtime-versus-sandbox difference here and nothing to
migrate — consistent with §9 of the conflation-removal handoff, which dispositions these
classes **DORMANT** on exactly this ground.

Line numbers are deliberately omitted: the previous figures (1181–1267 / 1273–1330) had
drifted from the file by the time they were next read. Locate by symbol.

**Governance:** Loop 3 activation requires API endpoint creation **and** a decision to flip
`enable_feedback`. Because the code path already exists, flipping that flag is a behaviour
change on a live extraction path, not new development — treat it as such. Corrections must
not auto-modify production extraction. Manual review gate required.

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
