# Remediation Status — March 2026

## Current Metrics

| Metric | Count | Target | Status |
|--------|-------|--------|--------|
| Python files | 1,095 | — | Baseline |
| Files >500 LOC | 18 | 0 | In progress |
| Broad exceptions | 315 | 0 | In progress |
| Router files | 54 | — | Baseline |

## Completed Remediations

### Infrastructure (March 2026)

| Item | Commit | Description |
|------|--------|-------------|
| Rate limiting middleware | `1ce75797` | Token bucket rate limiter with configurable limits |
| WebSocket live monitor | `28cdf8bd` | Event streaming with subscription filters |
| Golden test fixtures | `af1e746c` | 38 tests: fret positions, DXF preflight, rosette geometry |
| Store migration | `9c4e4de9` | SQLite stores for art_jobs, art_presets (18 tests) |

### Code Quality

| Item | Status | Notes |
|------|--------|-------|
| Bare `except:` → specific types | Partial | 12 files fixed in previous session |
| Fence boundary checks | Active | `check_boundary_imports.py`, `check_boundary_patterns.py` |
| Architecture scan CI | Active | `architecture_scan.yml` workflow |

## Files >500 LOC (18 files)

Priority candidates for decomposition:

| File | Est. LOC | Decomposition Strategy |
|------|----------|------------------------|
| `DesignFirstWorkflowPanel.vue` | ~800 | Extract action bar, overrides panel, history |
| `ScientificCalculator.vue` | ~700 | Extract calculator pad, display, converters |
| `DxfToGcodeView.vue` | ~650 | Extract compare UI, why panel, result panel |
| `PipelineLabView.vue` | ~600 | Extract stage panels, preview, controls |
| `ManufacturingCandidateList.vue` | ~550 | Extract filters, row components |

## Broad Exceptions (315 remaining)

### By Category

| Pattern | Count | Fix |
|---------|-------|-----|
| `except Exception:` | ~200 | Narrow to specific types |
| `except:` (bare) | ~50 | Add explicit exception type |
| `except Exception as e:` (swallowed) | ~65 | Log or re-raise |

### Priority Files

Files with highest broad exception density:
1. `app/cam/` — geometry parsing, coordinate conversion
2. `app/routers/` — request validation, file operations
3. `app/_experimental/` — prototype code

## Router Consolidation (54 files)

### Current Structure
- `app/routers/` — 30+ files
- `app/art_studio/api/` — 12 files
- `app/rmos/` — scattered route modules
- `app/saw_lab/` — 8 router files

### Target Architecture
```
app/
├── api_v1/           # Versioned public API
├── routers/
│   ├── cam/          # CAM operations
│   ├── instruments/  # Instrument geometry
│   └── tools/        # Tool management
├── art_studio/api/   # Art Studio routes (consolidated)
├── rmos/api/         # RMOS routes (consolidated)
└── saw_lab/api/      # Decision intelligence routes
```

## Next Actions

1. **Decompose large Vue components** — Start with `DesignFirstWorkflowPanel.vue`
2. **Fix broad exceptions** — Focus on `app/cam/` first
3. **Consolidate routers** — Merge small routers into domain modules
4. **Add missing smoke tests** — Cover remaining router endpoints

## Tracking

| Date | Files >500 | Broad Exceptions | Notes |
|------|------------|------------------|-------|
| 2026-03-15 | 18 | 315 | Baseline |

---
*Last updated: 2026-03-15*
