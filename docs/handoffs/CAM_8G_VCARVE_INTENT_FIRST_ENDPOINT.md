# CAM Dev Order 8G: V-Carve Intent First-Endpoint Migration

**Status**: COMPLETE  
**Date**: 2026-05-25  
**Sprint**: CAM-INTENT  

## Summary

Implemented the first CamIntentV1-based endpoint for V-Carve operations, establishing
the pattern for migrating remaining CAM endpoints to the unified intent contract.

## Deliverables

### New Files

| File | Purpose |
|------|---------|
| `app/cam/vcarve/intent_schema.py` | VCarveDesignV1 schema for design bucket |
| `app/cam/vcarve/intent_adapter.py` | Bridge CamIntentV1 → VCarveConfig |
| `app/cam/routers/vcarve/intent_router.py` | POST /intent-gcode endpoint |
| `tests/cam/test_vcarve_design_schema.py` | 14 schema validation tests |
| `tests/cam/test_vcarve_intent_migration.py` | 19 adapter + integration tests |

### Modified Files

| File | Change |
|------|--------|
| `app/cam/vcarve/__init__.py` | Export intent_schema and intent_adapter |
| `app/cam/routers/vcarve/__init__.py` | Include intent_router in aggregator |

## Endpoint Specification

```
POST /api/cam/vcarve/intent-gcode
```

**Request**: CamIntentV1 envelope with mode=router_3axis

**Response** (200):
```json
{
  "gcode": "G21\nG90\n...",
  "issues": [{"code": "UNITS_NORMALIZED", "message": "...", "path": "units"}],
  "run_id": "run_abc123",
  "hashes": {
    "request_sha256": "...",
    "feasibility_sha256": "...",
    "gcode_sha256": "..."
  }
}
```

**Error responses**:
- 422: Invalid mode, invalid design, adapter error, normalization error
- 409: Safety policy blocked

## VCarveDesignV1 Schema

Design bucket fields (the "what"):
```python
class VCarveDesignV1(BaseModel):
    paths: List[VCarvePathV1]        # Required: carving paths
    bit_angle_deg: float             # Required: 10-120
    target_line_width_mm: float      # Required: 0.1-20
    target_depth_mm: Optional[float] # Optional: override auto-depth
    tip_diameter_mm: float = 0.0     # Tip diameter for flat-tip bits
```

Context fields extracted from CamIntentV1.context (the "how"):
- spindle_rpm, flute_count, chipload_factor
- max_stepdown_mm, min_passes
- safe_z_mm, retract_z_mm
- feed_rate_mm_min, plunge_rate_mm_min
- corner_slowdown, corner_angle_threshold_deg, corner_feed_factor

## OPERATION Lane Compliance

The endpoint follows the OPERATION lane pattern:
1. Normalize CamIntentV1 (units conversion, type coercion)
2. Validate mode == router_3axis
3. Validate design against VCarveDesignV1 schema
4. Adapt design+context → VCarveConfig + MLPath list
5. Run feasibility check via compute_feasibility_internal()
6. Block if SafetyPolicy.should_block() returns True
7. Generate toolpath via VCarveToolpath
8. Persist RMOS RunArtifact via persist_run()
9. Return structured JSON response

## Test Coverage

- 14 schema tests (VCarveDesignV1 validation)
- 12 adapter tests (vcarve_params_from_intent)
- 7 integration tests (endpoint behavior)

All 33 tests pass.

## Migration Pattern Established

This implementation establishes the pattern for remaining endpoint migrations:

1. **Design schema**: Create `{Operation}DesignV1` in `app/cam/{operation}/intent_schema.py`
2. **Adapter**: Create `{operation}_params_from_intent()` in `app/cam/{operation}/intent_adapter.py`
3. **Router**: Create `intent_router.py` with POST `/intent-gcode` endpoint
4. **Registration**: Include intent_router in operation's `__init__.py`
5. **Tests**: Schema tests + adapter tests + integration tests

## Feature Parity Status

| Capability | Legacy `/production/gcode` | Intent `/intent-gcode` |
|------------|---------------------------|------------------------|
| Accept V-carve request | ✓ | ✓ |
| Chipload calculation | ✓ | ✓ |
| Multi-pass stepdown | ✓ | ✓ |
| Corner slowdown | ✓ | ✓ |
| Feasibility check | ✓ | ✓ |
| RMOS artifact | ✓ | ✓ |
| Provenance hashes | - | ✓ (new) |
| Normalization issues | - | ✓ (new) |

Legacy endpoint remains live under Feature Parity Migration Policy.

## Next Steps

1. Migrate Profile endpoint to CamIntentV1 (Dev Order 8H)
2. Migrate Drilling endpoint to CamIntentV1 (Dev Order 8I)
3. Migrate Pocketing endpoint to CamIntentV1 (Dev Order 8J)
4. After all endpoints migrated, deprecate legacy paths

## References

- CamIntentV1 schema: `app/rmos/cam/schemas_intent.py`
- Normalizer: `app/rmos/cam/normalize_intent.py`
- Production V-Carve router: `app/cam/routers/vcarve/production_router.py`
- Feature Parity Migration Policy: `FEATURE_PARITY_MIGRATION_POLICY.md`
