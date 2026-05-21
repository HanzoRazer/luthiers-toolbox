# Review Package Quality Guide

**Wave:** 1C  
**Purpose:** What reviewers **must** see for **reviewable semantic geometry** — separates current runtime from desired visibility.

Implementation: `ibg/workflow/review_package.py` — `ReviewPackage`, `CandidateSummary`, `emit_review_package()`.  
Output dir default: `morphology_harvest/outputs/workflow_1a/review_packages/{package_id}/`.

---

## Goal

```text
reviewable semantic geometry
```

**Not:** opaque machine inference or implied overlays that do not exist.

---

## Current runtime visibility

What `ReviewPackage.to_dict()` / JSON on disk includes **today**:

| Field | Content | Quality utility |
|-------|---------|-----------------|
| `package_id`, `created_at` | Run identity | Audit |
| `artifact_paths`, `artifact_hashes` | Preserved DXF/SVG | Coherence |
| `candidate_summaries[]` | Per-candidate rank, score, closure, area, perimeter, flags | Compare candidates |
| `candidate_summaries[].gate_decision` | `is_valid`, `rejections[]` | Authority boundary |
| `candidate_summaries[].authority_state` | e.g. advisory | Canonization guard |
| `topology_stats` | open/closed/near_closed entity counts | Continuity snapshot |
| `provenance` | From first candidate | Lineage (partial) |
| `confidence_declaration` | Typed confidence from first candidate | Explain declared confidence |
| `gate_decision` | Aggregate pass/fail counts | Package-level gate |
| `review_required` | Always true in 1A pipeline | Human loop |
| `review_notes_placeholder` | Empty string | Manual notes |
| `preview_paths` | Optional dict — **often empty** | Visual preview |

**CandidateSummary does NOT include:** primitive list, zone map, grouping fallback reason, morphology class, waist metrics, or contour ownership graph.

---

## Desired future reviewer visibility (not implemented — 1C documents only)

| Artifact | Purpose | Authority |
|----------|---------|-----------|
| Semantic overlays (SVG/DXF layers) | See waist/bouts on rank-1 | Review-only |
| Primitive annotations | Starvation visible | Non-authoritative |
| Continuity diagram | Gap tiers, near-closed | Telemetry |
| Confidence decomposition | Which signals drove rank | Explainability |
| Grouping fallback echo | Correlate vectorizer → package | Provenance |
| MorphologyDescriptor summary | Zones, `missing_regions` | Advisory |
| Side-by-side candidate renders | Compare rank 1 vs 2 | Sandbox-future |

Step 8 visualization remains **deferred**, sandbox-contained, non-authoritative.

---

## What reviewers must be able to answer (with current package)

1. Which candidate is rank 1 and what was the score?  
2. Is the top contour closed? What is area/perimeter?  
3. Did intake gate reject candidates — and why (`rejections`)?  
4. What topology stats suggest fragmentation?  
5. Where are preserved artifact files?

**Harder today:** Why primitives are missing; whether grouping fallback fired; whether morphology class matches outline.

---

## Worked package shape (grounded)

Example fields a reviewer sees for each candidate (from `CandidateSummary.to_dict()`):

```json
{
  "candidate_id": "...",
  "rank": 1,
  "rank_score": 0.72,
  "is_closed": true,
  "area_mm2": 45000.0,
  "perimeter_mm": 1200.0,
  "rejection_flags": [],
  "authority_state": "advisory_candidate",
  "review_required": true,
  "gate_decision": { "is_valid": false, "rejections": ["..."] }
}
```

Plus package-level `topology_stats` and `gate_decision.all_valid`. Full narrative: [SEMANTIC_ARTIFACT_QUALITY.md](SEMANTIC_ARTIFACT_QUALITY.md#worked-example--grouping-fallback--review-package-grounded).

---

## Adapter path vs workflow path

| Path | Entry | Review artifact |
|------|-------|-----------------|
| Workflow 1A | `IBGWorkflowPipeline.run()` | `{package_id}_review_package.json` |
| Harvest adapter | `ArtifactBodyEvidenceAdapter` | Candidate + gate — package may differ |

Reviewers comparing harvest-only runs to workflow packages should treat paths as **related but not identical** — PENDING unified run_id.

---

## Cross-links

- Ranking: [SEMANTIC_RANKING_SIGNALS.md](SEMANTIC_RANKING_SIGNALS.md)
- Observability gaps: [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md)
- Fixtures: [WAVE_1C_QUALITY_FIXTURES.md](WAVE_1C_QUALITY_FIXTURES.md)

---

*Research Wave 1C — 2026-05-20*
