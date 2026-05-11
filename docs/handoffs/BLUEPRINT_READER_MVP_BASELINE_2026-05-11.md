# Blueprint Reader MVP Baseline

**Date:** 2026-05-11  
**Status:** COMMERCIALLY VIABLE — Development Frozen  
**Classification:** Production Baseline

---

## Executive Summary

The Blueprint Reader vectorizer has reached a commercially viable production state and is now frozen. This document defines the MVP baseline for future reference, maintenance, or potential reactivation.

The system extracts instrument body outlines from PDF blueprints with ±3% to ±20% dimensional accuracy — sufficient for starter templates requiring manual verification before CNC work.

---

## 1. Production Entry Point

### API Endpoint

```
POST /api/blueprint/vectorize
```

### Files

| Component | Path |
|-----------|------|
| Router | `services/api/app/routers/blueprint/vectorize_router.py` |
| Orchestrator | `services/api/app/services/blueprint_orchestrator.py` |
| Extraction | `services/api/app/services/blueprint_extract.py` |
| Cleanup | `services/api/app/services/blueprint_clean.py` |
| Recommendation | `services/api/app/services/contour_recommendation.py` |
| Layer Builder | `services/api/app/services/layer_builder.py` |

### Request Schema

```
POST /api/blueprint/vectorize
Content-Type: multipart/form-data

file: <PDF or image>
page_num: 0
target_height_mm: 500.0
min_contour_length_mm: 100.0
close_gaps_mm: 1.0
debug: false
mode: "refined"
spec_name: "dreadnought"  (optional)
reinsert_text: false
```

### Response Schema

```json
{
  "ok": true,
  "processed": true,
  "stage": "complete",
  "artifacts": {
    "svg": { "present": true, "content": "...", "path_count": 3 },
    "dxf": { "present": true, "base64": "...", "entity_count": 1247 }
  },
  "dimensions": { "width_mm": 381.0, "height_mm": 520.0 },
  "selection": {
    "candidate_count": 12,
    "selected_index": 3,
    "selection_score": 0.72,
    "winner_margin": 0.15
  },
  "recommendation": {
    "action": "review",
    "confidence": 0.72,
    "reasons": ["Body-like contour selected"]
  }
}
```

---

## 2. Production Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `refined` | Hierarchy-based filtering with grouping | Default — best for clean blueprints |
| `baseline` | Simpler pre-grouping behavior | Fallback for complex layouts |
| `restored_baseline` | Historical 86c49526 behavior | Recovery mode for regression cases |
| `layered_dual_pass` | Classified layers (BODY, BRACING, etc.) | Multi-layer extraction |
| `enhanced` | Full edge detail (1M+ entities) | Maximum fidelity, requires cleanup |
| `cam_ready_r2000` | R2000 LWPOLYLINE output | Paid tier only (requires auth) |

---

## 3. Accuracy Baseline

Validated against three Tier 1 reference instruments at 400 DPI:

| Instrument | Body Type | Width Error | Height Error | Rating |
|------------|-----------|-------------|--------------|--------|
| Dreadnought | Acoustic steel | 7.1% | 2.5% | Excellent |
| Gibson Les Paul 59 | Electric solid | 16.5% | 19.7% | Acceptable |
| Cuatro Puertorriqueño | Latin American | 2.6% | 2.6% | Excellent |

**Typical range:** ±3% to ±20% of true body dimensions

**Accuracy disclaimer:** `docs/VECTORIZER_ACCURACY.md`

---

## 4. Defining Commits

| Commit | Date | Description | Role |
|--------|------|-------------|------|
| `86c49526` | 2026-04-11 | fix(blueprint): sync orchestrator | **Ground truth baseline** |
| `e2b4ad66` | 2026-04-12 | feat(vectorizer): multi-mode architecture | Mode system |
| `e3fb4792` | 2026-04-13 | fix(vectorizer): restore historical baseline | Recovery path |
| `757370cf` | 2026-04-14 | fix(blueprint): sync orchestrator and router | Production sync |
| `09a21af1` | 2026-04-28 | feat(dxf): implement R2000 dual-format | Paid tier mode |

