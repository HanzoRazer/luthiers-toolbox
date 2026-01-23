# Pending Patches

Tracking patches in development that require follow-up.

---

## PATCH-001: Archtop/Smart Guitar Router Design Fix

**Status**: In Development
**Created**: 2026-01-23
**Owner**: User

### Context

During the Option C migration, the following routers were removed and replaced with legacy 308 redirects:

- `archtop_router.py` → `instruments/guitar/archtop_instrument_router.py` + `cam/guitar/archtop_cam_router.py`
- `smart_guitar_router.py` → `instruments/guitar/smart_instrument_router.py` + `cam/guitar/smart_cam_router.py`

### Issue

Design issues identified in the original router implementations that need addressing in the new Option C structure.

### Files to Review

- `services/api/app/routers/instruments/guitar/archtop_instrument_router.py`
- `services/api/app/routers/instruments/guitar/smart_instrument_router.py`
- `services/api/app/routers/cam/guitar/archtop_cam_router.py`
- `services/api/app/routers/cam/guitar/smart_cam_router.py`

### Related

- `docs/ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md`
- `services/api/app/ci/deprecation_registry.json`

---

*Add new patches below this line*
