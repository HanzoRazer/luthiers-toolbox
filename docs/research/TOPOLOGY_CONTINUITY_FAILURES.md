# Topology Continuity Failures

**Wave:** 1B  
**Purpose:** Indexed catalog of **continuity breaks** — extends [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md) and [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) without duplicating full narratives.

Each entry includes: `fixture_status`, `artifact_path`, `verification_state`.

---

## Catalog

### 1. Primitive starvation

| Field | Value |
|-------|--------|
| failure_mode | Holes/routes/primitives absent after extraction→grid |
| origin_system | `vectorizer_phase3` SMART path; `body_grid` PrimitiveDetector |
| topology_cause | Contour fragmentation or primitive export disabled |
| semantic_impact | CAM body without semantic feature regions |
| runtime_visibility | `primitives_count` (partial) |
| known_mitigations | Enable primitives on SMART; monitor descriptor lists |
| research_status | structural — regression fixture TBD |
| fixture_status | verified |
| artifact_path | See [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) |
| verification_state | code verified; DXF fixture TBD |

---

### 2. slab_body collapse

| Field | Value |
|-------|--------|
| failure_mode | Multi-zone body collapses to single occupancy region |
| origin_system | Wave C grid archaeology; `body_grid` zones |
| topology_cause | Semantic occupancy mis-classification |
| semantic_impact | Waist/horn/asymmetry lost |
| runtime_visibility | `zone_coverage`, `missing_regions` (when populated) |
| known_mitigations | Keep grid R&D in sandbox; do not merge blindly |
| research_status | active documentation |
| fixture_status | verified (concept) |
| artifact_path | `body_grid/zones.py`; sandbox `extract_body_grid_v*` (external) |
| verification_state | PENDING / external verification — canonical slab_body DXF |

---

### 3. Loop fragmentation

| Field | Value |
|-------|--------|
| failure_mode | Open chains where closed body expected |
| origin_system | `topology_recovery.recover_topology`, `_chain_segments` |
| topology_cause | Endpoint mismatch; entity type mix |
| semantic_impact | Candidate isolation selects wrong region |
| runtime_visibility | `TopologyStats.open_contours` |
| known_mitigations | Arc recon tiers; gap closure registry ideas |
| research_status | indexed |
| fixture_status | evolving |
| artifact_path | `topology_recovery.py` |
| verification_state | PENDING / external verification — golden open-chain DXF |

---

### 4. False contour ownership

| Field | Value |
|-------|--------|
| failure_mode | Non-body contour scored as primary candidate |
| origin_system | `isolate_candidates`, `candidate_scoring` |
| topology_cause | Sheet layout / text geometry grouped with body |
| semantic_impact | BodyEvidence describes wrong region |
| runtime_visibility | Ranked candidate list in pipeline result — **partial** |
| known_mitigations | Grouping telemetry; REFINED vs V2_RAW mode discipline |
| research_status | evolving |
| fixture_status | evolving |
| artifact_path | `ibg_workflow_pipeline.isolate_candidates` |
| verification_state | PENDING / external verification |

---

### 5. Grouping fallback ambiguity

| Field | Value |
|-------|--------|
| failure_mode | Legacy isolation used after grouping exception |
| origin_system | `edge_to_dxf` + `grouping_telemetry` |
| topology_cause | `record_grouping_fallback(reason=...)` paths |
| semantic_impact | Topology drift vs prior run; primitive starvation downstream |
| runtime_visibility | `grouping_fallback_total`, `build_topology_provenance()` |
| known_mitigations | PR-2 telemetry; never debug-only |
| research_status | **verified example** in 1B |
| fixture_status | verified |
| artifact_path | `services/photo-vectorizer/grouping_telemetry.py`; `test_vectorizer_grouping_telemetry.py` |
| verification_state | telemetry + test verified |

---

### 6. Partial body isolation

| Field | Value |
|-------|--------|
| failure_mode | Only subset of body contour recovered |
| origin_system | topology recovery + scoring |
| topology_cause | Near-closed treated as closed incorrectly |
| semantic_impact | Under-complete BodyEvidence |
| runtime_visibility | `gap_distance`, `area_mm2` on candidates |
| known_mitigations | Gap closure tiers (registry §4) |
| research_status | indexed |
| fixture_status | evolving |
| artifact_path | `ContourCandidate` fields in `topology_recovery.py` |
| verification_state | PENDING / external verification |

---

### 7. Confidence collapse

| Field | Value |
|-------|--------|
| failure_mode | High confidence with low topological legitimacy |
| origin_system | scoring + descriptor + sandbox ML |
| topology_cause | Influence without continuity |
| semantic_impact | False promotion risk if gate bypassed |
| runtime_visibility | Separate confidence tracks — see [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md) |
| known_mitigations | `IBGIntakeGate`; constitutional candidate wrapper |
| research_status | constitutional — documented |
| fixture_status | verified (policy) |
| artifact_path | `body_evidence_candidate.py`, `ibg_intake_gate.py` |
| verification_state | policy verified; multi-signal collapse fixture TBD |

---

## Priority fixtures (Wave 1B)

| Fixture | fixture_status | Notes |
|---------|----------------|--------|
| Les Paul semantic continuity | evolving | See PRIMITIVE_FLOW_ANALYSIS |
| slab_body | verified concept / TBD DXF | |
| primitive starvation | verified structural | |
| grouping fallback | verified | |
| partial contour ownership | evolving | |

---

## Related

- Trace: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md)
- Questions: [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md)

---

*Research Wave 1B — 2026-05-20*
