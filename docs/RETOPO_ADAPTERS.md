# Retopo Adapters (QRM/MIQ) — Integration Guide

This document shows how to **swap in real retopology engines** (QuadRemesher or MIQ)
behind the stable Mesh Pipeline contracts:

- **Input:** `healed.obj` (or any intake mesh)
- **Output (normalized):** `retopo_mesh_path` + `metrics` written by the adapter
- **Pipeline then writes:** `qa_core.json` and `cam_policy.json` (already scaffolded)

---

## 0. Overview

| Item | Location |
|------|----------|
| Adapters | `services/api/app/retopo/{qrm_adapter.py, miq_adapter.py}` |
| Presets | `presets/retopo/{qrm,miq}/preset.json` |
| Utils | `services/api/app/retopo/util.py` |
| Sidecar | `<out_dir>/retopo_sidecar.json` |

**Key principle:** Each adapter shells out to a CLI or Python binding, **never** changes
the contract shape. The runner (`run.py`) consumes normalized outputs.

---

## 1. QuadRemesher (QRM)

> **Licensing:** QRM is commercial; install its CLI/binary headless on the build agent.  
> Typical binary name: `QuadRemesher` or `QuadRemesherCmd`. Paths vary by platform.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `QRM_BIN` | Path to the QuadRemesher CLI executable |
| `QRM_TIMEOUT_S` | (Optional) Fail fast if the run hangs (default: 300) |

### Minimal CLI Shape (Example)

```bash
$ QuadRemesher \
    --input in.obj \
    --output out.obj \
    --target_count 30000 \
    --adaptive 1 \
    --symmetry X
```

> Actual flags differ by version. Map your preset keys → flags in `qrm_adapter.py`.

### Determinism Tips

- Set a stable seed if the engine supports it
- Disable any implicit auto-detection modes you don't control
- Always write to a fresh temp dir (we do this in the shim)

---

## 2. Mixed-Integer Quadrangulation (MIQ)

