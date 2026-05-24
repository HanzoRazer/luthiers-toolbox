# Primitive Flow Analysis

**Wave:** 1B  
**Purpose:** Structural trace of **primitive starvation** and topology→primitive degradation — not a duplicate of [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) row narratives.

---

## Flow overview

```text
vectorizer contours (phase3 / edge_to_dxf)
    → DXF entities (holes, arcs, lines)
    → IBG topology_recovery (contour chains)
    → BodyEvidence segments
    → body_grid PrimitiveDetector → MorphologyPrimitive[]
    → MorphologyDescriptor.primitives
    → (optional) harvest E2E spine reporting primitives_count
```

**Collapse point:** primitives can disappear at **extraction**, **contour chaining**, **zone assignment**, or **descriptor aggregation** without a single observable counter today.

---

## Spine modules (verified)

| Step | Module | Function / type |
|------|--------|-----------------|
| Phase3 detection | `services/blueprint-import/vectorizer_phase3.py` | `PrimitiveDetector`, `export_primitives_to_dxf`, `enable_primitives` on orchestrator |
| Photo pipeline | `services/photo-vectorizer/edge_to_dxf.py` | Contour grouping → DXF (fallback paths affect topology) |
| Grid primitives | `ibg/body_grid/primitives.py` | `MorphologyPrimitive`, `PrimitiveDetector` |
| Descriptor | `ibg/body_grid/morphology_descriptor.py` | `MorphologyDescriptor.primitives`, `confidence` |
| Harvest E2E | `ibg/morphology_harvest/e2e_spine_runner.py` | `_stage_body_grid`, logs `primitives_count` |

Sandbox (non-authoritative): `vectorizer-sandbox` incubation / `agentic_supervisor` retries — **research-only**, not spine default.

---

## Failure: primitive starvation

| Field | Value |
|-------|--------|
| **Matrix link** | [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) — primitive starvation |
| **Topology link** | [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md) — §11 Primitive extraction |
| **Topology cause** | Contours lose hole/route entities before grid; SMART path skips primitive export |
| **Semantic impact** | CAM-ready body without pickguard/bridge/hole semantics |
| **Runtime visibility** | `primitives_count` in phase3 metadata; descriptor list length — **partial** |
| **fixture_status** | verified (structural) |
| **artifact_path** | `vectorizer_phase3.py` (PrimitiveDetector ~L909+); `body_grid/primitives.py`; `e2e_spine_runner.py` |
| **verification_state** | code paths verified; canonical regression DXF **TBD** |

---

## Failure: slab_body collapse

| Field | Value |
|-------|--------|
| **Matrix link** | slab_body collapse row |
| **Topology cause** | Semantic occupancy / zone classifier collapses to single region (“slab”) |
| **Semantic impact** | Waist, horns, asymmetry lost — morphology appears uniform |
| **Runtime visibility** | `MorphologyDescriptor.missing_regions`, `zone_coverage` — **when wired** |
| **fixture_status** | verified (concept + modules) |
| **artifact_path** | `body_grid/zones.py`, `ZoneClassifier`; sandbox archaeology `extract_body_grid_v*` (external repo) |
| **verification_state** | PENDING / external verification for canonical slab_body DXF fixture |

---

## Failure: grouping fallback ambiguity

| Field | Value |
|-------|--------|
| **Matrix link** | Grouping fallback visibility |
| **Topology cause** | `edge_to_dxf` isolation exception → legacy grouping |
| **Semantic impact** | Contour ownership changes → primitive and body isolation drift |
| **Runtime visibility** | `grouping_telemetry.record_grouping_fallback`, `build_topology_provenance()` |
| **fixture_status** | verified |
| **artifact_path** | `grouping_telemetry.py`; `test_vectorizer_grouping_telemetry.py` |
| **verification_state** | telemetry verified; corpus DXF for regression **TBD** |

---

## Evolving: Les Paul semantic continuity

| Field | Value |
|-------|--------|
| **Registry link** | LINE chaining / Les Paul corpus note |
| **fixture_status** | evolving |
| **artifact_path** | `SPRINTS.md` (Les Paul dimension accuracy notes); handoffs under `docs/archive/` — **no single canonical DXF path in spine** |
| **verification_state** | PENDING / external verification for Wave 1B regression anchor |

---

## Evolving: partial contour ownership

| Field | Value |
|-------|--------|
| **fixture_status** | evolving |
| **artifact_path** | `topology_recovery.ContourCandidate`; `isolate_candidates` — PENDING concrete failure DXF |
| **verification_state** | structural trace only |

---

## Reconstruction survivability

| Signal | Where observed | Interpretation |
|--------|----------------|----------------|
| `near_closed_contours` | `TopologyStats` | Gap closure may mask open topology |
| `gap_distance` | `ContourCandidate` | Small gap → false closure risk |
| `composite_score` | `candidate_scoring` | High score ≠ semantic correctness |
| `body_grid_success` | `E2ESpineResult` | Harvest path succeeded ≠ gate approved |

---

## Preservation actions (1B)

- Cross-link failures in [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md).
- Do not add classifiers or memory writes.
- Future instrumentation wave: primitive survival counters (sandbox-only telemetry).

---

*Research Wave 1B — 2026-05-20*
