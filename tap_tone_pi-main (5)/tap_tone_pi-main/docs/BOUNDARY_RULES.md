## Boundary Rules

This repository (**tap_tone_pi**) is a measurement instrument repo.

**Hard boundary:** it must not import **Luthier's ToolBox** (design/CAM/RMOS) Python namespaces.

### Forbidden in Analyzer
Do not import:
- `app.*`
- `services.*`
- `packages.*`

### Why CI fails
CI runs:

`python ci/check_boundary_imports.py --preset analyzer`

If CI fails, remove the import and pass data across repos via **exported artifacts** (files + manifests), not Python imports.
