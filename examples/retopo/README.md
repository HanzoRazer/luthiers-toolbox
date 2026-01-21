# Mesh Pipeline Examples — Retopo (QRM / MIQ)

This folder contains a minimal, contract-stable example that exercises the Mesh Pipeline:

- Intake → **heal + QA** (Open3D if available; OBJ fallback otherwise)
- Retopo via **QRM** or **MIQ** adapter (shims by default; ready for real engines)
- Outputs:
  - `qa_core.json` — mesh QA metrics & counts (holes, non-manifold edges approx, edge stats)
  - `cam_policy.json` — deterministic CAM caps in contract form
  - `healed.obj` — output of the healing pass
  - `retopo.obj` — output from the selected adapter (placeholder OBJ in shims)
  - `retopo_sidecar.json` — optional sidecar with adapter stdout/stderr, rc, dur_s (when wired)

> The example is designed to run **without** licensed tools. If Open3D wheels are not available for your platform,
> the pipeline falls back to a tiny OBJ topology pass and still produces valid contracts.

---

## Quick start

From repo root:

```bash
# QRM preset path
bash examples/retopo/run.sh qrm

# MIQ preset path
bash examples/retopo/run.sh miq
```

Artifacts are written to:

```
examples/retopo/out_qrm/
examples/retopo/out_miq/
```

Validate all produced JSON artifacts against contracts:

```bash
python scripts/validate_schemas.py --out-root examples/retopo
```

Or use the Makefile target:

```bash
make mesh-example
```

---

## Inputs

* `examples/retopo/intake.obj` — a minimal placeholder mesh (triangulated).
  Replace with a real model for richer QA metrics.

---

## Presets

Preset files live under:

```
presets/retopo/qrm/preset.json
presets/retopo/miq/preset.json
```

These JSONs map directly to adapter flags. You may add fields like:

```json
{
  "name": "qrm-default",
  "target_count": 30000,
  "prioritize_quads": true,
  "minimize_poles": true,
  "adaptive": true,
  "symmetry": "none",
  "seed": 42
}
```

> The shims ignore unknown keys; real adapters should map each key to the engine's CLI/bindings.

---

## Environment & dependencies

* **Python 3.11**
* **jsonschema** (for schema validation)
* **open3d** (optional) — healing step will use it if available; otherwise a fallback runs

Install:

```bash
python -m pip install --upgrade pip
pip install jsonschema
pip install open3d || true
```

---

## How the example works

1. **Healing + QA**

   * If Open3D is installed:

     * Remove duplicated/degenerate triangles, non-manifold edges, unreferenced vertices.
     * Compute counts (holes via boundary loops, non-manifold edge approx via edge adjacency >2), edge-length stats, and self-intersections.
   * If not installed:

     * A tiny OBJ parser computes the same topological counts (except self-intersections).
2. **Retopo adapter (preset-selected)**

   * **QRM** or **MIQ** shim is called; in the scaffold they emit a placeholder `retopo.obj`.
   * When real engines are wired, outputs remain **contract-identical**.
3. **Contracts emitted**

   * `qa_core.json`, `cam_policy.json` with `schema_id`/`schema_version` pinned by registry.

---

## Determinism

* Use a fixed `seed` in presets (if supported by your engines).
* The example produces deterministic JSON (timestamps aside), and CI compares only schema validity.

---

## Troubleshooting

* **Open3D wheel not found**: the pipeline falls back automatically; you can ignore the warning.
* **Schema validation fails**: run `python scripts/validate_schemas.py --out-root examples/retopo` and read the reported paths/messages.
* **Adapter errors with real engines**:

  * Ensure `QRM_BIN` / `MIQ_BIN` (or `PYTHON_MIQ`) are set in the environment.
  * Check `retopo_sidecar.json` for `stdout/stderr` and return code.

---

## Next steps

* Swap in real **QRM/MIQ** binaries (see `docs/RETOPO_ADAPTERS.md`).
* Replace `intake.obj` with your real intake mesh.
* Extend `cam_policy.json` composition logic once grain/thickness fields are implemented.
