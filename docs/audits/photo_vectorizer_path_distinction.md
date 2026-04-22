# Photo Vectorizer Path Distinction

**Date:** 2026-04-21
**Purpose:** Document the extraction paths in `photo_vectorizer_v2.py` to clarify which code is Live vs Suspended

---

## File Versioning Note

The file is named `photo_vectorizer_v2.py` but the header declares "Photo Vectorizer v3.0".

- **v2** = file naming convention (vs v1 which doesn't exist in repo)
- **v3.0** = internal feature version (added AI path, 4-stage pipeline)

References to "v3" in audit documents refer to these v3.0 internal features.

---

## Extraction Paths

`PhotoVectorizerV2.extract()` routes to different paths based on `source_type` parameter:

### 1. Blueprint Path — LIVE

**Entry:** `source_type="blueprint"`
**Implementation:** `_extract_blueprint_path()` → `light_line_body_extractor.py`
**Status:** Live — produces 85-90% grade DXF/SVG for scanned blueprint PNG/JPEG
**Suspension:** None

**Key files:**
- `light_line_body_extractor.py` — Core extraction logic
- `edge_to_dxf.py` — DXF output
- `blueprint_view_segmenter.py` — View segmentation

### 2. Photo Path — SUSPENDED

**Entry:** `source_type="photo"` or auto-detect non-AI
**Implementation:** 12-stage pipeline in `extract()` method body
**Status:** Suspended — poor results on L-1 historical images
**Suspension reason:** Sprint 4 (2026-04-16)

**Key files:**
- `body_isolation_stage.py` — Body isolation
- `contour_stage.py` — Contour extraction
- `contour_election.py` — Contour selection
- `geometry_coach.py` / `geometry_coach_v2.py` — ML coaching (Scaffolded for IBG)

**Remaining Sprint 4 work (if resumed):**
- Body isolation filter (4 paths → 1)
- Scale output discrepancy
- Neck crop pre-processor

### 3. AI Path — SUSPENDED

**Entry:** `source_type="ai"` or auto-detect AI-generated
**Implementation:** `_extract_ai_path()` — 4-stage pipeline (v3 feature)
**Status:** Suspended — poor results on AI renders (DALL-E, Midjourney)
**Suspension reason:** Sprint 4 (2026-04-16)

**Key files:**
- `ai_render_extractor.py` — AI render extraction
- `cognitive_extraction_engine.py` — Cognitive AI path
- `cognitive_extractor.py` — AI cognitive extraction

### 4. Silhouette Path — Status TBD

**Entry:** `source_type="silhouette"`
**Implementation:** `_extract_silhouette_path()` — flood-fill extraction
**Status:** Not explicitly suspended, but limited use case

**Key files:**
- `photo_silhouette_extractor.py` — Silhouette extraction

---

## Code Classification by Path

### Blueprint Path Files (LIVE)

| File | Role |
|------|------|
| `light_line_body_extractor.py` | Core blueprint extraction |
| `edge_to_dxf.py` | DXF output |
| `blueprint_view_segmenter.py` | View segmentation |
| `extract_body_grid_v5.py` | Grid extraction (latest) |
| `grid_classify.py` | Grid classification |

### Photo Path Files (SUSPENDED)

| File | Role |
|------|------|
| `body_isolation_stage.py` | Body isolation |
| `body_isolation_result.py` | Result data structure |
| `contour_stage.py` | Contour extraction |
| `contour_election.py` | Contour selection |
| `contour_plausibility.py` | Plausibility scoring |
| `landmark_extractor.py` | Landmark detection |
| `geometry_authority.py` | Geometry validation |
| `multi_view_reconstructor.py` | Multi-view handling |

### AI Path Files (SUSPENDED)

| File | Role |
|------|------|
| `ai_render_extractor.py` | AI render extraction |
| `cognitive_extraction_engine.py` | Cognitive AI path |
| `cognitive_extractor.py` | AI cognitive extraction |
| `generate_carlos_jumbo_dxf*.py` | Carlos Jumbo AI scripts |
| `calibrate_carlos_jumbo.py` | Carlos Jumbo calibration |

### ML Training Layer Files (SCAFFOLDED)

| File | Role | Future Home |
|------|------|-------------|
| `geometry_coach_v2.py` | ML coaching | TBD (not sg.coach) |
| `geometry_coach.py` | Older coaching | TBD |
| `replay_execution.py` | Training replay | TBD |

### Shared Infrastructure (LIVE)

| File | Role |
|------|------|
| `photo_vectorizer_v2.py` | Main orchestrator |
| `body_model.py` | Data structures |
| `material_bom.py` | BOM generation |
| `replay_*.py` | Test/replay infrastructure |
| `__init__.py` | Package init |

---

## IBG Wiring Target

The IBG + ML Repo Extraction sprint should wire to:

**Entry point:** `PhotoVectorizerV2.extract(source_type="blueprint")`

This is the established interface. The blueprint path's output feeds IBG for second-pass correction.

**Do NOT** wire directly to `light_line_body_extractor.py` — that would bypass the orchestrator layer and create a duplicate interface.

---

## Relationship to Blueprint Vectorizer (vectorizer_phase3.py)

**No direct code sharing.** `photo_vectorizer_v2.py` does not import from `vectorizer_phase3.py`.

The two pipelines are separate:
- `services/blueprint-import/vectorizer_phase3.py` — PDF blueprint extraction (Phase3Vectorizer)
- `services/photo-vectorizer/photo_vectorizer_v2.py` — Photo/image extraction (PhotoVectorizerV2)

They share conceptual approaches and may share utilities (like DXF output patterns), but there is no code-level delegation between them.
