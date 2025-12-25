# Canonical API Surface

This document defines the canonical API surface for Luthier's ToolBox.

**Hard rule:** New production endpoints must land under canonical prefixes.
Legacy endpoints may remain temporarily, but must be marked as LEGACY/SHADOW and have a defined replacement path.

## Canonical Prefixes

- `/api/rmos/*` - RMOS orchestration, runs, workflow sessions, governed ops
- `/api/cam/*` - CAM operations
- `/api/art/*` - Art Studio (graphics/SVG) canonical surface (if/when promoted)
- `/api/ai/*` - Platform AI services (transport/safety/cost/observability only)

## Legacy / Shadow Prefixes (temporary)

These exist for backward compatibility and must not grow.

- Root-mounted endpoints (examples): `/feasibility`, `/toolpaths`
- Legacy sandbox prefixes (examples): `/api/art-studio/*`

## Governance Requirements

1. **Every new endpoint must have `@endpoint_meta(status=...)`.**
2. **Legacy/Shadow endpoints must declare `replacement=...` to canonical path.**
3. **Endpoints in the registry must match actual FastAPI routes** (method + path pattern).
4. **No new endpoints are allowed under legacy prefixes** without explicit architecture approval.

## Runtime Visibility

A global middleware logs a warning (once per process) when a LEGACY/SHADOW endpoint is hit.
This provides a safe observation window before removals.

## CI Checks

CI should run:

```bash
cd services/api
python -m app.ci.check_endpoint_governance
```

Failures indicate drift between:

* the authoritative registry (`app/governance/endpoint_registry.py`)
* and the actual FastAPI mounted routes.