---

## 5. Deployment

| Location | URL | Purpose |
|----------|-----|---------|
| Frontend | `HanzoRazer/blueprint-reader` (Hostinger) | Production UI |
| Backend | Railway (`luthiers-toolbox-production`) | API service |
| Frontend dev | `hostinger/blueprint-reader.html` | Development copy |

---

## 6. What Was NOT Implemented

The following CLAUDE.md-approved features were never built:

| Feature | Status | Reason |
|---------|--------|--------|
| Loop 2: Cross-Image Learning | NOT_IMPLEMENTED | MVP reached before implementation |
| Loop 3: User Correction Retraining | ORPHANED | FeedbackSystem exists but unwired |
| AGE Integration | NOT_IMPLEMENTED | Never built |
| Segmentation-First Extraction | NOT_STARTED | Edge detection sufficient for MVP |

**Audit reference:** `docs/handoffs/VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md`

---

## 7. Related Documentation

### Architecture

| Document | Path |
|----------|------|
| Vectorizer Architecture | `docs/BLUEPRINT_VECTORIZER_ARCHITECTURE.md` |
| Recovery Baseline | `docs/archive/2026/status/RECOVERY_BASELINE.md` |
| Mode Comparison | `docs/VECTORIZER_MODE_COMPARISON.md` |
| Accuracy Disclaimer | `docs/VECTORIZER_ACCURACY.md` |

### Audits

| Document | Path |
|----------|------|
| Pipeline Regression | `docs/audit/blueprint_pipeline_regression_2026-04-26.md` |
| Vectorizer Geometry Audit | `docs/handoffs/VECTORIZER_GEOMETRY_AUDIT_HANDOFF_2026-05-11.md` |
| DXF Compliance Closeout | `docs/handoffs/VECTOR_1A_DXF_COMPLIANCE_CLOSEOUT.md` |

### Handoffs

| Document | Path |
|----------|------|
| Pipeline Handoff | `docs/handoffs/VECTORIZER_PIPELINE_HANDOFF.md` |
| Edge Detection Strategy | `docs/handoffs/EDGE_DETECTION_STRATEGY_HANDOFF.md` |
| Thin Stroke PDF | `docs/handoffs/THIN_STROKE_PDF_HANDOFF.md` |

---

## 8. Test Coverage

| Test File | Purpose |
|-----------|---------|
| `tests/test_blueprint_endpoint_smoke.py` | Endpoint existence verification |
| `tests/test_text_masking.py` | Text preprocessing |
| `tests/test_text_masking_regression.py` | Regression prevention |
| `tests/test_text_reinsertion.py` | Text layer reinsertion |

---

## 9. Known Limitations

1. **Complex layouts** — Multi-view blueprints with annotations produce higher error margins
2. **Thin-stroke PDFs** — Require `close_gaps_mm` tuning or `enhanced` mode
3. **Scale detection** — Falls back to spec-based inference without `ANTHROPIC_API_KEY`
4. **Electric guitars** — Higher error (16-20%) due to layout complexity

---

## 10. Reactivation Guidance

If development resumes:

1. **Start from `restored_baseline` mode** — Proven stable, permissive extraction
2. **Do not re-implement filtering early** — Root cause of 2026-04-12 regression
3. **Implement Loop 1 first** — Scale validation gate exists but lacks retry logic
4. **Loop 2 requires dedicated sprint** — See VECTOR-1B audit for scope
5. **Test against Melody Maker PDF** — Primary regression indicator

---

## 11. Ownership

| Role | Assignment |
|------|------------|
| Product | Production Shop |
| Maintenance | Frozen (no active development) |
| Reactivation authority | Ross (explicit request required) |

---

*MVP baseline frozen as of 2026-05-11. No further development without explicit reactivation.*
