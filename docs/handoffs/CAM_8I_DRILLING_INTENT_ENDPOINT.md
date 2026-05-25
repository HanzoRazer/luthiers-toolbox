# CAM Dev Order 8I: Drilling Intent Endpoint Migration

**Status**: COMPLETE  
**Date**: 2026-05-25  
**Sprint**: CAM-INTENT  

## Summary

Migrated Drilling operation to CamIntentV1 following the pattern established by 8G (V-Carve) and 8H (Profile).
Added depth/diameter ratio feasibility check, correct DrillConfig field mapping, and full OPERATION-lane compliance.

## Scope Decisions

Per user guidance, the following fields were excluded from 8I scope:

| Field | Decision | Reason |
|-------|----------|--------|
| `through_hole` | EXCLUDED | No core support - PeckDrill has no through-hole logic |
| `coolant_mode` | EXCLUDED | No core support - G-code generator has no coolant control |
| `hole_diameter_mm` | INCLUDED | Enables feasibility validation (depth/diameter ratio) |

## Deliverables

### New Files

| File | Purpose |
|------|---------|
| `app/cam/drilling/intent_schema.py` | DrillingDesignV1 schema for design bucket |
| `app/cam/drilling/intent_adapter.py` | Bridge CamIntentV1 → DrillConfig |
| `app/cam/drilling/feasibility.py` | Drilling feasibility check with depth/diameter ratio |
| `app/cam/routers/drilling/intent_router.py` | POST /intent-gcode endpoint |
| `tests/cam/test_drilling_design_schema.py` | 19 schema validation tests |
| `tests/cam/test_drilling_intent_migration.py` | 17 adapter + feasibility + integration tests |

### Modified Files

| File | Change |
|------|--------|
| `app/cam/drilling/__init__.py` | Export intent_schema, intent_adapter, feasibility |
| `app/cam/routers/drilling/__init__.py` | Include intent_router in aggregator |
| `app/cam/routers/drilling/drilling_consolidated_router.py` | Mount intent_router |

## Endpoint Specification

```
POST /api/cam/drilling/intent-gcode
```

**Request**: CamIntentV1 envelope with mode=router_3axis

**Response** (200):
```json
{
  "gcode": "...",
  "issues": [],
  "run_id": "run_abc123",
  "hashes": {
    "request_sha256": "...",
    "feasibility_sha256": "...",
    "gcode_sha256": "..."
  },
  "metadata": {
    "hole_count": 6,
    "total_depth_mm": 270.0,
    "estimated_time_seconds": 45.2
  }
}
```

**Error responses**:
- 422: Invalid mode, invalid design, adapter error, normalization error
- 409: Feasibility check blocked

## DrillingDesignV1 Schema

Design bucket fields (the "what"):
```python
class DrillingDesignV1(BaseModel):
    holes: List[DrillPointV1]      # Required, min 1
    hole_depth_mm: float           # Required, > 0, <= 200
    hole_diameter_mm: float        # Required, > 0, <= 50 (for feasibility)
    peck_drilling: bool = True
    peck_depth_mm: Optional[float] # Required > 0 and < hole_depth when peck_drilling
    dwell_ms: int = 0
```

### Peck Depth Validation

When `peck_drilling=True`:
- `peck_depth_mm` must be > 0
- `peck_depth_mm` must be < `hole_depth_mm`

This prevents invalid configurations where peck depth equals or exceeds hole depth.

## Field Mapping

The adapter maps to actual DrillConfig fields:

| Design Field | DrillConfig Field | Notes |
|--------------|-------------------|-------|
| `hole_diameter_mm` | `drill_diameter_mm` | KEY MAPPING for feasibility |
| `hole_depth_mm` | `hole_depth_mm` | Direct |
| `peck_depth_mm` | `peck_depth_mm` | Direct |
| `peck_drilling` | `use_canned_cycle` | True = G83, False = G81 |
| `dwell_ms` | `dwell_ms` | Direct |

## Feasibility Check

The feasibility check mirrors `peck_cycle.py::_validate()` but runs BEFORE toolpath generation.

Key validation:
```python
# Depth/diameter ratio check - matches peck_cycle.py behavior
if hole_diameter_mm > 0:
    ratio = hole_depth_mm / hole_diameter_mm
    if ratio > 10:
        warnings.append(
            f"Deep hole warning: depth/diameter ratio is {ratio:.1f}. "
            "Consider using smaller peck depth or pilot hole."
        )
```

Risk levels:
- `low`: No issues or warnings
- `medium`: 1-2 warnings
- `high`: 3+ warnings
- `blocked`: Any issue (e.g., zero depth, zero diameter)

## Test Coverage

- 19 schema tests (DrillingDesignV1 validation including peck_depth)
- 7 adapter tests (drilling_params_from_intent)
- 6 feasibility tests (including depth/diameter ratio warning)
- 4 integration tests (full intent → G-code flow)

All 36 tests pass. V-Carve (33) and Profile (28) tests still pass.

## CI Guard Verification

1. Positive test: `check_execution_class_compliance.py` passes with drilling intent_router
2. Negative test: Removing `normalize_cam_intent_v1` causes guard to flag `drilling/intent_router.py`

```
❌ Execution Governance Violation

The following CAM modules do not normalize CamIntentV1:

  - api\app\cam\routers\drilling\intent_router.py
```

## Feature Parity Status

| Capability | Legacy `/gcode` | Intent `/intent-gcode` |
|------------|-----------------|------------------------|
| Single holes | ✓ | ✓ |
| Hole patterns | ✓ | ✓ |
| Peck drilling (G83) | ✓ | ✓ |
| Simple drilling (G81) | ✓ | ✓ |
| Per-hole depth override | ✓ | ✓ |
| Dwell at bottom | ✓ | ✓ |
| String-through patterns | ✓ | ✓ |
| Feasibility check | - | ✓ (new) |
| Depth/diameter warning | - | ✓ (new) |
| RMOS artifact | - | ✓ (new) |
| Provenance hashes | - | ✓ (new) |

Legacy endpoint remains live under Feature Parity Migration Policy.

## Next Steps

1. Migrate Pocketing endpoint to CamIntentV1 (Dev Order 8J)
2. Update ADR-003 with V-Carve + Profile + Drilling complete

## References

- CamIntentV1 schema: `app/rmos/cam/schemas_intent.py`
- Normalizer: `app/rmos/cam/normalize_intent.py`
- Drilling core: `app/cam/drilling/peck_cycle.py`
- 8G V-Carve migration: `docs/handoffs/CAM_8G_VCARVE_INTENT_FIRST_ENDPOINT.md`
- 8H Profile migration: `docs/handoffs/CAM_8H_PROFILE_INTENT_ENDPOINT.md`
- Feature Parity Migration Policy: `FEATURE_PARITY_MIGRATION_POLICY.md`
