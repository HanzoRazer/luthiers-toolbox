# Mesh Pipeline v${VERSION}

**Tag:** `toolbox-mesh-pipeline-v${VERSION}`
**Scope:** ToolBox (design/geometry/CAM). Analyzer remains measurement-only.

## Highlights

- Contracts & registry entries: **`qa_core` v1.0**, **`cam_policy` v1.0**
- Minimal **Open3D healing + QA** (holes, non-manifold edges approx, edge stats) with OBJ fallback
- Retopo adapters: **QRM** and **MIQ** shims (ready for real engines; contract-stable outputs)
- Example runner: `examples/retopo/run.sh` for **qrm/miq** paths
- Schema validation tooling + CI workflow
- Topology unit tests for `_edge_map_from_triangles` and `_boundary_loops`

## What's included

- `services/api/app/mesh/o3d_heal.py` — healing + QA
- `services/api/app/retopo/{run.py, qrm_adapter.py, miq_adapter.py}` — retopo pipeline
- `services/api/app/cam/policy/{compose.py, export.py}` — CAM policy composition
- `contracts/schemas/{qa_core.schema.json, cam_policy.schema.json}` — contracts
- `contracts/schema_registry.json` — registry entries
- `examples/retopo/{run.sh, intake.obj, README.md}` — runnable example
- `scripts/validate_schemas.py` — registry-driven validator
- `.github/workflows/mesh-pipeline-ci.yml` — CI to run examples and validate artifacts

## Getting started

```bash
# Run QRM example (shim)
bash examples/retopo/run.sh qrm

# Run MIQ example (shim)
bash examples/retopo/run.sh miq

# Validate produced JSON against contracts
python scripts/validate_schemas.py --out-root examples/retopo
```

Artifacts will appear in:

```
examples/retopo/out_qrm/
examples/retopo/out_miq/
```

Key files:

* `qa_core.json`
* `cam_policy.json`
* `healed.obj`
* `retopo.obj`

## Engine integration (optional)

Wire real engines by setting environment variables on runners/hosts:

* QuadRemesher CLI: `QRM_BIN=/path/to/QuadRemesher`
* MIQ CLI: `MIQ_BIN=/path/to/miq_cli`

  * or Python entry: `PYTHON_MIQ="module.submodule:function"`

See `docs/RETOPO_ADAPTERS.md` for flag mapping and sidecar logging.

## Contracts & governance

* Contracts are **stable**; adapters must not change output shapes.
* Version bumps to contracts require updating `contracts/schema_registry.json` (CI-guarded).

## Known limitations

* Retopo adapters in this release are **shims**; they generate placeholder `retopo.obj`.
* Grain/brace/thickness field computations are **stubs** pending algorithm drops.
* Open3D may be unavailable on some CI runners; fallback keeps contracts valid.

## CI status

This release includes:

* Schema validation in CI
* Example runs for both presets (qrm/miq)
* Topology unit tests independent of Open3D

---

*Paste this body when drafting the GitHub Release. Replace `${VERSION}` with the tag version (e.g., `0.1.0`).*
