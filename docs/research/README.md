# Institutional Semantic Memory

**Layer:** `docs/research/`  
**Status:** ACTIVE (Research Wave 1A + 1B)  
**Authority:** Discovery and lineage only — **not** operational authority

---

## What this is

`docs/research/` is the **institutional semantic memory layer** for The Production Shop vectorizer, IBG, topology, and semantic cognition work from **December 2025 through May 2026**.

It exists so the platform does not **forget itself**: repeated rediscovery of topology ideas, disconnected sandboxes, and migration without lineage are treated as memory failures, not individual engineer mistakes.

```text
research remembers   →  docs/research/ (lineage & discovery)
governance ratifies  →  docs/governance/ (authority & promotion)
sandbox discovers    →  vectorizer-sandbox (experiments)
runtime ratifies     →  luthiers-toolbox production paths only
```

This layer **records** what was discovered, where it came from, what it influenced, what remains unresolved, and where artifacts live **now** (runtime spine vs `vectorizer-sandbox`).

Release citations use narrative placeholders until tags exist:

```text
runtime spine @ pending tag
vectorizer-sandbox @ pending tag
```

---

## What this is not

- Not a substitute for `docs/governance/` (constitutional rules, canonical paths, lifecycle)
- Not a code migration plan (see `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md`)
- Not permission to wire archaeological code back into `services/` without graduation

**No production behavior changes** are implied by any document here.

---

## Core Wave 1A Spine

| Document | Purpose |
|----------|---------|
| [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md) | Time-indexed waves Wave 0 → E + Wave 1B phase |
| [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md) | IBG as governed runtime bridge (not research sandbox) |
| [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md) | IBG component evolution and Workflow 1A lineage |
| [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md) | At-risk topology ideas and where they live |
| [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) | Discoveries vs runtime vs sandbox vs risk (H/M/L) |
| [RESEARCH_PLATFORM_SPINE.md](RESEARCH_PLATFORM_SPINE.md) | archaeology → graduation stack |

---

## Core Wave 1B Spine

| Document | Purpose |
|----------|---------|
| [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) | **Primary 1B** — pipeline semantic continuity trace |
| [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) | Primitive starvation and topology→primitive degradation |
| [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md) | Harvest vs body_grid vs Workflow 1A authority |
| [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) | Indexed continuity failures + fixture metadata |
| [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md) | Current visibility vs blind spots vs desired telemetry |
| [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md) | Bounded open questions; 1A prerequisite status |

---

## Constitutional Alignment / Operating Answers

| Document | Purpose |
|----------|---------|
| [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md) | Ratified Q&A — authority, freeze, non-goals, citation policy |

---

## Supporting Research Notes

Outside the core 1A spine but indexed for continuity:

| Document | Purpose |
|----------|---------|
| [CAD_KERNEL_BOUNDARY_ANALYSIS.md](CAD_KERNEL_BOUNDARY_ANALYSIS.md) | CAD kernel adapter boundary research |
| [gibson_l37_1941_significance.md](gibson_l37_1941_significance.md) | Instrument canon / measurement significance |

---

## Related layers (read in order)

| Layer | Location | Role |
|-------|----------|------|
| **Governance** | `docs/governance/` | What production may do (authority, paths, lifecycle) |
| **Handoffs** | `docs/handoffs/` | Session and sprint narratives |
| **Research memory** | `docs/research/` (here) | What was learned and why it matters |
| **Runtime spine** | `services/` in `luthiers-toolbox` | Governed extraction + IBG constitutional runtime |
| **Cognition lab** | `vectorizer-sandbox` repo | Semantic R&D and archaeological lineage |

---

## Research waves (summary)

| Wave | Era | Theme |
|------|-----|--------|
| **0** | Dec 2025 | Pre-constitutional boundaries (`ci/ai_sandbox`) |
| **A** | Apr 2026 | Reconstruction intelligence (arc closure, body completion) |
| **B** | Apr–May 2026 | Evaluation science (corpus benchmarks, mode comparison) |
| **C** | Mar–May 2026 | Semantic cognition (grid, ML classification, supervision) |
| **D** | May 2026 | Constitutional runtime (provenance, intake gates, authority) |
| **E** | May 2026 | Workflow / IBG intake (Pipeline 1A, review packages) |

Detail: [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md).

---

## Capability and graduation (pointers)

| Topic | Document |
|-------|----------|
| Component lifecycle states | `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` |
| Sandbox migration | `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md` |
| Incubation architecture | `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md` |
| Sandbox chronology | `docs/handoffs/VECTORIZER_SANDBOX_CHRONOLOGY.md` |
| Vectorizer capability map | `docs/governance/VECTORIZER_CAPABILITY_MAP.md` |

---

## Machine-readable index

```bash
python scripts/research/build_research_index.py
```

Emits deterministic `reports/research/research_index.json` (committed snapshot; no timestamps). Includes all `docs/research/*.md` files.

---

## Validation

```bash
pytest tests/research/test_research_docs_structure.py -q
```

---

## Wave 1B scope

Wave **1B** adds **semantic continuity observability** (trace, primitive flow, morphology boundaries, failure index, observability map). Docs-only — no instrumentation in this sprint.

Prerequisite status: [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md). Ratified 1A boundaries: [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md).

---

*Research Wave Index 1A — Semantic Civilization Spine — 2026-05-20*
