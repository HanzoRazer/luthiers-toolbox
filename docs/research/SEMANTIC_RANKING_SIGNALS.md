# Semantic Ranking Signals

**Wave:** 1C  
**Purpose:** Formalize **morphology-aware ranking** — implemented vs proposed vs research-only. No code changes in 1C.

Primary implementation: `services/api/app/instrument_geometry/body/ibg/workflow/candidate_scoring.py` — `ScoringSignals`, `score_candidates()`, `composite_score()`.

---

## Implemented (runtime spine)

| Signal | Type | Weight in `composite_score()` | Notes |
|--------|------|------------------------------|--------|
| `vertical_extent` | Heuristic (normalized 0–1) | 0.15 | Body-scale height |
| `horizontal_distribution` | Heuristic | 0.10 | Mass spread |
| `waist_narrowing` | Topology-derived heuristic | 0.15 | `_detect_waist_narrowing()` |
| `bout_presence` | Topology-derived heuristic | 0.15 | Upper/lower bout evidence |
| `centerline_balance` | Topology-derived heuristic | 0.10 | `_compute_centerline_balance()` |
| `asymmetry_visibility` | Topology-derived heuristic | 0.05 | `_compute_asymmetry()` |
| `not_text_stroke` | Heuristic | 0.15 | Penalize dimension-like strokes |
| `closure_quality` | Topology-derived | 0.15 | Closed vs open contour |

**Output:** `ScoredCandidate.rank_score` → fed to `create_candidate_from_evidence(..., confidence_value=scored.rank_score)` — **ranking confidence, not morphology canon**.

`rejection_flags` on `ScoredCandidate` may disqualify candidates (see module implementation below scoring).

---

## Proposed (research backlog — not implemented)

| Signal | Rationale | Status |
|--------|-----------|--------|
| `primitive_density` | Starvation visible in rank | proposed |
| `loop_integrity` | Fragmentation beyond `closure_quality` | proposed |
| `occupancy_balance` | Anti-slab_body zone balance | proposed |
| `grouping_fallback_penalty` | Down-rank when `grouping_fallback_used` | proposed — needs provenance in pipeline |
| `morphology_descriptor_agreement` | Rank vs `MorphologyDescriptor.variant_match` | proposed |
| `primitive_survival_rate` | DXF primitive count vs grid count | proposed |

---

## Research-only (sandbox / non-authoritative)

| Signal | Source | Label |
|--------|--------|-------|
| ML classifier body class | `vectorizer-sandbox` cognitive paths | non-authoritative · research-only · non-canonical |
| Grid occupancy ML | `extract_body_grid_v*` archaeology | same |
| Agentic supervisor retries | incubation | same |

Must not feed default `IBGIntakeGate` approval without graduation — see [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md).

---

## Signal taxonomy

| Class | Definition |
|-------|------------|
| **Heuristic** | Geometric proxy on contour points |
| **Topology-derived** | Derived from contour shape / closure / bout geometry |
| **Research-only** | Sandbox ML or incubation — not spine default |

---

## Commercial quality link

Weak `waist_narrowing` + strong `vertical_extent` may yield high `rank_score` on **slab-like** contours — commercial risk documented in [MORPHOLOGY_CONTINUITY_EVALUATION.md](MORPHOLOGY_CONTINUITY_EVALUATION.md). Ranking improves **candidate ordering**, not **semantic truth**.

---

## Cross-links

- Ownership: [CONTOUR_OWNERSHIP_ANALYSIS.md](CONTOUR_OWNERSHIP_ANALYSIS.md)
- Review output: [REVIEW_PACKAGE_QUALITY_GUIDE.md](REVIEW_PACKAGE_QUALITY_GUIDE.md)
- Trace: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) stage 4

---

*Research Wave 1C — 2026-05-20*
