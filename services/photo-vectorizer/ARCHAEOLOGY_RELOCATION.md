# Archaeological / semantic modules — relocated

**Date:** 2026-05-20  
**Lifecycle:** `RELOCATED_EXTERNAL` (see `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md`)

Tier A modules were removed from the runtime spine and re-homed to the semantic cognition repo:

**https://github.com/HanzoRazer/vectorizer-sandbox**

| Former path (luthiers-toolbox) | New location (sandbox) |
|--------------------------------|-------------------------|
| `cognitive_extractor.py` | `src/semantic/cognitive_extractor.py` |
| `cognitive_extraction_engine.py` | `src/semantic/cognitive_extraction_engine.py` |
| `body_dimension_reference.json` | `src/semantic/body_dimension_reference.json` |
| `extract_body_grid.py` … `extract_body_grid_v5.py` | `src/archaeology/` |
| `services/blueprint-import/vectorizer_phase2.py` | `src/archaeology/vectorizer_phase2_runtime_spine.py` |

**Source commit:** `f1e11d995c45e882c84c1a622743931209757f04` (manifest in sandbox `MIGRATION_MANIFEST.json`)  
**Sandbox release tag:** `v0.2.0-semantic-lineage-import`

## Production path (unchanged)

Blueprint Reader MVP uses:

- `POST /api/blueprint/vectorize/async` → `CleanupMode.REFINED` → `edge_to_dxf.py`

Not Phase 2 `/vectorize-geometry` or cognitive/grid modules.

## Re-import policy

Do **not** copy these files back into `services/` without the graduation bridge
(`docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`). Enforced by
`scripts/governance/check_semantic_sandbox_imports.py` (precommit).
