# DXF Reconciliation Pre-Migration Investigation

**Date:** 2026-04-25
**Sprint:** 3B — DXF Reconciliation (Full Consolidation)
**Purpose:** Pre-migration investigation to inform architectural decisions
**Status:** COMPLETE — decisions locked

---

## 1. dxf_writer.py Interface Summary

**Location:** `services/api/app/cam/dxf_writer.py` (149 lines)

### Core Class: `DxfWriter`

| Method | Parameters | Purpose |
|--------|------------|---------|
| `__init__` | `layers: Sequence[LayerDef]` | Creates R12 doc, registers layers |
| `add_layer` | `ldef: LayerDef` | Register named layer (rejects layer 0) |
| `add_line` | `layer, start, end` | Single LINE entity |
| `add_polyline` | `layer, points, closed` | Polyline as LINE segments |
| `add_circle` | `layer, center, radius` | CIRCLE entity |
| `add_arc` | `layer, center, radius, start_angle, end_angle` | ARC entity |
| `add_point` | `layer, location` | POINT entity |
| `add_text` | `layer, text, insert, height` | TEXT entity |
| `add_polyline3d` | `layer, points, closed` | 3D POLYLINE |
| `to_bytes()` | — | Return DXF as bytes |
| `saveas(path)` | — | Write to file |

### Factory Function

```python
create_dxf_writer(layer_names: Sequence[str], layer_color: int = 7) -> DxfWriter
```

### Standards Enforced (per CLAUDE.md)

- **Format:** R12 (AC1009) — maximum CAM compatibility
- **Entities:** LINE only — no LWPOLYLINE, no POLYLINE2D
- **Coordinates:** 3 decimal place precision
- **Extents:** Sentinel EXTMIN/EXTMAX (1e+20) — do NOT recompute
- **Layers:** Named layers only — no geometry on layer 0

---

## 2. R2010 → R12 Feature Analysis

### Files Using R2010-Specific Features

| File | Current | Features Used | R12-Compatible? | Migration Path |
|------|---------|---------------|-----------------|----------------|
| bezier_body.py | R2010 | `add_spline`, `add_lwpolyline` | NO | Remove SPLINE (unused), convert LWPOLYLINE → LINE |
| archtop_surface_tools.py | R2010 | `add_lwpolyline` | NO | Convert LWPOLYLINE → LINE (lossless) |
| smart_guitar_dxf_router.py | R2010 | `add_lwpolyline` | NO | Convert LWPOLYLINE → LINE (lossless) |

### bezier_body.py SPLINE Mode Investigation

**Question:** Is SPLINE mode actively called by any consumer?

**Answer:** NO — unused code path.

Evidence:
- `use_spline: bool = False` — default is polyline mode
- Grep across codebase: zero callers pass `use_spline=True`
- Example code (line 18): `generator.to_dxf("body_outline.dxf")` — no spline flag

**Question:** What tolerance does the polyline approximation use?

**Answer:** 200 points total (100 per side), ~5mm spacing at guitar scale.

- `resolution=200` is default
- For 20" body length: ~2.5mm per point along curve
- Already discrete point approximation from Bézier evaluation

**Question:** How visually significant is the curvature loss?

**Answer:** Negligible at 200-point resolution.

The outline data is already discrete points. SPLINE vs LWPOLYLINE vs LINE all use the same point data — only the DXF entity type differs. At 200 points on a guitar body, visual difference is imperceptible.

### Decision: bezier_body.py Migration

**LOCKED:** Remove SPLINE mode (dead code), convert LWPOLYLINE → LINE via dxf_writer.py.

Rationale:
- SPLINE mode has zero callers — safe to remove
- LWPOLYLINE → LINE is lossless — same point data, different entity type
- R12 rule wins — universal compliance simplifies maintenance

---

## 3. layered_dxf_writer.py Investigation

**Location:** `services/api/app/services/layered_dxf_writer.py` (181 lines)

### Purpose

Specialized writer for layered DXF output with preset support:
- `GEOMETRY_ONLY` — primary geometry
- `GEOMETRY_PLUS_AUX` — geometry + auxiliary views
- `REFERENCE_FULL` — all layers

### Current Implementation

- Already uses R12 format
- Already writes LINE entities only
- Uses direct `ezdxf.new()` call (line 80)

### Active Callers

1 caller: `services/api/app/services/blueprint_orchestrator.py`

### Git History

```
814be53b Revert "feat(vectorizer): implement phase 6b confidence-gated body polyline output"
ec56946a feat(vectorizer): implement phase 6b confidence-gated body polyline output
5d42ee3f feat(vectorizer): implement BODY system with support contour promotion
c8e68d69 feat(vectorizer): add layer model and classification for Phase 4
```

Created for vectorizer Phase 4 work — specialized layer handling for blueprint extraction.

### Relationship to dxf_writer.py

| Aspect | dxf_writer.py | layered_dxf_writer.py |
|--------|---------------|----------------------|
| Created | 7b04008d (earlier) | c8e68d69 (Phase 4) |
| Purpose | General DXF output | Blueprint layer presets |
| DXF Format | R12 | R12 |
| Entity Type | LINE only | LINE only |

**Not a predecessor** — parallel implementation serving different use case.

### Decision: layered_dxf_writer.py Migration

**LOCKED:** Migrate internally to use `DxfWriter` instead of direct `ezdxf.new()`.

Rationale:
- Preserves specialized preset/layer API
- Centralizes ezdxf usage in dxf_writer.py
- Already follows R12/LINE-only standard — minimal code change

---

## 4. Verification Standard

### Three-Tier Verification

