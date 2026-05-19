# Blueprint Vectorizer v3.6 Audit — April 16-21, 2026

Generated: 2026-04-21

---

## Executive Summary

The v3.6 build period focused on morphological gap closing restoration (commit 3db07c62) and Phase 6B polyline output (reverted). The key deliverable was restoring the March 6 breakthrough capability in enhanced mode.

**Critical Finding:** The blueprint reader vectorizer (`services/blueprint-import/`) borrowed core algorithms from the photo-vectorizer (`services/photo-vectorizer/`), not the reverse. The photo-vectorizer was the source of the "secret sauce" — morphological gap closing via `cv2.MORPH_CLOSE`.

---

## Part 1: Lineage Audit — Photo-Vectorizer Origin (March-April 2026)

### March 6-9, 2026: Photo Vectorizer V2 Breakthrough

| Commit | Date | Summary |
|--------|------|---------|
| 94d90243 | Mar 9, 02:45 | **Photo Vectorizer V2** — 12-stage pipeline, 1,222 lines |
| 94e40951 | Mar 9 | docs: add photo-vectorizer developer handoff |
| 0b5024db | Mar 9 | feat: add grid zone re-classification |

The "March 6 breakthrough" refers to the 12-stage pipeline in `photo_vectorizer_v2.py`:

| Stage | Function |
|-------|----------|
| 1 | EXIF DPI detection |
| 2 | Input classification |
| 3 | Perspective correction |
| 4 | Background removal (GrabCut/rembg/SAM/threshold) |
| 5 | **Multi-method edge detection (Canny+Sobel+Laplacian fusion)** |
| 6 | Reference object detection |
| 7 | Scale calibration |
| 8 | Contour assembly with hierarchy |
| 9 | Feature classification |
| 10-12 | SVG/DXF/JSON export |

**Key capability:** Morphological closing (`cv2.MORPH_CLOSE`) bridging pixel-level gaps.

### April 1-2, 2026: Photo-Vectorizer Expansion

| Commit | Date/Time | Summary |
|--------|-----------|---------|
| 9417fd9b | Apr 1, 01:08 | **edge_to_dxf.py created** (414 lines) — new implementation |
| 14f68241 | Apr 1, 10:03 | light_line_body_extractor.py added (550 lines) |
| 4f1a87e9 | Apr 1, 13:26 | Integrated blueprint + silhouette extractors |
| f573c4f6 | Apr 2, 20:38 | BlueprintLab UI + vectorizer improvements |

**Finding:** `edge_to_dxf.py` was authored fresh on April 1, 2026. It contains the morphological closing implementation that was later referenced by blueprint-import.

### Directory Comparison

| Directory | Core Files | Origin |
|-----------|-----------|--------|
| `services/photo-vectorizer/` | photo_vectorizer_v2.py, edge_to_dxf.py, light_line_body_extractor.py | **SOURCE** (March 9) |
| `services/blueprint-import/` | vectorizer_phase2.py, vectorizer_phase3.py, dxf_compat.py | DERIVED (April+) |

The blueprint-import vectorizer phases reference patterns from photo-vectorizer but use different class structures and integration points.

---

## Part 2: v3.6 Build Period (April 16-21, 2026)

### Benchmark File Metrics

| File | Size | LINE Entities | gap_close_size | Timestamp |
|------|------|---------------|----------------|-----------|
| cuatro_gapclose0.dxf | 45 MB | 435,302 | 0 (disabled) | Apr 20 16:26 |
| cuatro_gapclose3.dxf | 25 MB | 244,349 | 3 | Apr 20 16:24 |
| cuatro_gapclose5.dxf | 23 MB | 218,214 | 5 | Apr 20 16:26 |
| cuatro_puertoriqueno_gapclose7.dxf | 21 MB | 204,125 | 7 (default) | Apr 20 15:26 |
| gibson_melody_maker_gapclose7.dxf | 39 MB | 266,359 | 7 (default) | Apr 20 15:27 |

**Key observation:** Larger `gap_close_size` = fewer but more connected contours = smaller file size. The 7px kernel produces optimal balance (March 6 proven value).

