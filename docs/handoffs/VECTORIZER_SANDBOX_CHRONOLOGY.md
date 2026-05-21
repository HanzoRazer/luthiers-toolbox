# Vectorizer Sandbox Chronology

**Created:** 2026-05-20  
**Purpose:** Document the evolution of vectorizer R&D sandboxes across repositories  
**Status:** Migration in progress to `vectorizer-sandbox`

---

## Timeline Overview

```
2025-12 ─────────────────────────────────────────────────────────────────────────
    │
    └─ ci/ai_sandbox/ created (governance checks, still active in luthiers-toolbox)

2026-03 ─────────────────────────────────────────────────────────────────────────
    │
    ├─ Mar 6: cuatro_puertorriqueño_simple.dxf baseline created (16.3 MB golden artifact)
    │
    └─ Mar 31: vectorizer-sandbox repo created (Wave 1-2)
         ├─ agentic_supervisor.py — Multi-pass supervision prototype
         ├─ vectorizer_enhancements.py — Wave 1 calibration features
         ├─ vectorizer_phase2.py / phase3.py — Incubation forks
         ├─ phase4/ — Dimension linking R&D
         └─ DEVELOPER_HANDOFF.md — Wave 3 multi-view extraction scope

2026-04 ─────────────────────────────────────────────────────────────────────────
    │
    ├─ Apr 15-16: sandbox/arc_reconstructor/ created (Sprint 9 — IBG)
    │    ├─ arc_reconstructor.py — 4-tier gap closure algorithm
    │    ├─ body_contour_solver.py — Parametric body generation (Sections A-G)
    │    ├─ constraint_extractor.py — DXF landmark extraction
    │    ├─ instrument_body_generator.py — End-to-end body completion
    │    ├─ reference_outline_bridge.py — Tier 0 reference bridging
    │    ├─ test_*.py — Unit tests (cuatro, dreadnought, DXF output)
    │    └─ SESSION_AUDITS.md — Detailed session findings
    │
    ├─ Apr 16: Production IBG created at services/api/app/instrument_geometry/body/ibg/
    │    └─ (sandbox prototypes promoted to production with proper packaging)
    │
    ├─ Apr 18: constraint_extractor.py / test_dreadnought_solver.py finalized
    │
    └─ Apr 28: services/blueprint-import/sandbox/text_geometry_eval/ created
         ├─ run_evaluation.py — Full corpus evaluation orchestrator
         ├─ runners/*.py — 6 pipeline runners (Phase2, Phase3, edge_to_dxf variants)
         ├─ metrics/*.py — Text legibility, geometry scoring, DXF inventory
         └─ README.md — 8-blueprint corpus definition, success criteria

2026-05 ─────────────────────────────────────────────────────────────────────────
    │
    ├─ May 2-13: services/blueprint-import/sandbox/adaptive_reconstruction/ created
    │    ├─ README.md — Observation sandbox scope (VECTOR-AI-1A sprint)
    │    ├─ ARCHAEOLOGY.md — Catalog of 6 existing sandboxes
    │    ├─ boundary.md — Hard forbidden list, production isolation
    │    ├─ metrics.md — Baseline corpus metrics schema
    │    └─ roadmap.md — 6-step evaluation plan
    │
    ├─ May 14: sandbox/arc_reconstructor/*.py timestamps updated (last local edits)
    │
    ├─ May 17: text_geometry_eval/runners/__pycache__ last accessed
    │
    └─ May 20: Migration to vectorizer-sandbox begins
         ├─ Phase 1: Scaffold semantic cognition layout (commit 18:01)
         ├─ Phase 2: Tier A semantic lineage import (commit 18:23)
         │    ├─ cognitive_extractor.py → src/semantic/
         │    ├─ cognitive_extraction_engine.py → src/semantic/
         │    ├─ extract_body_grid_v1-v5.py → src/archaeology/
         │    └─ vectorizer_phase2_runtime_spine.py → src/archaeology/
         │
         └─ Phase 3: arc_reconstructor migration (commit 20:51, 20:58)
              └─ sandbox/arc_reconstructor/* → src/archaeology/arc_reconstructor/
```

---

## Sandbox Inventory Summary

### Migrated to vectorizer-sandbox (2026-05-20)

