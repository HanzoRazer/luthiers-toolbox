# Morphology Continuity Evaluation

**Wave:** 1C  
**Purpose:** Whether **recognizable body identity** survives extraction — evaluation framing, not autonomous promotion.

Cross-links: [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md), [PRIMITIVE_SURVIVABILITY_ANALYSIS.md](PRIMITIVE_SURVIVABILITY_ANALYSIS.md).

---

## Evaluation question

```text
After extraction and ranking, would a skilled reviewer
still recognize the instrument family and body shape
without guessing?
```

No numeric pass/fail threshold in 1C — structural understanding only.

---

## Continuity targets

| Target | Expected morphology (when healthy) | 1C status |
|--------|-----------------------------------|-----------|
| **Les Paul continuity** | Double-cutaway, waist, horn asymmetry | **partially verified / evolving** — `SPRINTS.md` dimension accuracy notes; no single canonical spine DXF |
| **slab_body collapse** | Distinct waist + bouts | **verified concept** — fixture DXF TBD ([WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md)) |
| **rounded-single-cut preservation** | Single cutaway + bout curve | evolving — registry + scoring heuristics only |
| **acoustic waist continuity** | Pinched waist, lower bout | evolving — see [gibson_l37_1941_significance.md](gibson_l37_1941_significance.md) as canon context, not extraction fixture |
| **asymmetry survivability** | `asymmetry_visibility` signal + `AsymmetryDescriptor` | implemented signal; full solver consumption PENDING / external verification |

---

## Signals used today (not canonization)

| Source | Field | Role |
|--------|-------|------|
| Workflow scoring | `ScoringSignals.asymmetry_visibility` | Rank only |
| body_grid | `MorphologyDescriptor.confidence` | Advisory |
| body_grid | `variant_match` / `BodyMorphologyClass` | Heuristic class label |
| Candidate wrap | `rank_score` → `create_heuristic_confidence` | Declared, review-gated |

Sandbox ML confidence: **non-authoritative · research-only · non-canonical** (`vectorizer-sandbox`).

---

## Slab_body collapse (commercial)

**Visual:** body reads as one occupied region.  
**Semantic:** zones merge; `missing_regions` may under-report if classifier not wired.  
**Fabrication:** outer outline may CAM while internal semantics wrong.

Registry: 1B §2; overlay: 1C fixtures.

---

## Les Paul (do not overstate)

| Field | Value |
|-------|--------|
| fixture_status | partially verified / evolving |
| artifact_path | `SPRINTS.md` (Les Paul W/H accuracy); handoffs in `docs/archive/` — no committed golden DXF in workflow output path verified |
| verification_state | PENDING / external verification for extraction continuity corpus |
| expected_morphology | Double-cutaway electric, waist visible, horn offset |
| known_collapse_mode | LINE chaining / grouping fallback / primitive starvation (any may apply) |

---

## Gibson L-37 (context only)

Archtop / acoustic research canon — supports **acoustic waist continuity** discussion, not a Wave 1C regression fixture unless measurement artifacts are later linked.

---

## Improvement direction (docs-only)

1. Align rank-1 contour with morphology descriptor on same `BodyEvidence` instance.  
2. Expose descriptor `missing_regions` + `zone_coverage` in review package (desired — [REVIEW_PACKAGE_QUALITY_GUIDE.md](REVIEW_PACKAGE_QUALITY_GUIDE.md)).  
3. Canonical fixtures in [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md).

---

*Research Wave 1C — 2026-05-20*
