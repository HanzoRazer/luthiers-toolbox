# Wave 1B Research Questions

**Wave:** 1B — Semantic Interpretation Trace  
**Purpose:** Bound future cognition work — prevent uncontrolled semantic expansion.

---

## Prerequisites (from 1A freeze — not blocking 1B docs)

| Prerequisite | Status |
|--------------|--------|
| PR-1 SIMPLE export integrity | PENDING / external verification |
| PR-2 grouping fallback telemetry | PENDING / external verification (telemetry modules exist on disk) |
| PR-3 feedback lifecycle truthfulness | PENDING / external verification |
| Sandbox repo separation stabilized | PENDING / external verification |
| Research Wave 1A spine merged | PENDING / external verification (stable enough on disk for 1B) |

1B proceeds as **docs-first**; no instrumentation in this sprint.

---

## Unresolved semantic questions

1. At which stage does **semantic occupancy** first diverge from **geometric occupancy** on real corpus DXFs?
2. When does `MorphologyDescriptor.confidence` disagree with `ScoringSignals.composite_score` by more than a useful threshold?
3. Can harvest E2E success (`body_grid_success`) occur while Workflow 1A intake gate would block the same evidence?
4. What minimum primitive survival rate defines “starvation” vs “sparse but valid” bodies?

---

## Topology unknowns

1. Canonical open-chain vs near-closed regression geometry — **fixture TBD**
2. Contour ownership graph for multi-sheet blueprints — **evolving**
3. Les Paul semantic continuity across REFINED vs V2_RAW — **evolving** (see `SPRINTS.md` accuracy notes; no single spine DXF)
4. Entity-level chain provenance from `edge_to_dxf` through `recover_topology` — **not exported**

---

## Morphology ambiguities

1. When does zone classifier output qualify as **slab_body** vs valid archtop — **slab fixture TBD**
2. Which solver paths consume `MorphologyDescriptor` as advisory vs ignore — **PENDING / external verification** (grep call sites)
3. Harvest adapter vs Workflow 1A wrap — single provenance chain **TBD**

---

## Instrumentation gaps (deferred wave)

| Gap | Desired (not in 1B) |
|-----|---------------------|
| Primitive survival counter | sandbox telemetry |
| Continuity metrics per stage | workflow stage hooks |
| Candidate trace dumps | review package attachment |
| Topology observability hooks | `topology_recovery` |

---

## Constitutional reminders (non-negotiable)

- No IBG memory population
- No classifier expansion on spine
- No semantic promotion / graduation in 1B
- No governance architecture rewrites
- Sandbox ML: **non-authoritative · research-only · non-canonical**

---

## Wave 1B completion criteria (this sprint)

- [x] Semantic degradation points traceable — [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md)
- [x] Primitive starvation documented structurally — [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md)
- [x] Morphology boundaries explicit — [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md)
- [x] Continuity failures indexed — [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md)
- [x] Observability gaps visible — [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md)
- [ ] Canonical regression fixtures — **TBD** (structure allowed with explicit labels)

---

## Pointer to Wave 1A alignment

Ratified operating answers: [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md) (frozen; minimal 1B pointer only).

---

*Research Wave 1B — 2026-05-20*
