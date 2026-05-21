# Primitive Survivability Analysis

**Wave:** 1C  
**Purpose:** Connect **primitive starvation** to **visible morphology collapse** — extends [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) with commercial/artifact lens.

---

## Survivability chain

```text
vectorizer primitives (phase3 PrimitiveDetector)
    → DXF feature entities
    → contour topology (may drop feature-scale geometry)
    → BodyEvidence segments
    → MorphologyPrimitive[] (body_grid)
    → MorphologyDescriptor.primitives
    → (review package: NOT listed per-primitive today)
```

When primitives vanish, reviewers see a **smooth outer outline** but lose pickguard, bridge, waist definition, and cutaway semantics — **body identity collapse** in fabrication prep terms.

---

## Morphology features vs survivability

| Feature | Primitive / signal dependency | Visible collapse |
|---------|------------------------------|------------------|
| **Bout survivability** | `bout_presence` scoring; zone lower/upper | Single blob outline |
| **Waist preservation** | `waist_narrowing`; waist zone coverage | Slab-like rectangle |
| **Horn continuity** | Asymmetry + upper bout zones | Rounded-single-cut reads as symmetric block |
| **Centerline integrity** | `centerline_balance`; `CenterlineDescriptor` | Left/right flank incoherent |
| **Cutaway preservation** | Feature-scale primitives | Missing cutaway in CAM semantics |

---

## Primitive starvation (1B → 1C)

| Field | Value |
|-------|--------|
| Structural registry | [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) §1 |
| Spine modules | `vectorizer_phase3.py` (`PrimitiveDetector`, `enable_primitives`); `body_grid/primitives.py` |
| Commercial impact | Fabrication-oriented semantics missing while outline looks “complete” |
| Review visibility | **Low** — `ReviewPackage` has no `primitives_count` field |
| fixture overlay | [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md) |

---

## Slab_body link

Occupancy collapse → few meaningful zones → descriptor confidence may remain moderate while shape is wrong — **confidence ≠ canonization**. See [MORPHOLOGY_CONTINUITY_EVALUATION.md](MORPHOLOGY_CONTINUITY_EVALUATION.md).

---

## Reconstruction survivability

| Signal | Module | Quality meaning |
|--------|--------|-----------------|
| `closure_quality` | `ScoringSignals` | Topology trust for ranking |
| `gap_distance` | `ContourCandidate` | Near-closed may hide fragmentation |
| `primitives_count` | phase3 / E2E harvest logs | Partial visibility — not in review JSON |

---

## Deferred instrumentation (non-authoritative, sandbox-future)

- Primitive survival rate DXF→descriptor
- Per-zone primitive heatmaps (Step 8 — **not in 1C**)

---

*Research Wave 1C — 2026-05-20*
