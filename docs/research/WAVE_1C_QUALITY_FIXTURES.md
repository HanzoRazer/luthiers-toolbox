# Wave 1C Quality Fixtures

**Wave:** 1C  
**Purpose:** Commercial/artifact-quality overlay on the **1B structural fixture registry** — does not supersede [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) or [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md).

Adds: `expected_morphology`, `visual_failure_impact`, `fabrication_implications`.

---

## Registry relationship

| Layer | Document |
|-------|----------|
| Structural index (canonical) | 1B failure catalog + PRIMITIVE_FLOW tables |
| Commercial interpretation (1C) | This file |

---

## Fixtures

### 1. primitive starvation

| Field | Value |
|-------|--------|
| 1B reference | [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) §1 |
| fixture_status | verified (structural) |
| artifact_path | `vectorizer_phase3.py`; `body_grid/primitives.py`; `e2e_spine_runner.py` |
| verification_state | code paths verified; regression DXF TBD |
| expected_morphology | Recognizable body outline with feature holes/routes/primitives |
| visual_failure_impact | “Empty” pickguard/bridge regions; smooth blob body |
| fabrication_implications | CAM outer profile without semantic feature ops |
| known_collapse_mode | primitive starvation |

---

### 2. slab_body collapse

| Field | Value |
|-------|--------|
| 1B reference | TOPOLOGY_CONTINUITY_FAILURES §2 |
| fixture_status | verified (concept) |
| artifact_path | `body_grid/zones.py`; sandbox grid archaeology (external) |
| verification_state | PENDING / external verification — canonical DXF |
| expected_morphology | Visible waist pinch + distinct upper/lower bouts |
| visual_failure_impact | Single occupied slab; horns/waist absent |
| fabrication_implications | Wrong bracing/zone assumptions if promoted |
| known_collapse_mode | slab_body collapse |

---

### 3. grouping fallback ambiguity

| Field | Value |
|-------|--------|
| 1B reference | TOPOLOGY_CONTINUITY_FAILURES §5 |
| fixture_status | verified |
| artifact_path | `grouping_telemetry.py`; `edge_to_dxf.py`; `test_vectorizer_grouping_telemetry.py` |
| verification_state | telemetry + unit test verified |
| expected_morphology | Stable contour grouping across runs on same input |
| visual_failure_impact | Outline shifts; rank-1 contour changes |
| fabrication_implications | Inconsistent review packages; false regression |
| known_collapse_mode | grouping fallback ambiguity |

---

### 4. partial contour ownership

| Field | Value |
|-------|--------|
| 1B reference | TOPOLOGY_CONTINUITY_FAILURES §6 |
| fixture_status | evolving |
| artifact_path | `ibg_workflow_pipeline.isolate_candidates` |
| verification_state | PENDING / external verification |
| expected_morphology | Full outer body loop owned by rank-1 |
| visual_failure_impact | C-shaped or partial body; wrong aspect ratio |
| fabrication_implications | Under-cut or missing half-body |
| known_collapse_mode | partial contour ownership |

---

### 5. Les Paul continuity

| Field | Value |
|-------|--------|
| 1B reference | PRIMITIVE_FLOW — Les Paul evolving |
| fixture_status | partially verified / evolving |
| artifact_path | `SPRINTS.md` (dimension notes); `docs/archive/` handoffs — no spine golden DXF |
| verification_state | PENDING / external verification |
| expected_morphology | Double-cutaway electric; waist; horn asymmetry |
| visual_failure_impact | Les Paul reads as generic slab or TE-shaped block |
| fabrication_implications | Wrong body template for operator review |
| known_collapse_mode | composite (starvation / grouping / scoring) |

---

### 6. contour fragmentation (1C addition)

| Field | Value |
|-------|--------|
| 1B reference | TOPOLOGY_CONTINUITY_FAILURES §3 |
| fixture_status | evolving |
| artifact_path | `topology_recovery.py` |
| verification_state | PENDING / external verification |
| expected_morphology | Single closed outer fabricatable loop |
| visual_failure_impact | Broken outline gaps in preview |
| fabrication_implications | Non-manifold or open toolpaths |
| known_collapse_mode | loop fragmentation |

---

### 7. low morphology confidence (1C addition)

| Field | Value |
|-------|--------|
| 1B reference | MORPHOLOGY_INTERPRETATION_BOUNDARY — confidence tracks |
| fixture_status | verified (policy) |
| artifact_path | `MorphologyDescriptor.confidence`; `ScoringSignals.composite_score` |
| verification_state | fields exist; correlation fixture TBD |
| expected_morphology | Descriptor confidence aligns with visual recognizability |
| visual_failure_impact | High score, unrecognizable shape |
| fabrication_implications | Reviewer distrust; gate may still block |
| known_collapse_mode | confidence collapse |

---

## Sandbox references (non-authoritative)

Eval corpora and grid archaeology in `vectorizer-sandbox` may host future golden files — cite with `vectorizer-sandbox @ pending tag` only; not spine defaults.

---

## Cross-links

- Quality spine: [SEMANTIC_ARTIFACT_QUALITY.md](SEMANTIC_ARTIFACT_QUALITY.md)
- Trace: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md)

---

*Research Wave 1C — 2026-05-20*
