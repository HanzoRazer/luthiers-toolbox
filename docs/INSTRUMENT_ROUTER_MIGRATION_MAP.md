# Instrument Router Migration Map
Generated: 2026-03-29
**Status: COMPLETE** (2026-03-29)

## Summary
- **Total endpoints migrated**: 19
- **Parallel implementations retained**: 4 (different schemas)
- **instrument_router.py**: Trimmed from 1,291 lines → 215 lines

## Migration Commits

| Commit | Endpoints | Router |
|--------|-----------|--------|
| `e48db130` | 5 | geometry_calculator_router.py |
| `ceeb4cc0` | 4 | tuning_machine_router.py |
| `6f33a931` | 4 | construction_router.py |
| `70b6c450` | 3 | string_tension_router.py |
| `4c9e4aa1` | 3 | nut_fret_router.py, soundhole_router.py |

## Parallel Implementations (4 endpoints) — RETAINED

These exist in BOTH instrument_router.py AND split routers with DIFFERENT schemas.
Retained pending schema reconciliation. See docs/INSTRUMENT_ROUTER_OVERLAP.md.

| Endpoint | instrument_router | split router |
|----------|-------------------|--------------|
| POST:/api/instrument/nut-compensation | action_at_nut_mm model | nut_width_mm model |
| POST:/api/instrument/nut-compensation/compare | NutCompareResponse | NutComparisonResponse |
| POST:/api/instrument/soundhole | has standard_diameter_mm | missing field |
| POST:/api/instrument/soundhole/check-position | has position_ratio | missing field |

## Migrated Endpoints (19) — COMPLETE

All migrated to split routers in `app/routers/instrument_geometry/`:

**Geometry (5 endpoints)** → geometry_calculator_router.py
- [x] GET:/api/instrument/geometry/presets
- [x] POST:/api/instrument/geometry/bridge
- [x] POST:/api/instrument/geometry/radius-at-position
- [x] POST:/api/instrument/geometry/radius-profile
- [x] POST:/api/instrument/geometry/standard-guitar

**String/Tension (3 endpoints)** → string_tension_router.py
- [x] GET:/api/instrument/string-tension/presets
- [x] POST:/api/instrument/string-tension
- [x] POST:/api/instrument/saddle-force

**Tuning Machine (4 endpoints)** → tuning_machine_router.py
- [x] GET:/api/instrument/tuning-machine/post-heights
- [x] GET:/api/instrument/tuning-machine/string-trees
- [x] POST:/api/instrument/tuning-machine
- [x] POST:/api/instrument/tuning-machine/required-height

**Construction (4 endpoints)** → construction_router.py
- [x] GET:/api/instrument/kerfing/types
- [x] POST:/api/instrument/kerfing
- [x] POST:/api/instrument/brace-sizing
- [x] POST:/api/instrument/top-deflection

**Other (3 endpoints)** → nut_fret_router.py, soundhole_router.py
- [x] GET:/api/instrument/nut-compensation/types
- [x] GET:/api/instrument/soundhole/body-styles
- [x] POST:/api/instrument/nut-compensation/zero-fret-positions

## Result

| Metric | Before | After |
|--------|--------|-------|
| instrument_router.py lines | 1,291 | 215 |
| Endpoint count | 917 | 898 |
| Split routers | 9 | 13 |

## Next Steps

1. Schema reconciliation for 4 parallel implementations
2. After reconciliation, remove parallel endpoints from instrument_router.py
3. Eventually delete instrument_router.py entirely
