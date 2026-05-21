# Semantic Artifact Quality

**Wave:** 1C — Semantic Artifact Quality (May 2026+)  
**Status:** ACTIVE — commercial/artifact-quality interpretation layer (docs only)  
**Spine:** Primary Wave 1C document

Builds on: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md), [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md). Does not duplicate 1B failure narratives.

Citation: `runtime spine @ pending tag` · `vectorizer-sandbox @ pending tag`

---

## Mission

Wave 1A gave **institutional memory**. Wave 1B gave **continuity observability**. Wave 1C begins improving how **commercially meaningful semantic geometry** survives extraction — through analysis and explicit quality expectations, not through authority promotion or production rollout.

---

## Commercial objective (1C canonical)

```text
The platform exists to produce
commercially viable,
human-reviewable,
fabrication-oriented semantic geometry.
```

**Not:** autonomous design generation, or unsupervised morphology canonization.

Operational bridge (unchanged): [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md) — provenance-bearing governed runtime.

---

## Research philosophy

```text
beautiful geometry requires semantic continuity
```

This is an **architectural principle**, not a formal metric threshold system. Metrics and signals are **enabling instrumentation** for future waves — not the end product of 1C.

---

## Quality dimensions

| Dimension | Meaning for reviewers / fabrication workflows |
|-----------|-----------------------------------------------|
| **Artifact coherence** | Preserved DXF/SVG, hashes, and package JSON tell one story |
| **Outline continuity** | Closed/near-closed body contours without silent fragmentation |
| **Morphology recognizability** | Waist, bouts, asymmetry visible in evidence — not slab-like flattening |
| **Fabrication plausibility** | Geometry could plausibly drive CAM prep after human approval |
| **Semantic continuity** | Meaning does not collapse between extraction and review — see 1B trace |
| **Review clarity** | Rank, gate, provenance, and topology stats explain *why* a candidate leads |

Detail: [REVIEW_PACKAGE_QUALITY_GUIDE.md](REVIEW_PACKAGE_QUALITY_GUIDE.md), [SEMANTIC_RANKING_SIGNALS.md](SEMANTIC_RANKING_SIGNALS.md).

---

## Priority collapse modes (commercial lens)

| Failure | Commercial impact | 1B index |
|---------|-------------------|----------|
| primitive starvation | Body identity collapse (holes/routes missing) | [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) |
| slab_body collapse | Morphology flattening | [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) §2 |
| contour fragmentation | Broken outlines | §3 loop fragmentation |
| grouping fallback ambiguity | Inconsistent geometry run-to-run | §5 (verified telemetry) |
| partial contour ownership | Malformed body boundaries | §6 |
| low morphology confidence | Unstable review quality | [MORPHOLOGY_CONTINUITY_EVALUATION.md](MORPHOLOGY_CONTINUITY_EVALUATION.md) |

Fixtures: [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md) (references 1B structural registry).

---

## Worked example — grouping fallback → review package (grounded)

**Path:** photo vectorize → workflow 1A → on-disk review JSON.

1. **Extraction:** `edge_to_dxf.py` may call `grouping_telemetry.record_grouping_fallback(reason=...)` when isolation fails; API exposes `build_topology_provenance()` — verified: `services/photo-vectorizer/grouping_telemetry.py`, `test_vectorizer_grouping_telemetry.py`.

2. **Topology:** `recover_topology()` produces `TopologyStats` (open/closed/near_closed counts) consumed by `emit_review_package()`.

3. **Ownership:** `IBGWorkflowPipeline.isolate_candidates()` keeps closed, near-closed (&lt;5 mm gap), large chains (&gt;500 mm), or LINE-sourced body-scale contours (&gt;800 mm perimeter) — see `ibg_workflow_pipeline.py`.

4. **Ranking:** `ScoringSignals` → `composite_score()`; top candidate wrapped via `create_candidate_from_evidence()` with `rank_score` as heuristic confidence — **not canonization**.

5. **Review:** `ReviewPackage` JSON includes `candidate_summaries[]` with `rank`, `rank_score`, `rejection_flags`, `gate_decision`, plus `topology_stats` — **no primitive overlay fields today**.

**Quality gap visible in package:** reviewer sees rank and closure flags but not grouping-fallback reason unless separately correlated from vectorizer API provenance — see [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md).

---

## Major transition boundary

**`artifact_body_evidence_adapter.py`** — vectorizer artifact → `BodyEvidence` / `BodyEvidenceCandidate` with constitutional metadata. See [CONTOUR_OWNERSHIP_ANALYSIS.md](CONTOUR_OWNERSHIP_ANALYSIS.md) and [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md).

---

## Wave 1C doc map

| Document | Focus |
|----------|--------|
| [CONTOUR_OWNERSHIP_ANALYSIS.md](CONTOUR_OWNERSHIP_ANALYSIS.md) | Which contour owns the body |
| [PRIMITIVE_SURVIVABILITY_ANALYSIS.md](PRIMITIVE_SURVIVABILITY_ANALYSIS.md) | Visible primitive loss |
| [MORPHOLOGY_CONTINUITY_EVALUATION.md](MORPHOLOGY_CONTINUITY_EVALUATION.md) | Recognizable body identity |
| [SEMANTIC_RANKING_SIGNALS.md](SEMANTIC_RANKING_SIGNALS.md) | Implemented vs proposed signals |
| [REVIEW_PACKAGE_QUALITY_GUIDE.md](REVIEW_PACKAGE_QUALITY_GUIDE.md) | Reviewer visibility |
| [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md) | Commercial fixture overlay |

---

## Non-goals (1C)

- Production deployment, classifier graduation, memory persistence, semantic federation
- Sandbox/production code changes (Step 8 visualization **deferred**)
- Hard quality score thresholds or autonomous promotion

---

## README note

If `README.md` is missing in checkout, use [_README.md](_README.md) for spine links.

---

*Research Wave 1C — 2026-05-20*