| Origin | Destination | Status |
|--------|-------------|--------|
| `services/photo-vectorizer/cognitive_extractor.py` | `src/semantic/` | Migrated |
| `services/photo-vectorizer/cognitive_extraction_engine.py` | `src/semantic/` | Migrated |
| `services/photo-vectorizer/extract_body_grid_v1-v5.py` | `src/archaeology/` | Migrated |
| `sandbox/arc_reconstructor/*` | `src/archaeology/arc_reconstructor/` | Migrated |

### Pending Migration

| Origin | Destination | Status |
|--------|-------------|--------|
| `services/blueprint-import/sandbox/text_geometry_eval/` | `src/evaluation/text_geometry_eval/` | **PENDING** |
| `services/blueprint-import/sandbox/adaptive_reconstruction/` | `src/evaluation/adaptive_reconstruction/` | **PENDING** |

### Remains in luthiers-toolbox (Active)

| Location | Purpose | Status |
|----------|---------|--------|
| `ci/ai_sandbox/` | Governance CI checks | **ACTIVE** — do not migrate |
| `services/api/app/instrument_geometry/body/ibg/` | Production IBG | **ACTIVE** — production code |

---

## Thematic Groupings

These sandboxes represent **three waves of related R&D** that fragmented across time:

### Wave A: Body Extraction & Reconstruction (Apr 2026)

**Goal:** Complete partial vectorizer DXF output into full guitar body outlines

| Component | Location | Role |
|-----------|----------|------|
| `arc_reconstructor.py` | sandbox → vectorizer-sandbox | 4-tier gap closure math |
| `body_contour_solver.py` | sandbox → vectorizer-sandbox | Parametric body generation |
| `constraint_extractor.py` | sandbox → vectorizer-sandbox | Landmark extraction from DXF |
| `instrument_body_generator.py` | sandbox → vectorizer-sandbox | End-to-end orchestration |
| `reference_outline_bridge.py` | sandbox → vectorizer-sandbox | Reference waypoint bridging |
| **Production IBG** | `services/api/app/.../ibg/` | Promoted prototypes (ACTIVE) |

### Wave B: Extraction Mode Evaluation (Apr-May 2026)

**Goal:** Benchmark vectorizer modes for text preservation + geometry quality

| Component | Location | Role |
|-----------|----------|------|
| `text_geometry_eval/` | blueprint-import/sandbox | 8-corpus benchmark framework |
| `adaptive_reconstruction/` | blueprint-import/sandbox | Observation sandbox |
| Phase2/Phase3/edge_to_dxf runners | text_geometry_eval/runners/ | Pipeline comparison |
| `metrics/*.py` | text_geometry_eval/metrics/ | Legibility + geometry scoring |

### Wave C: Semantic Cognition (Mar-May 2026)

**Goal:** ML-based contour classification and body grid extraction

| Component | Location | Role |
|-----------|----------|------|
| `cognitive_extractor.py` | vectorizer-sandbox/src/semantic/ | ML classification (orphaned) |
| `cognitive_extraction_engine.py` | vectorizer-sandbox/src/semantic/ | Extraction engine (orphaned) |
| `extract_body_grid_v1-v5.py` | vectorizer-sandbox/src/archaeology/ | Grid extraction iterations |
| `agentic_supervisor.py` | vectorizer-sandbox/src/incubation/ | Multi-pass supervision |

---

## Key Findings from SESSION_AUDITS.md

These findings from the arc_reconstructor development sessions inform future work:

1. **Deduplication at LINE level** — Edge detection creates parallel traces 0.1-0.5mm apart. Must deduplicate before chain consolidation.

2. **Tuned DXF files are clean** — Files marked `*_tuned_full.dxf` have 100% closed contours. Arc reconstructor targets fragmented files.

3. **LINE-to-ARC promotion** — LWPOLYLINE with bulge values achieves 56-89% arc coverage. Parameters: `angle_tol=45°`, `tolerance_mm=1.0`, `max_error_mm=2.5`.

4. **Half-body detection critical** — Mirroring reference outline without detecting half-body causes 2x width mismatch.

5. **Tier 0 reference bridging** — Uses actual measured geometry from `body_outlines.json` waypoints, not spherical formula approximation.

6. **Source layer structure matters** — Some DXFs have multiple body layers at different scales/positions. Must select correct layer.

---

## Migration Manifest

See `vectorizer-sandbox/MIGRATION_MANIFEST.json` for:
- Source commit SHAs
- Blob hashes for verification
- Destination paths
- Phase tracking

---

*Document generated during sandbox consolidation sprint 2026-05-20*
