# GEN-5: Generator Remediation Plan — Description System Consolidation

**Date:** 2026-03-17
**Status:** In Progress
**Gap:** GEN-5

---

## Problem Statement

Three systems describe the same instruments with overlapping but inconsistent data:

| System | Location | Models | Coverage |
|--------|----------|--------|----------|
| 1. instrument_model_registry.json | app/instrument_geometry/ | 30+ | Rich metadata, assets, status |
| 2. model_spec.py PRESET_MODELS | app/instrument_geometry/ | 2 | Detailed string/spacing/taper |
| 3. guitars/*.py MODEL_INFO | app/instrument_geometry/guitars/ | 19 | Per-model specs, get_spec() |

### Specific Issues

1. **Duplication:** Same model defined in multiple places with potential drift
2. **Missing cam_capable flag:** No explicit marker for which models support CAM generation
3. **Incomplete coverage:** model_spec.py only has 2 models, guitars/*.py has 19, JSON has 30+
4. **No single source of truth:** Consumers don't know which source to trust

---

## Consolidation Plan

### Phase 1: Designate Single Source of Truth

**Winner: instrument_model_registry.json**

Rationale:
- Richest metadata (assets, status, variants, manufacturer, year)
- Already has 30+ models
- JSON is language-agnostic (can be consumed by frontend)
- Easy to add new fields (cam_capable, etc.)

### Phase 2: Add cam_capable Flag

Add to each model in instrument_model_registry.json:

- cam_capable: boolean indicating if model supports CAM generation
- cam_operations: array of available CAM operations

### Phase 3: Generate guitars/*.py from JSON

Option A (Recommended): **Deprecate guitars/*.py MODEL_INFO**
- Keep get_spec() functions but have them read from JSON
- Remove duplicated MODEL_INFO dicts
- guitars/__init__.py loads from JSON

Option B: **Code generation**
- Script generates guitars/*.py from JSON
- Run on JSON change

### Phase 4: Expand model_spec.py PRESET_MODELS

Either:
- Auto-generate PRESET_MODELS from JSON + manual string/taper data files
- Or deprecate PRESET_MODELS in favor of JSON + separate taper configs

---

## Current Model Status

### CAM-Capable Models (cam_capable: true)

| Model | Status | CAM Operations |
|-------|--------|----------------|
| les_paul | COMPLETE | OP20-OP63 (body generator) |
| stratocaster | PARTIAL | Neck presets, body outline |
| explorer | PARTIAL | 2-phase G-code (rear + perimeter) |
| flying_v | PARTIAL | DWG assets only |
| melody_maker | COMPLETE | DXF outline |
| smart_guitar | COMPLETE | Electronics cavities |
| klein | PARTIAL | Vectorizer output |

### Non-CAM Models (cam_capable: false)

| Model | Status | Reason |
|-------|--------|--------|
| telecaster | STUB | No assets |
| sg | STUB | No assets |
| es_335 | STUB | No assets |
| firebird | STUB | No assets |
| moderne | STUB | No assets |
| prs | STUB | No assets |
| dreadnought | STUB | No assets |
| j_45 | STUB | No assets |
| classical | STUB | No assets |
| jazz_bass | STUB | No assets |

---

## Implementation Steps

1. [ ] Add cam_capable field to all models in instrument_model_registry.json
2. [ ] Add cam_operations array listing available CAM operations
3. [ ] Update guitars/__init__.py to load MODEL_INFOS from JSON
4. [ ] Deprecate per-file MODEL_INFO dicts (keep get_spec() functions)
5. [ ] Add JSON schema validation for instrument_model_registry.json
6. [ ] Update model_spec.py to read scale profiles from JSON
7. [ ] Add API endpoint: GET /api/instrument-geometry/models?cam_capable=true

---

## Files Changed

### Modified
- services/api/app/instrument_geometry/instrument_model_registry.json
- services/api/app/instrument_geometry/guitars/__init__.py
- services/api/app/instrument_geometry/model_spec.py

### Deprecated (but not deleted)
- services/api/app/instrument_geometry/guitars/*.py (MODEL_INFO dicts only)

---

## Validation

After changes:
- Run pytest services/api/tests/test_instrument_model_registry.py -v
- Verify MODEL_INFOS loads correctly from JSON

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing imports | Keep get_spec() functions, only change data source |
| JSON schema drift | Add JSON schema validation |
| Frontend assumptions | Version the JSON, add deprecation notices |
