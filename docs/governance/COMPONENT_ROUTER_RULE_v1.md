# Component Router Rule

**Document Type:** Architectural Governance Rule
**Version:** 1.0
**Effective Date:** December 20, 2025
**Status:** AUTHORITATIVE

---

## Rule Statement

> **Any instrument subdomain with >2 endpoints MUST have a dedicated component router.**

This rule prevents endpoint sprawl across multiple routers, which creates:
- Inconsistent API prefixes
- Duplicate functionality
- Poor discoverability
- Maintenance burden

---

## Canonical Component Routers

| Domain | Router | Prefix | Status |
|--------|--------|--------|--------|
| Neck | `neck_router.py` | `/api/neck` | Compliant |
| Bridge | `bridge_router.py` | `/api/bridge` | Compliant |
| Fret Design | `fret_router.py` | `/api/fret` | Compliant |
| Archtop (Instrument) | `instruments/guitar/archtop_instrument_router.py` | `/api/instruments/guitar/archtop` | Canonical (Wave 20) |
| Archtop (CAM) | `cam/guitar/archtop_cam_router.py` | `/api/cam/guitar/archtop` | Canonical (Wave 20) |
| Stratocaster (Instrument) | `instruments/guitar/stratocaster_instrument_router.py` | `/api/instruments/guitar/stratocaster` | Canonical (Wave 20) |
| Stratocaster (CAM) | `cam/guitar/stratocaster_cam_router.py` | `/api/cam/guitar/stratocaster` | Canonical (Wave 20) |
| OM (Instrument) | `instruments/guitar/om_instrument_router.py` | `/api/instruments/guitar/om` | Canonical (Wave 20) |
| OM (CAM) | `cam/guitar/om_cam_router.py` | `/api/cam/guitar/om` | Canonical (Wave 20) |
| Smart Guitar | `instruments/guitar/smart_instrument_router.py` | `/api/instruments/guitar/smart` | Canonical (Wave 20) |
| Smart Guitar (CAM) | `cam/guitar/smart_cam_router.py` | `/api/cam/guitar/smart` | Canonical (Wave 20) |

> **Note (Dec 2025):** Legacy standalone routers removed. 308 redirects via `legacy/guitar_model_redirects.py`.

---

## Compliance Criteria

### MUST

1. **Single Prefix** — All endpoints for a domain under one prefix (e.g., `/api/fret/*`)
2. **Dedicated File** — One router file per domain (`{domain}_router.py`)
3. **Wave Registration** — Registered in `main.py` under appropriate wave section
4. **Design/CAM Separation** — Design routers separate from CAM/export routers

### MUST NOT

1. **No Scatter** — Same functionality across multiple routers
2. **No Duplicate Prefixes** — `/fret/` cannot appear outside `/api/fret/*`
3. **No Mixed Concerns** — CAM operations stay in `cam_*_router.py` files

---

## Violation Detection

### Manual Check
```bash
# List all routes containing a keyword
curl -s http://localhost:8000/openapi.json | \
  jq '.paths | keys | map(select(contains("fret")))'
```

### CI Check (Recommended)
```python
# Fail build if fret routes appear outside /api/fret/
def test_no_scattered_fret_routes():
    paths = get_openapi_paths()
    for path in paths:
        if "fret" in path.lower() and not path.startswith("/api/fret"):
            if "/cam/" not in path:  # CAM exceptions allowed
                pytest.fail(f"Scattered route: {path}")
```

---

## Migration Protocol

When scattered endpoints are discovered:

1. **Create** component router following naming convention
2. **Consolidate** all related endpoints into new router
3. **Register** in `main.py` with single prefix
4. **Remove** duplicate endpoints from source routers
5. **Document** migration in `docs/reports/`

---

## Historical Context

**December 2025:** Fret endpoints were scattered across 4 routers (12 duplicate endpoints). Consolidated into `fret_router.py` with 13 endpoints under `/api/fret/*`.

See: `docs/reports/FRET_ROUTER_CONSOLIDATION_REPORT.md`

---

## Governance

| Role | Responsibility |
|------|----------------|
| Developer | Follow rule when adding endpoints |
| Reviewer | Reject PRs that violate rule |
| CI | Automated duplicate detection |

**Amendment Process:** Changes require governance review and version increment.

---

*Document Author: Claude Opus 4.5*
*Origin: Fret Router Consolidation Session*
