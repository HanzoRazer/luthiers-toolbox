# Frontend Migration Ticket: Fret Endpoint Consolidation

**Ticket ID:** FE-2025-001
**Priority:** Medium
**Type:** Breaking Change Migration
**Status:** Open
**Created:** December 20, 2025

---

## Summary

Fret design endpoints have been consolidated from 4 scattered routers into a single `fret_router.py`. Frontend code must be updated to use the new canonical paths.

---

## Breaking Changes

All old fret endpoints are **REMOVED**. Frontend calls to these paths will return 404.

---

## Endpoint Migration Map

### From `instrument_geometry_router` → `fret_router`

| Old Path | New Path | Method |
|----------|----------|--------|
| `/api/instrument_geometry/frets/positions` | `/api/fret/table` | POST |
| `/api/instrument_geometry/fretboard/outline` | `/api/fret/board/outline` | POST |
| `/api/instrument_geometry/radius/at_fret` | `/api/fret/radius/compound` | POST |
| `/api/instrument_geometry/fan_fret/calculate` | `/api/fret/fan/calculate` | POST |
| `/api/instrument_geometry/fan_fret/validate` | `/api/fret/fan/validate` | POST |
| `/api/instrument_geometry/fan_fret/presets` | `/api/fret/fan/presets` | GET |

### From `ltb_calculator_router` → `fret_router`

| Old Path | New Path | Method |
|----------|----------|--------|
| `/api/calculators/fret/position` | `/api/fret/position` | POST |
| `/api/calculators/fret/table` | `/api/fret/table` | POST |

### From `instrument_router` → `fret_router`

| Old Path | New Path | Method |
|----------|----------|--------|
| `/api/instrument/geometry/frets` | `/api/fret/table` | POST |
| `/api/instrument/geometry/fretboard` | `/api/fret/board/outline` | POST |
| `/api/instrument/geometry/fret-slots` | `/api/fret/board/slots` | POST |

### From `temperament_router` → `fret_router`

| Old Path | New Path | Method |
|----------|----------|--------|
| `/api/temperaments/staggered` | `/api/fret/staggered` | POST |

---

## New Canonical Endpoints

All fret functionality is now under `/api/fret/*`:

```
/api/fret/
├── position              POST  Single fret position
├── table                 POST  Complete fret table
├── board/
│   ├── outline           POST  Fretboard geometry
│   └── slots             POST  Fret slot endpoints
├── radius/
│   ├── compound          POST  Radius at fret
│   └── presets           GET   Common radius profiles
├── fan/
│   ├── calculate         POST  Multi-scale positions
│   ├── validate          POST  Geometry validation
│   └── presets           GET   Fan-fret configs
├── staggered             POST  Alt temperament frets
├── temperaments          GET   Available systems
├── scales/presets        GET   Scale length presets
└── health                GET   Health check
```

---

## Code Changes Required

### TypeScript/JavaScript

```typescript
// BEFORE (multiple scattered imports)
const fretTable = await api.post('/instrument_geometry/frets/positions', data);
const fanFret = await api.post('/instrument_geometry/fan_fret/calculate', data);
const staggered = await api.post('/temperaments/staggered', data);
const fretPosition = await api.post('/calculators/fret/position', data);

// AFTER (single consolidated prefix)
const fretTable = await api.post('/fret/table', data);
const fanFret = await api.post('/fret/fan/calculate', data);
const staggered = await api.post('/fret/staggered', data);
const fretPosition = await api.post('/fret/position', data);
```

### Search Patterns

Use these patterns to find code that needs updating:

```bash
# Find old endpoint references
grep -r "instrument_geometry.*fret" src/
grep -r "calculators/fret" src/
grep -r "temperaments/staggered" src/
grep -r "instrument/geometry/fret" src/

# Find old path patterns
grep -rE "(frets/positions|fan_fret|at_fret)" src/
```

---

## Request/Response Compatibility

**Request bodies are unchanged.** The same JSON payloads work with new endpoints.

**Response bodies are unchanged.** Frontend parsing logic does not need modification.

---

## Testing Checklist

- [ ] Fret table generation works
- [ ] Fan-fret calculations work
- [ ] Compound radius lookup works
- [ ] Staggered fret generation works
- [ ] Fretboard outline rendering works
- [ ] Fret slot coordinates correct
- [ ] All presets endpoints return data
- [ ] Health check returns healthy

---

## Rollback Plan

If issues are discovered:

1. Backend can temporarily re-add old routes (not recommended)
2. Frontend can revert to previous commit
3. API versioning can be introduced (future consideration)

**Recommended:** Complete migration rather than maintain dual paths.

---

## Timeline

| Phase | Task | Owner | Status |
|-------|------|-------|--------|
| 1 | Backend consolidation | Backend | ✅ Complete |
| 2 | CI governance tests | Backend | ✅ Complete |
| 3 | Frontend migration | Frontend | ⬜ Open |
| 4 | E2E test updates | QA | ⬜ Open |
| 5 | Documentation update | Docs | ⬜ Open |

---

## Related Documents

- `docs/governance/COMPONENT_ROUTER_RULE_v1.md` - Governance rule
- `docs/reports/FRET_ROUTER_CONSOLIDATION_REPORT.md` - Full technical details
- `services/api/tests/test_route_governance.py` - CI enforcement

---

## Acceptance Criteria

- [ ] No frontend code references old endpoints
- [ ] All fret-related features work in UI
- [ ] E2E tests pass with new paths
- [ ] No 404 errors in production logs for fret routes

---

*Created by: Claude Opus 4.5*
*Origin: Fret Router Consolidation Session*
