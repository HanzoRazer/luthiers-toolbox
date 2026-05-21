# Semantic Observability Map

**Wave:** 1B  
**Purpose:** Map **what runtime can observe today** vs **blind spots** vs **desired instrumentation** — basis for future telemetry waves (not implemented in 1B).

---

## Legend

| Column | Meaning |
|--------|---------|
| **Current Visibility** | Verified signals on disk today |
| **Blind Spot** | What operators/reviewers cannot see reliably |
| **Desired Instrumentation** | Sandbox-only / telemetry-only targets (deferred) |

---

## Topology & extraction

| Domain | Current Visibility | Blind Spot | Desired Instrumentation |
|--------|-------------------|------------|-------------------------|
| DXF entity inventory | Phase3 result dicts, entity counts | Per-entity semantic role | Mode-labeled entity lineage export |
| Cleanup mode | API `CleanupMode`, orchestrator flags | Semantic loss per mode | Mode comparison trace (sandbox eval) |
| Contour chains | `TopologyStats`, `ContourCandidate` | Chain provenance entity IDs | `chain_entity_ids[]` in review package |
| Gap closure tier | Registry docs; arc recon code | Which tier applied per contour | Tier telemetry in `topology_recovery` |
| Grouping fallback | `grouping_telemetry`, `topology_provenance` in API | Pre/post topology diff | Fallback corpus diff dump (sandbox) |
| Open vs closed | `is_closed`, `gap_distance` | Near-closed false positive rate | Near-closed classifier metrics |

---

## Primitives

| Domain | Current Visibility | Blind Spot | Desired Instrumentation |
|--------|-------------------|------------|-------------------------|
| Phase3 primitives | `primitives_count`, `export_primitives_to_dxf` | Survival rate contour→DXF | Primitive survival counter |
| Grid primitives | `MorphologyDescriptor.primitives` length | Dropped primitive reasons | Per-zone primitive audit log |
| Starvation events | Matrix + logs (narrative) | Automatic starvation alert | Structured `primitive_starvation` event |

---

## Morphology

| Domain | Current Visibility | Blind Spot | Desired Instrumentation |
|--------|-------------------|------------|-------------------------|
| Zones | `zone_coverage`, `missing_regions` | slab_body collapse detection | Zone collapse detector |
| Variant class | `variant_match`, morphology_class in E2E | Grammar confidence vs topology fit | Variant/topology disagreement flag |
| Descriptor confidence | `MorphologyDescriptor.confidence` | Lineage of confidence inputs | Confidence decomposition record |
| Harvest E2E | `E2ESpineResult` stage flags | Harvest vs workflow gate divergence | Unified run_id across harvest+workflow |

---

## Authority & provenance

| Domain | Current Visibility | Blind Spot | Desired Instrumentation |
|--------|-------------------|------------|-------------------------|
| BodyEvidenceCandidate | Provenance + authority on candidate | DXF→candidate transform steps | Stage-level provenance chain |
| Intake gate | `IntakeValidationResult` in tests/pipeline | Gate reason in review package summary | Gate reason codes (telemetry) |
| Review package | `ReviewPackage` JSON on disk | Candidate ranking rationale | Trace dump attachment (deferred) |
| RMOS | API GREEN/YELLOW/RED | Link RMOS to body candidate | PENDING / external verification |

---

## Sandbox ML (non-authoritative)

| Domain | Current Visibility | Blind Spot | Desired Instrumentation |
|--------|-------------------|------------|-------------------------|
| Classifier scores | `vectorizer-sandbox` only | Any leak to spine default | Import gate + grep CI |
| Cognitive extractor | Archaeology location | Production wiring | Lifecycle DEAD enforcement |
| Eval modes | `vectorizer-sandbox/src/evaluation/` | Live production parity | Mode matrix dashboard (eval repo) |

Label all sandbox ML observations: **non-authoritative · research-only · non-canonical**.

---

## Workflow 1A stages

| Stage | Current Visibility | Blind Spot | Desired Instrumentation |
|-------|-------------------|------------|-------------------------|
| preserve_artifacts | `PreservedArtifact` hashes | — | — |
| recover_topology | `PipelineStageResult` | Fallback path used flag | `_fallback_topology_recovery` counter |
| isolate/score | `ScoredCandidate` dicts | Ownership graph | Contour parent map |
| wrap + gate | candidates + gate results | Per-candidate block reason | Gate telemetry |
| emit_review_package | `review_package_path` | Full semantic trace | 1B-deferred trace export |

---

## Cross-links

- Trace stages: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md)
- Failures: [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md)
- Open gaps: [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md)

---

*Research Wave 1B — 2026-05-20*
