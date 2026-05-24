# Research Platform 1A — Constitutional Alignment

**Status:** RATIFIED — interpretation boundary for all `docs/research/` work  
**Date:** 2026-05-20  
**Supersedes:** ad hoc assumptions in handoffs; does not modify `docs/governance/` authority rules

---

## Transition

The platform is moving from **large-scale exploratory R&D** to **institutional semantic engineering**.

```text
research remembers
governance ratifies
```

---

## Scope and authority

### 1. Is `docs/research/` the single source of institutional memory?

**Yes** — for semantic research lineage and discovery continuity.

**No** — for runtime legitimacy. `docs/governance/` remains authoritative for:

- promotion rules
- runtime authority
- operational constraints
- intake governance
- constitutional enforcement

| Domain | Owner |
|--------|--------|
| Research continuity | `docs/research/` |
| Runtime legitimacy | `docs/governance/` |
| Semantic discovery | research |
| Operational authority | governance |

---

### 2. Who may edit research docs?

- **Any engineer** may append findings, link lineage, document archaeology.
- Each wave has **named maintainers / stewards** for structural coherence and conflict resolution.
- **Reclassification, wave closure, or graduation claims** require maintainer review.

| Wave | Steward (initial) |
|------|-------------------|
| Wave 0 | Platform / governance liaison |
| Wave A | IBG + reconstruction steward |
| Wave B | Vectorizer evaluation steward |
| Wave C | Cognition sandbox steward |
| Wave D | Constitutional runtime steward |
| Wave E | IBG workflow steward |

*Update stewards in place when ownership changes.*

---

### 3. Citation format (tags, not SHAs)

Prefer:

```text
runtime spine @ <tag>
vectorizer-sandbox @ <tag>
```

Avoid raw commit SHAs in research prose (brittle, unreadable). Preserve semantic continuity, not git minutiae.

---

## Wave boundaries

### 4. Wave B evaluation migration

**COMPLETE** in `vectorizer-sandbox` (`src/evaluation/`).

Main repo may consume outputs, reference metrics, preserve interfaces — **evaluation science evolves in sandbox**, not in `services/blueprint-import/sandbox/` (removed).

---

### 5. Wave 0 — `ci/ai_sandbox`

**Formal Wave 0** — pre-constitutional semantic experimentation (Dec 2025). Do not erase origin lineage.

---

### 6. Wave C graduation (2026)

**NONE** officially targeted for graduation in 2026.

Semantic cognition remains sandbox research until provenance + operational repeatability mature. Research allowed; promotion not assumed.

---

## IBG vs vectorizer

### 7. Workflow Pipeline 1A

**Internal / developmental** runtime infrastructure — not public API product surface yet.

Document for architecture, IBG lineage, runtime continuity. Do not market as stable operator workflow.

---

### 8. Canonical IBG performance objective

```text
IBG exists to produce provenance-bearing,
human-reviewable body evidence
for governed geometric workflows.
```

**Not:** fully autonomous body completion.

IBG supports **semantic operationalization**, not autonomous semantic authority.

---

### 9. Morphology Harvest vs Workflow 1A

**Shared intake lineage; different runtime roles.**

| System | Role |
|--------|------|
| Morphology Harvest | Semantic extraction + evidence preparation |
| Workflow Pipeline 1A | Governed intake + runtime orchestration |

May converge later — do not collapse conceptually in docs yet.

---

## Topology registry

### 10. Ownership

- **Primary:** author of semantic/topology PR updates registry when behavior changes.
- **Secondary:** topology steward / curator.

---

### 11. Link priority

When available:

```text
ADR → governance doc → handoff → archaeology note
```

Prefer durable architectural rationale over transient sprint notes.

---

## Discovery matrix

### 12. Risk ratings

**Formal High / Medium / Low** on matrix rows (no scoring engine in 1A).

---

### 13. Canonical failure fixtures

**TBD — establish in Lane 4 (Research Wave 1B).**

Les Paul, slab_body collapse, primitive starvation → target **canonical semantic regression fixtures**.

---

## Process and freeze

### 14–15. Freeze 1A before 1B

**Yes.** Complete before formal 1B:

- PR-1 SIMPLE export integrity
- PR-2 grouping fallback telemetry
- PR-3 feedback lifecycle truthfulness
- Sandbox repo separation
- Research lineage stabilization

```text
1A = continuity restoration
1B = semantic interpretation refinement
```

Do not overlap aggressively.

### 16. `research_index.json`

**Commit** deterministic snapshots to git. No volatile timestamps, machine-local paths, or nondeterministic ordering by default.

---

### 17. Stale handoff paths

**No bulk rewrite** during 1A.

Allowed: clarification notes, redirect footnotes, “migrated to vectorizer-sandbox” annotations.  
Forbidden: aggressive rewrite of historical context.

---

## Non-goals (confirmed)

| Item | Status |
|------|--------|
| IBG memory population / semantic federation | **CONFIRMED out of scope** |
| Classifier expansion / cognition graduation | **CONFIRMED out of scope** for 1A |
| Governance architecture rewrites | **Frozen** — cross-links and lineage pointers only |

Allowed in 1A scope: evidence generation, provenance capture, review preparation, semantic instrumentation, topology evaluation, runtime gating.

---

---

## Wave 1B pointer (scope only)

Semantic interpretation trace and continuity observability: see [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) and [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md). This alignment doc remains frozen.

---

*Ratified alignment — Research Wave Index 1A — 2026-05-20*
