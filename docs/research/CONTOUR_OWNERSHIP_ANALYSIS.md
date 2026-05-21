# Contour Ownership Analysis

**Wave:** 1C  
**Purpose:** Which contours belong to the **semantic body** — commercial boundary quality, not a duplicate of [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) §4/§6.

---

## Ownership pipeline (verified modules)

| Stage | Module | Decision |
|-------|--------|----------|
| DXF entities → chains | `topology_recovery.recover_topology()` | LINE/LWPOLYLINE/ARC chaining |
| Body candidacy filter | `IBGWorkflowPipeline.isolate_candidates()` | Closed, near-closed, large chain, LINE-scale rectangle heuristics |
| Rank ownership | `candidate_scoring.score_candidates()` | Highest `composite_score` → rank 1 |
| Evidence wrap | `wrap_candidates()` → `BodyEvidence` | Normalized segments from winning contour |
| Artifact bridge | `ArtifactBodyEvidenceAdapter` | DXF/SVG → outline points → `BodyEvidence` / candidate |

Adapter role (major boundary): `morphology_harvest/artifact_body_evidence_adapter.py` — parses vectorizer DXF, builds `ParsedArtifact`, converts to `BodyEvidenceCandidate` with `AuthorityState`, `ProvenanceRecord`, `ConfidenceDeclaration`.

---

## Ownership classes

| Class | Description | Risk |
|-------|-------------|------|
| **Outer-body ownership** | Primary closed/near-closed contour at guitar scale | Low if scoring + closure correct |
| **Inner contour leakage** | Holes, labels, inner cuts scored as body | Commercial: wrong waist/bout |
| **False contour adoption** | Text/dimension strokes pass `not_text_stroke` weakly | Sheet geometry dominates rank |
| **Fragmented ownership** | Multiple partial chains; rank picks wrong fragment | Broken outline in review |

---

## Current heuristics (runtime)

From `isolate_candidates()` (documented in module):

- `is_closed` → keep
- `gap_distance < 5.0` → keep (near-closed)
- `perimeter_mm > 500` and `len(points) > 50` → keep
- `perimeter_mm >= 800` and `len(points) >= 4` → keep (LINE-sourced body)

From `ScoringSignals`:

- `not_text_stroke`, `vertical_extent`, `waist_narrowing`, `bout_presence` — influence rank, **heuristic**

**Open contour:** `wrap_candidates` records `record_topology_degradation` when not closed — visible in provenance, not always obvious in review summary alone.

---

## Topology blind spots

| Blind spot | Commercial effect |
|------------|-------------------|
| No contour-parent graph in review package | Reviewer cannot see *why* contour won |
| Grouping fallback not in `CandidateSummary` | Inconsistent geometry vs prior run |
| Multi-candidate sheets | Second-best contour may be more “body-like” visually |
| Adapter vs workflow dual paths | Harvest adapter vs `ibg_workflow_pipeline` may diverge |

---

## Proposed observability (deferred — docs only)

- Contour ownership graph in review package
- Fallback reason echo in `CandidateSummary`
- Outer vs inner contour tagging (sandbox-future, non-authoritative)

---

## Cross-links

- Trace: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) stages 3–5
- Fixtures: [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md) — partial contour ownership
- Ranking: [SEMANTIC_RANKING_SIGNALS.md](SEMANTIC_RANKING_SIGNALS.md)

---

*Research Wave 1C — 2026-05-20*
