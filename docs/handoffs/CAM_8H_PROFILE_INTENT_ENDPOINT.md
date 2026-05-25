# CAM Dev Order 8H: Profile Intent Endpoint Migration

**Status**: COMPLETE  
**Date**: 2026-05-25  
**Sprint**: CAM-INTENT  

## Summary

Migrated Profile operation to CamIntentV1 following the pattern established by 8G (V-Carve).
Added minimal feasibility check, correct ProfileConfig field mapping, and full OPERATION-lane compliance.

## Prerequisite Work

Fixed CI guard scope (`check_execution_class_compliance.py`) to only check `intent_router.py` files,
not all CAM Python files. This was blocking 8G verification.

## Deliverables

### New Files

| File | Purpose |
|------|---------|
| `app/cam/profiling/intent_schema.py` | ProfileDesignV1 schema for design bucket |
| `app/cam/profiling/intent_adapter.py` | Bridge CamIntentV1 → ProfileConfig |
| `app/cam/profiling/feasibility.py` | Minimal feasibility check |
| `app/cam/routers/profiling/intent_router.py` | POST /intent-gcode endpoint |
| `tests/cam/test_profile_design_schema.py` | 19 schema validation tests |
| `tests/cam/test_profile_intent_migration.py` | 23 adapter + feasibility + integration tests |

### Modified Files

| File | Change |
|------|--------|
| `app/cam/profiling/__init__.py` | Export intent_schema, intent_adapter, feasibility |
| `app/cam/routers/profiling/__init__.py` | Include intent_router in aggregator |
| `app/ci/check_execution_class_compliance.py` | Scope to intent_router.py files only |

## Endpoint Specification

```
POST /api/cam/profiling/intent-gcode
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
    "pass_count": 3,
    "tab_count": 4,
    "total_length_mm": 1234.56,
    "estimated_time_seconds": 45.2
  }
}
```

**Error responses**:
- 422: Invalid mode, invalid design, adapter error, normalization error
- 409: Feasibility check blocked

## ProfileDesignV1 Schema

Design bucket fields (the "what"):
```python
class ProfileDesignV1(BaseModel):
    contour: List[ProfilePointV1]  # Required, min 3 points
    is_closed: bool = True
    is_outside: bool = True        # Outside cut vs inside cut
    tool_diameter_mm: float        # Required, > 0
    cut_depth_mm: float            # Required, > 0
    use_tabs: bool = True
    tab_count: int = 4             # >= 1 when use_tabs=True
    tab_width_mm: float = 6.0
    tab_height_mm: float = 1.5
    finishing_pass: bool = True
    finishing_allowance_mm: float = 0.3
```

## Field Mapping Corrections

The adapter maps to actual ProfileConfig fields, not legacy router's incorrect field names:

| Intent Field | ProfileConfig Field |
|--------------|---------------------|
| `is_outside` | `compensation_side` ("outside" or "inside") |
| `context.stepdown_mm` | `stepdown_mm` |
| `context.climb_milling` | `direction` (MillingDirection enum) |
| `context.feed_rate_mm_min` | `feed_rate_xy` |

## Feasibility Check

Minimal feasibility validation:
- Tool diameter > 0
- Cut depth > 0
- Stepdown > 0 and reasonable vs tool diameter
- Feed/plunge rates in bounds
- Contour has >= 3 points
- Tab settings coherent (height < cut depth)
- Safe/retract Z > 0

Returns risk_level: "low", "medium", "high", or "blocked".

## Test Coverage

- 19 schema tests (ProfileDesignV1 validation)
- 10 adapter tests (profile_params_from_intent)
- 4 feasibility tests
- 9 integration tests (endpoint behavior)

All 42 tests pass. V-Carve tests (33) still pass.

## CI Guard Fix

`check_execution_class_compliance.py` was checking all CAM Python files for
`normalize_cam_intent_v1`. This is wrong - only OPERATION-lane intent routers
should be checked.

Fixed to check only `intent_router.py` files in router directories.

## Feature Parity Status

| Capability | Legacy `/gcode` | Intent `/intent-gcode` |
|------------|-----------------|------------------------|
| Contour profile | ✓ | ✓ |
| Inside/outside cut | ✓ | ✓ (correct mapping) |
| Tool diameter | ✓ | ✓ |
| Multi-pass stepdown | ✓ | ✓ |
| Holding tabs | ✓ | ✓ |
| Climb/conventional | ✓ | ✓ |
| Lead-in radius | ✓ | ✓ |
| Feasibility check | - | ✓ (new) |
| RMOS artifact | - | ✓ (new) |
| Provenance hashes | - | ✓ (new) |
| Metadata in response | headers | JSON body |

Legacy endpoint remains live under Feature Parity Migration Policy.

## Next Steps

1. Migrate Drilling endpoint to CamIntentV1 (Dev Order 8I)
2. Migrate Pocketing endpoint to CamIntentV1 (Dev Order 8J)
3. Update ADR-003 with V-Carve + Profile complete

## References

- CamIntentV1 schema: `app/rmos/cam/schemas_intent.py`
- Normalizer: `app/rmos/cam/normalize_intent.py`
- 8G V-Carve migration: `docs/handoffs/CAM_8G_VCARVE_INTENT_FIRST_ENDPOINT.md`
- Feature Parity Migration Policy: `FEATURE_PARITY_MIGRATION_POLICY.md`
