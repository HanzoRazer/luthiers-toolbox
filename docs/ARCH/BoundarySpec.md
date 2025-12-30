he next micro after this: add --scan-all-malformed-classify that prints a rough tag per sample (TRUNCATED_JSON, NON_JSON_GARBAGE, BOM/ENCODING, etc.) based on simple heuristics (still no dependencies).# BoundarySpec — ToolBox ↔ Analyzer Boundary

Status: ACCEPTED  
Date: 2025-12-28  
Owners: ToolBox maintainers, Analyzer maintainers  

## Context

We maintain two separate systems:

- **Analyzer (tap_tone_pi)**: a measurement instrument that emits reproducible facts + artifacts.
- **ToolBox (luthiers-toolbox)**: orchestration + interpretation; converts facts into advisories, workflows, and CAM decisions.

Cross-imports create hidden coupling, break independent builds, and cause implementation drift.

## Decision

Enforce a hard boundary:

- Analyzer MUST NOT import ToolBox namespaces.
- ToolBox MUST NOT import Analyzer namespaces.
- Integration must occur only via:
  - file artifacts + manifests (hash/provenance),
  - HTTP APIs,
  - explicitly versioned schemas/contracts.

This boundary is enforced by CI and fails builds on violation.

## Rules

### Analyzer repo — forbidden imports

Forbidden prefixes (ToolBox package roots):

| Prefix | Reason |
|--------|--------|
| `app.*` | ToolBox application code |
| `services.*` | ToolBox service layer |
| `rmos.*` | Rosette Manufacturing OS |
| `cam.*` | CAM toolpath generation |
| `compare.*` | Comparison workflows |
| `art_studio.*` | Art Studio design tools |

Allowed:
- standard library
- Analyzer package roots (`tap_tone.*`, `modes.*`, `schemas.*`)
- declared third-party deps

### ToolBox repo — forbidden imports

Forbidden prefixes (Analyzer package roots):

| Prefix | Reason |
|--------|--------|
| `tap_tone.*` | Analyzer core measurement code |
| `modes.*` | Analyzer modal analysis |

> **Note**: `schemas.*` is NOT forbidden in ToolBox — we have our own `app/schemas/` package.
> If Analyzer renames to `tap_tone_schemas`, we'll add that to forbidden list.

Allowed:
- ToolBox package roots (`app.*`, etc.)
- declared third-party deps

## Enforcement

CI runs a boundary guard that statically scans Python files for:

- `import X`
- `from X import Y`
- `importlib.import_module("X")`
- `__import__("X")`

Violations fail CI and link to `docs/BOUNDARY_RULES.md#boundary-rules`.

### Implementation

| File | Purpose |
|------|---------|
| `services/api/app/ci/boundary_spec.py` | Reusable BoundarySpec framework |
| `services/api/app/ci/check_boundary_imports.py` | CLI runner with profile configs |

### Running Locally

```bash
cd services/api
python -m app.ci.check_boundary_imports --profile toolbox
```

## Exceptions

No code exceptions.

If integration is required:
- create/extend an artifact contract, or
- create/extend an HTTP contract

instead of importing across the boundary.

## Consequences

### Pros

- Independent builds
- Predictable ownership boundaries
- Drift prevention
- Safer refactors

### Cons

- Requires explicit contracts for integration (intentional)

## Maintenance

- Keep forbidden prefix lists aligned to real module roots.
- Add tests proving the guard catches both static imports and `importlib` usage.
- Update this ADR if boundary rules change.

## Related

- [BOUNDARY_RULES.md](../BOUNDARY_RULES.md) — Quick reference for developers
- [ROUTER_MAP.md](../../ROUTER_MAP.md) — ToolBox API organization