### Commits in Range (22 total)

| Commit | Summary |
|--------|---------|
| **3db07c62** | **fix(vectorizer): restore morphological gap closing in enhanced mode** |
| d3c9c97d | docs: add code snapshots at each stage to feedback loop handoff |
| 862e833f | docs: add Feedback Loop System developer handoff |
| ab6f7632 | feat(orchestrator): add mode=enhanced for multi-scale extraction |
| 15489000 | fix(api): wire spec_name to blueprint routes |
| d9435834 | feat(orchestrator): wire spec_name parameter for scale correction |
| 0df259ed | feat(layer): add apply_scale_correction for spec-based body scaling |
| 32f8e599 | refactor(layer): rename BODY layer to BODY_OUTLINE |
| 814be53b | Revert "feat(vectorizer): implement phase 6b confidence-gated body polyline output" |

### Gap Closing Fix (3db07c62)

**Files changed:**
- `services/photo-vectorizer/edge_to_dxf.py` — Added `cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)`
- `services/api/app/services/blueprint_extract.py` — Wired `gap_close_size` parameter
- `services/api/app/services/blueprint_orchestrator.py` — Added to `process_file()` signature

**Implementation** (`edge_to_dxf.py:1529-1532`):
```python
if gap_close_size > 0:
    kernel = np.ones((gap_close_size, gap_close_size), np.uint8)
    combined_edges = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
```

---

## Part 3: Vectorizer Schema / Blueprint Orchestrator Architecture

### Pipeline Flow

```
POST /api/blueprint/vectorize
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                 BlueprintOrchestrator.process_file()        │
│                                                             │
│  ┌─────────────────┐                                        │
│  │ CleanupMode     │                                        │
│  │ ─────────────── │                                        │
│  │ ENHANCED        │ ──► Multi-scale Canny + MORPH_CLOSE    │
│  │ LAYERED_DUAL_   │ ──► Pass A + Pass B + Layer Builder    │
│  │   PASS          │                                        │
│  │ REFINED         │ ──► Standard extraction + cleanup      │
│  │ RESTORED_       │ ──► RETR_LIST (no hierarchy)           │
│  │   BASELINE      │                                        │
│  └─────────────────┘                                        │
│                                                             │
│  Stages:                                                    │
│    1. image_extract (PDF→PNG if needed)                     │
│    2. edge_extraction (Canny or multi-scale)                │
│    3. cleanup (filtering/gap closing)                       │
│    4. encode (DXF→base64)                                   │
│    5. validation (SVG/DXF sanity)                           │
│    6. recommendation (accept/review/reject)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
   BlueprintResult (ok, svg, dxf, metrics, debug)
```

### Enhanced Mode (CleanupMode.ENHANCED)

```python
extract_blueprint_enhanced(
    source_path,
    output_path,
    target_height_mm=500.0,
    gap_close_size=7,      # ← March 6 breakthrough value
)
```

Multi-scale Canny thresholds: 30/100, 50/150, 80/200 fused into single edge mask.

### Layered Dual-Pass Mode (CleanupMode.LAYERED_DUAL_PASS)

| Pass | Method | Output |
|------|--------|--------|
| Pass A | `extract_entities_simple()` — Adaptive threshold + RETR_LIST | BODY, AUX_VIEWS contours |
| Pass B | `extract_annotations()` — Lighter thresholds | ANNOTATION, TITLE_BLOCK |

**Layers** (from `layer_builder.py`):
- `BODY_OUTLINE` — Primary instrument outline
- `AUX_VIEWS` — Secondary structural clusters
- `ANNOTATION` — Text, dimensions, labels
- `TITLE_BLOCK` — Dense annotation cluster
- `PAGE_FRAME` — Page border geometry

### Result Schema

```python
@dataclass
class BlueprintResult:
    ok: bool                    # True only when accept
    processed: bool = True
    stage: str                  # "complete" | "extraction" | "recommendation"
    error: str
    warnings: list[str]
    dimensions: Dimensions      # width_mm, height_mm
    svg: SVGArtifact           # present, content, path_count
    dxf: DXFArtifact           # present, base64, entity_count, closed_contours
    selection: SelectionResult
    recommendation: Recommendation
    metrics: dict
    debug: dict
```

