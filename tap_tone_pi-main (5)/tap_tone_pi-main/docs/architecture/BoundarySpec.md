# BoundarySpec — ToolBox ↔ Analyzer Boundary

Status: ACCEPTED  
Date: 2025-12-28  
Owners: ToolBox maintainers, Analyzer maintainers  

## Context

We maintain two separate systems:

- **Analyzer (tap_tone_pi)**: a measurement instrument that emits reproducible facts + artifacts.
- **ToolBox (Luthier's ToolBox)**: orchestration + interpretation; converts facts into advisories, workflows, and CAM decisions.

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

Forbidden prefixes (update to match ToolBox package roots you actually use):
- `app.`
- `services.`
- `rmos.`
- `cam.`
- `compare.`
- `art_studio.`

Allowed:
- standard library
- Analyzer package roots (`tap_tone.`, `modes.`, `schemas.`)
- declared third-party deps

### ToolBox repo — forbidden imports

Forbidden prefixes:
- `tap_tone.`
- `modes.`
- `schemas.` (Analyzer-side)

Allowed:
- ToolBox package roots (e.g., `app.`)
- declared third-party deps

## Enforcement

CI runs a boundary guard that statically scans Python files for:
- `import X`
- `from X import Y`
- `importlib.import_module("X")`
- `__import__("X")`

Violations fail CI and link to README "Boundary Rules".

Location: `ci/check_boundary_imports.py`

## Exceptions

No code exceptions.

If integration is required:
- create/extend an artifact contract or
- create/extend an HTTP contract
instead of importing across the boundary.

## Consequences

Pros:
- independent builds
- predictable ownership boundaries
- drift prevention
- safer refactors

Cons:
- requires explicit contracts for integration (intentional)

## Maintenance

- Keep forbidden prefix lists aligned to real module roots.
- Add tests proving the guard catches both static imports and importlib usage.
- Update this ADR if boundary rules change.

## Related

- [README.md#boundary-rules](../../README.md#boundary-rules) — user-facing summary
- [ci/check_boundary_imports.py](../../ci/check_boundary_imports.py) — enforcement script
- [ci/boundary_spec.py](../../ci/boundary_spec.py) — BoundarySpec class