| Tier | Scope | Method | Files |
|------|-------|--------|-------|
| 1 | All 13 files | Geometric equivalence (entity count, coordinates, layers) | All |
| 2 | Critical path 6 | Visual render comparison (matplotlib/ezdxf viewer) | IBG + active features |
| 3 | Top priority 3 | Fusion 360 import test (code owner runs) | arc_reconstructor, body_contour_solver, bezier_body |

### Pre-Migration Baseline Capture

Before each file migration:
1. Generate sample DXF output with current code
2. Store baseline in `services/api/test_temp/baselines/`
3. After migration, generate same output with new code
4. Run Tier 1 comparison

### Tier 3 File Selection (LOCKED)

1. `arc_reconstructor.py` — IBG core, Sprint 4/5, critical path
2. `body_contour_solver.py` — IBG core, paired with arc_reconstructor
3. `bezier_body.py` — Body generator, Smart Guitar Fusion work

---

## 5. CI Enforcement

### Existing CI Infrastructure

- **Platform:** GitHub Actions (52 workflow files)
- **Pre-commit:** `.pre-commit-config.yaml` with local hooks

### Relevant Existing Workflows

| Workflow | Purpose |
|----------|---------|
| dxf_validation.yml | DXF output validation |
| dxf_validation_gate.yml | DXF output gate (well-formed R12, closed polylines) |
| api_dxf_tests.yml | DXF test suite |

### dxf_validation_gate.yml Analysis

**Current purpose:** Validates DXF OUTPUT files (not source code)

Checks:
- Must be AC1009 or later (R12+)
- Must have at least 1 closed LWPOLYLINE
- Bounding box within reasonable dimensions

**Assessment:** OUTPUT validation is different concern from SOURCE CODE rule enforcement.

### Decision: CI Workflow Placement (LOCKED)

**Create new workflow:** `dxf_ezdxf_gate.yml`

Rationale:
- Separation of concerns (output vs source)
- Independent failure modes
- Simple grep-based check warrants dedicated workflow

### Proposed Workflow

```yaml
# .github/workflows/dxf_ezdxf_gate.yml
name: DXF ezdxf.new() Enforcement

on:
  push:
    branches: [main]
    paths:
      - 'services/api/app/**/*.py'
  pull_request:
    paths:
      - 'services/api/app/**/*.py'

jobs:
  check-ezdxf-usage:
    name: Check for direct ezdxf.new() calls
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Check for direct ezdxf.new() calls
        run: |
          VIOLATIONS=$(grep -rn "ezdxf\.new" --include="*.py" services/api/app/ | grep -v "dxf_writer.py" | grep -v "dxf_compat.py" || true)
          if [ -n "$VIOLATIONS" ]; then
            echo "::error::Direct ezdxf.new() calls found outside dxf_writer.py:"
            echo "$VIOLATIONS"
            echo ""
            echo "All DXF generation must route through dxf_writer.py."
            echo "See: services/api/app/cam/dxf_writer.py"
            exit 1
          fi
          echo "✓ No direct ezdxf.new() calls found outside dxf_writer.py"
```

---

## 6. Migration Priority (from generator_status_2026-04-25.md)

### Critical Path (IBG + body generation)

| Priority | File | Current | Notes |
|----------|------|---------|-------|
| 1 | `ibg/arc_reconstructor.py` | R12 ×3 | 3 separate ezdxf.new() calls |
| 2 | `ibg/body_contour_solver.py` | R12 | 1 call |
| 3 | `generators/bezier_body.py` | R2010 | Remove SPLINE, convert LWPOLYLINE |

### Active Features

| Priority | File | Current | Notes |
|----------|------|---------|-------|
| 4 | `art_studio/generators/inlay_export.py` | R12 | 1 call |
| 5 | `cam/archtop/archtop_surface_tools.py` | R2010 | Convert LWPOLYLINE |
| 6 | `routers/instruments/smart_guitar_dxf_router.py` | R2010 | Convert LWPOLYLINE |

### Utility/Validation

| Priority | File | Current | Notes |
|----------|------|---------|-------|
| 7 | `cam/dxf_consolidator.py` | R2000 | |
| 8 | `cam/dxf_advanced_validation.py` | R2010 ×2 | 2 separate calls |
| 9 | `cam/layer_consolidator.py` | R2000 | |
| 10 | `services/layered_dxf_writer.py` | R12 | Migrate internally |
| 11 | `routers/neck/export.py` | R12 | |
| 12 | `routers/dxf_preflight_router.py` | R12 | |
| 13 | `calculators/inlay_calc.py` | R12 | |

---

## 7. Decisions Summary

| Decision | Status | Outcome |
|----------|--------|---------|
| bezier_body.py SPLINE mode | **LOCKED** | Remove (unused code) |
| LWPOLYLINE → LINE conversion | **LOCKED** | Accept (lossless) |
| layered_dxf_writer.py fate | **LOCKED** | Migrate internally to use DxfWriter |
| Tier 3 verification files | **LOCKED** | arc_reconstructor, body_contour_solver, bezier_body |
| CI workflow placement | **LOCKED** | New `dxf_ezdxf_gate.yml` |

---

## 8. Next Steps

1. Begin migration in priority order (1-13)
2. Capture pre-migration baselines before each file
3. Apply Tier 1 verification to all files
4. Apply Tier 2 verification to priority 1-6
5. Provide Tier 3 DXF outputs to code owner for priorities 1-3
6. Add `dxf_ezdxf_gate.yml` after all 13 files migrated
7. Backfill IBG Sprint 4/5 closeout documents

**Holding for execution direction.**