---

## Part 4: Phase 6B Status (April 16 Session)

**Built but reverted** (814be53b):
- `body_geometry_repair.py` — 786 lines, polyline run detection
- Feature flags: `ENABLE_BODY_REPAIR`, `ENABLE_POLYLINE_OUTPUT` (default OFF)
- Produced `dreadnought_phase6b_FINAL.dxf` with 2,038 POLYLINE entities

**Reason for revert:** Reserved for staging validation before production.

See [session_audit_april16_2026_phase6b.md](session_audit_april16_2026_phase6b.md) for full Phase 6B details.

---

## Part 5: Frontend Work (April 16-21)

### April 19: Vectorizer Artifacts Helper

| Commit | Summary |
|--------|---------|
| 38a3c020 | feat: add utility scripts and vectorizer artifacts helper |

**Files added:**
- `packages/client/src/utils/vectorizerArtifacts.ts` (318 lines)
- `scripts/run_frontend_mode_benchmark.py` (177 lines)
- `scripts/trace_live_path.py` (231 lines)

**vectorizerArtifacts.ts** — Centralized helpers for consuming canonical vectorizer responses:

```typescript
// Types defined
VectorizerArtifacts    // svg.content, dxf.base64, entity_count
VectorizerDimensions   // width_mm, height_mm, spec_match
VectorizerSelection    // candidate_count, selection_score, winner_margin
VectorizerRecommendation // action: accept|review|reject, confidence
VectorizerMetrics      // processing_ms, scale_source, bg_method

// Key functions
decodeBase64ToBlob()   // DXF download from base64
getDimensions()        // Extract canonical dimensions
getStatus()            // Parse ok/processed/stage into UI state
```

### Body Outline Editor Timeline (Context)

| Date | Commit | Feature |
|------|--------|---------|
| Apr 5 | 73b2dcfd | Initial release — precision sandbox for lutherie outlines |
| Apr 5 | 50f7242d-b98f56d8 | TDZ fixes, smooth() compatibility |
| Apr 6 | ca70fd24 | Simplify + Smooth All buttons |
| Apr 6 | c765f160 | Dimension tool + symmetry mirror toggle |
| Apr 8 | 8bfe36c9 | Moved to hostinger/ tracked directory |

The Body Outline Editor validates vectorizer output quality — users import DXF/SVG artifacts and manually correct/refine contours.

---

## Part 6: DXF Output Corpus (March 20 - April 1)

From `docs/dxf_files_march20_april1_2026.md`:

- ~104 DXF files generated during this period
- **Cuatro reference files:** 10 main + 10 primitives + regenerated_v3 + simple_extract
- **Carlos Jumbo:** 25 DXF variants (views, enhanced, all-edges, validated)
- **Smart Guitar:** v2 complete → v3 from spec → v6 smoothed
- **Gibson Explorer:** body cavities, phase3, primitives

---

## Part 7: Test Schemes Used

| Test | Description |
|------|-------------|
| Gap close sweep | Test files generated with `gap_close_size` = 0, 3, 5, 7 |
| March 6 baseline comparison | Cuatro output compared to 16MB reference |
| Ratio validation | Output 1.34x larger than March 6 = success threshold |

---

## Summary

1. **Lineage confirmed:** Photo-vectorizer (March 9, 2026) is the source; blueprint-import is derived
2. **Gap closing regression identified and fixed** (3db07c62)
3. **Frontend utilities** (vectorizerArtifacts.ts) align with canonical backend schema
4. **Body Outline Editor** provides validation workflow for vectorizer artifacts
5. **DXF corpus** (104 files) establishes baseline quality targets from March 6 breakthrough
6. **Phase 6B** built but reverted pending staging validation

---

## ADR Reference

See SPRINTS.md Architectural Decisions Log entry for 2026-04-20:

> Blueprint vectorizer ceiling declaration (2026-04-16) reversed. v3.6 restored morphological gap closing capability from vectorizer_phase2.py (commit 3db07c62). Benchmark output exceeded the March 6 baseline.
