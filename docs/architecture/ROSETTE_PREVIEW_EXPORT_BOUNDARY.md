# Rosette Preview/Export Boundary Proposal

**Dev Order:** 5G  
**Date:** 2026-05-10  
**Status:** Architecture Proposal (No Implementation)

---

## Boundary Definition

### Preview Layer (Safe)

Endpoints that produce **visual/geometric data only** with no machine semantics.

| Responsibility | Layer |
|----------------|-------|
| Visual geometry (SVG, paths) | PREVIEW |
| Ring/tile segmentation data | PREVIEW |
| BOM calculation | PREVIEW |
| Feasibility scoring | PREVIEW |
| Design comparison | PREVIEW |
| Snapshot persistence | PREVIEW |

**Characteristics:**
- No G-code output
- No machine profile assumptions
- No tool validation required
- No safety gate enforcement required
- RMOS integration optional

---

### Export Layer (Governed)

Endpoints that produce **machine-ready output** requiring governance.

| Responsibility | Layer |
|----------------|-------|
| G-code generation | EXPORT |
| DXF for CNC (with machine assumptions) | EXPORT |
| Toolpath postprocessing | EXPORT |
| CNC job creation | EXPORT |
| Operator reports | EXPORT |

**Characteristics:**
- Machine output (G-code, CNC-ready DXF)
- Requires RMOS artifact persistence
- Requires safety gate
- Requires coordinate system declaration
- Requires tool validation

---

## Current Route Classification

### Preview Routes

| Route | File | Output | Boundary |
|-------|------|--------|----------|
| `/api/art/rosette/preview/svg` | preview_routes.py | SVG | PREVIEW |
| `/api/art/rosette/preview` | rosette_jobs_routes.py | paths | PREVIEW |
| `/api/rmos/rosette/preview` | rosette_cam_router.py | snapshot | PREVIEW |
| `/api/rmos/rosette/segment-ring` | rosette_cam_router.py | geometry | PREVIEW |
| `/api/rmos/rosette/generate-slices` | rosette_cam_router.py | geometry | PREVIEW |
| `/rosette/designer/preview` | rosette_designer_routes.py | SVG | PREVIEW |
| `/rosette/designer/bom` | rosette_designer_routes.py | BOM | PREVIEW |
| `/api/art/rosette/compare` | rosette_compare_routes.py | diff | PREVIEW |

### Export Routes

| Route | File | Output | Boundary | Status |
|-------|------|--------|----------|--------|
| `/api/rmos/rosette/export-cnc` | rosette_cam_router.py | G-code | EXPORT | QUARANTINED |
| `/api/cam/rosette/post-gcode` | rosette_toolpath_router.py | G-code | EXPORT | GOVERNED |
| `/rosette/designer/export/svg` | rosette_designer_routes.py | SVG | EXPORT | UNTRACKED |
| `/pipelines/rosette/export-gcode` | legacy | G-code | EXPORT | LEGACY |

### Boundary Violations

| Route | Issue | Resolution |
|-------|-------|------------|
| `/api/rmos/rosette/export-cnc` | Export in preview router | Move to export namespace or add governance |

---

## Proposed Architecture

### Namespace Separation

```
/api/art/rosette/           # Design preview (visual)
├── preview/svg             # SVG preview
├── preview                 # Path preview
├── compare                 # Comparison
├── jobs                    # Job listing
└── presets                 # Preset listing

/api/rmos/rosette/          # CAM preview (geometry validation)
├── segment-ring            # Ring segmentation
├── generate-slices         # Slice generation
├── preview                 # CNC-aware preview
├── design                  # Multi-ring design
└── (remove export-cnc)     # Move to export namespace

/api/cam/rosette/           # Governed export
├── post-gcode              # G-code generation (governed)
├── export-cnc              # Future: governed CNC export
└── toolpath                # Toolpath generation
```

### Response Contract Differences

#### Preview Response

```json
{
  "ok": true,
  "geometry": {...},
  "statistics": {...},
  "warnings": []
}
```

No `gcode`, no `machine_profile`, no `tool_id`.

#### Export Response

```json
{
  "ok": true,
  "gcode": "...",
  "run_id": "RUN-ROSETTE-...",
  "coordinate_system": {
    "origin": "jig_center",
    "units": "mm",
    "z_zero": "stock_top"
  },
  "safety": {
    "decision": "GREEN",
    "risk_level": 0.2,
    "requires_override": false
  },
  "artifacts": {
    "input_hash": "sha256:...",
    "output_hash": "sha256:..."
  }
}
```

---

## Governance Requirements by Layer

### Preview Layer

| Requirement | Status |
|-------------|--------|
| Coordinate system | RECOMMENDED |
| RMOS metadata | OPTIONAL |
| Safety gate | NOT REQUIRED |
| Artifact persistence | NOT REQUIRED |

### Export Layer

| Requirement | Status |
|-------------|--------|
| Coordinate system | REQUIRED |
| RMOS run artifact | REQUIRED |
| Safety gate | REQUIRED |
| Input/output hash | REQUIRED |
| Tool validation | REQUIRED |
| Machine profile | REQUIRED |

---

## Migration Path

### Phase 1: Classification (5G)

- [x] Identify all routes
- [x] Classify as PREVIEW or EXPORT
- [x] Document boundary violations
- [x] Quarantine ungoverned exports

### Phase 2: Preview Normalization (5H-5I)

- [ ] Select canonical preview route
- [ ] Add coordinate_system to preview responses
- [ ] Add gate semantics to CAM preview

### Phase 3: Export Separation (5J)

- [ ] Move `/export-cnc` logic to governed path
- [ ] Add full RMOS governance
- [ ] Deprecate ungoverned export

### Phase 4: Cleanup (5K)

- [ ] Remove deprecated routes
- [ ] Update frontend consumers
- [ ] Final documentation

---

*Boundary proposal created: 2026-05-10*