You can use:
- A **local MIQ CLI** (e.g., an internal wrapper around libigl's MIQ), or
- A **Python path** if you've built bindings

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MIQ_BIN` | Path to MIQ CLI executable |
| `PYTHON_MIQ` | Alternative: Python entry point (`module.path:function_name`) |
| `MIQ_TIMEOUT_S` | (Optional) Timeout in seconds (default: 300) |

### Typical CLI Draft

```bash
$ miq_cli \
    --input in.obj \
    --output out.obj \
    --scale_hard_features 1.0 \
    --smoothness 0.2 \
    --singularity_opt 1
```

### Python Binding Mode

If you invoke via Python, export a single entry function:

```python
def miq_run(input_path: str, output_path: str, **kwargs) -> None:
    ...
```

Set `PYTHONPATH` plus `PYTHON_MIQ="module.path:miq_run"` (adapter resolves it).

---

## 3. Presets

Each preset JSON should contain only parameters you can map to engine flags.

### QRM Preset (`presets/retopo/qrm/preset.json`)

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

### MIQ Preset (`presets/retopo/miq/preset.json`)

```json
{
  "name": "miq-default",
  "scale_hard_features": 1.0,
  "smoothness": 0.2,
  "singularity_opt": true,
  "boundary_preservation": "strict",
  "seed": 42
}
```

### Preset → Flag Mapping

The adapters read these fields and map to CLI flags:

| Preset Field | QRM Flag | MIQ Flag |
|--------------|----------|----------|
| `target_count` | `--target_count` | N/A (uses scale) |
| `adaptive` | `--adaptive 1/0` | N/A |
| `symmetry` | `--symmetry X/Y/none` | N/A |
| `smoothness` | N/A | `--smoothness` |
| `singularity_opt` | N/A | `--singularity_opt 1/0` |
| `seed` | `--seed` | `--seed` |

---

## 4. Sidecar Logging

Adapters capture execution details to `<out_dir>/retopo_sidecar.json`:

```json
{
  "timestamp_utc": "2026-01-21T12:00:00Z",
  "adapter": "qrm",
  "cmd": ["QuadRemesher", "--input", "..."],
  "rc": 0,
  "dur_s": 45.2,
  "stdout": "...",
  "stderr": "",
  "tool_version": "3.0.1",
  "preset": "qrm-default"
}
```

**Truncation:** stdout/stderr limited to 32KB to avoid bloat.

---

## 5. QA Metrics

If the engine doesn't emit metrics, compute basic ones post-run:

| Metric | Description |
|--------|-------------|
| `vertex_count` | Total vertices in output mesh |
| `face_count` | Total faces |
| `quad_pct` | Percentage of quads vs n-gons |
| `edge_length_mean` | Mean edge length (mm) |
| `edge_length_std` | Edge length standard deviation |
| `aspect_ratio_p95` | 95th percentile aspect ratio |

The adapter's `_compute_post_metrics()` function handles this via Open3D or trimesh.

---

## 6. CI Strategy

### Fake Engine for CI (No License)

Provide a mock script that:
1. Copies input → output
2. Prints a version string
3. Exits 0

```bash
#!/bin/bash
# fake_qrm.sh
cp "$2" "$4"  # Assumes --input X --output Y ordering
echo "FakeQRM 0.0.0-stub"
```

Set `QRM_BIN=./scripts/ci/fake_qrm.sh` in CI.

### Real Engine in Self-Hosted Runners

- Gate behind `if: secrets.HAS_QRM_LICENSE`
- Install licensed binary
- Use machine-specific `QRM_BIN` path

---

## 7. Failure Modes

| Failure | Behavior |
|---------|----------|
| Missing binary | Clear error: "QRM_BIN not set or not found" |
| Non-zero exit | Surface stderr in logs, keep temp folder |
| Timeout | Kill process, write partial sidecar, return error dict |
| Output missing | Check for file, fail with "output mesh not created" |

All failures return a structured dict:

```python
{
    "error": "QRM_TIMEOUT",
    "detail": "Process killed after 300s",
    "sidecar_path": "/tmp/.../retopo_sidecar.json"
}
```

---

## 8. Adding a New Adapter

1. Create `services/api/app/retopo/new_adapter.py`
2. Implement `run(input_mesh, preset_path, out_dir) -> dict`
3. Add preset at `presets/retopo/new/preset.json`
4. Update `run.py` to dispatch based on preset name
5. Add fake engine for CI

### Template

```python
"""new_adapter.py"""
from .util import run_cmd, load_preset, write_sidecar

def run(input_mesh: str, preset_path: str, out_dir: str) -> dict:
    preset = load_preset(preset_path)
    cmd = build_cmd(input_mesh, out_dir, preset)
    result = run_cmd(cmd, timeout=preset.get("timeout_s", 300))
    write_sidecar(out_dir, "new", cmd, result, preset)
    
    if result["rc"] != 0:
        return {"error": "NEW_ADAPTER_FAILED", "detail": result["stderr"]}
    
    return {
        "retopo_mesh_path": f"{out_dir}/retopo_new.obj",
        "metrics": compute_metrics(f"{out_dir}/retopo_new.obj")
    }
```

---

## 9. Troubleshooting

### "Binary not found"

```
export QRM_BIN=/path/to/QuadRemesher
# or
export MIQ_BIN=/path/to/miq_cli
```

### "Permission denied"

```bash
chmod +x $QRM_BIN
```

### "Timeout during retopo"

Increase timeout or simplify mesh:

```bash
export QRM_TIMEOUT_S=600
```

### "Output mesh has zero faces"

Check the sidecar stderr for engine errors. Common causes:
- Non-watertight input
- Degenerate triangles
- Unsupported mesh format

---

## See Also

- [Mesh Pipeline README](../services/api/app/retopo/README.md)
- [qa_core.schema.json](../contracts/qa_core.schema.json)
- [cam_policy.schema.json](../contracts/cam_policy.schema.json)
