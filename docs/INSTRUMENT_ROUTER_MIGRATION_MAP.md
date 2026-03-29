# Instrument Router Migration Map
Generated: 2026-03-29

## Summary
- **Total endpoints in instrument_router.py**: 23
- **Already covered by split routers**: 4 (parallel implementations, NOT replacements)
- **Needs migration**: 19

## Endpoint Status

### COVERED (4 endpoints) — Different schemas, both remain
These exist in both instrument_router and split routers but use DIFFERENT
request/response schemas. See docs/INSTRUMENT_ROUTER_OVERLAP.md for details.

| Endpoint | instrument_router | split router |
|----------|-------------------|--------------|
| POST:/api/instrument/nut-compensation | action_at_nut_mm model | nut_width_mm model |
| POST:/api/instrument/nut-compensation/compare | NutCompareResponse | NutComparisonResponse |
| POST:/api/instrument/soundhole | has standard_diameter_mm | missing field |
| POST:/api/instrument/soundhole/check-position | has position_ratio | missing field |

### NOT COVERED (19 endpoints) — Need migration to split routers

**Geometry (5 endpoints)**
- GET:/api/instrument/geometry/presets
- POST:/api/instrument/geometry/bridge
- POST:/api/instrument/geometry/radius-at-position
- POST:/api/instrument/geometry/radius-profile
- POST:/api/instrument/geometry/standard-guitar

**String/Tension (3 endpoints)**
- GET:/api/instrument/string-tension/presets
- POST:/api/instrument/string-tension
- POST:/api/instrument/saddle-force

**Tuning Machine (4 endpoints)**
- GET:/api/instrument/tuning-machine/post-heights
- GET:/api/instrument/tuning-machine/string-trees
- POST:/api/instrument/tuning-machine
- POST:/api/instrument/tuning-machine/required-height

**Construction (4 endpoints)**
- GET:/api/instrument/kerfing/types
- POST:/api/instrument/kerfing
- POST:/api/instrument/brace-sizing
- POST:/api/instrument/top-deflection

**Other (3 endpoints)**
- GET:/api/instrument/nut-compensation/types
- GET:/api/instrument/soundhole/body-styles
- POST:/api/instrument/nut-compensation/zero-fret-positions

## Large Routers (>500 lines) for Phase B

| File | Lines | Status |
|------|-------|--------|
| instrument_router.py | 1,291 | **Phase A target** |
| woodworking_router.py | 596 | New, no split needed |
| binding_design_router.py | 589 | Review for split |
| cam_post_v155_router.py | 518 | Review for split |

## Migration Strategy

1. Create split routers for uncovered endpoint groups:
   - `geometry_calculator_router.py` (5 endpoints)
   - `string_tension_router.py` (3 endpoints)
   - `tuning_machine_router.py` (4 endpoints)
   - `construction_calculator_router.py` (4 endpoints)

2. Migrate endpoints with IDENTICAL schemas (not the 4 parallel implementations)

3. Update manifest to register new split routers

4. Unregister instrument_router.py when all 19 are migrated

5. Retain instrument_router.py file for reference (parallel implementations)
