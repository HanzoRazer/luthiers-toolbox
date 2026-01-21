# Mesh Pipeline v0.1.0

> **Status:** Scaffold + hardened adapters (stub mode unless QRM_BIN/MIQ_BIN set)
> **Location:** ToolBox repo (`luthiers-toolbox`)

The Mesh Pipeline provides the healing → retopo → fields → CAM policy chain
for luthiery geometry. It couples grain direction, brace topology, and
thickness data to produce manufacturing constraints.

---

## Quick Start

```bash
# Run the scaffold example (stub mode - no external tools needed)
make mesh-example

# Or manually:
bash examples/retopo/run.sh qrm    # QuadRemesher preset
bash examples/retopo/run.sh miq    # MIQ preset

# With real tools (set environment first):
export QRM_BIN=/path/to/QuadRemesher
bash examples/retopo/run.sh qrm
```

---

## Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Mesh Pipeline                         │
                    │                                                          │
  ┌──────────┐      │   ┌────────┐    ┌────────┐    ┌────────┐    ┌─────────┐ │
  │ Input    │──────│──▶│  Heal  │───▶│ Retopo │───▶│ Fields │───▶│ CAM     │ │
  │ Mesh     │      │   │        │    │QRM/MIQ │    │        │    │ Policy  │ │
  └──────────┘      │   └────────┘    └────────┘    └────────┘    └─────────┘ │
                    └─────────────────────────────────────────────────────────┘
                                                         │
                                            ┌────────────┴────────────┐
                                            ▼                         ▼
                                     qa_core.json              cam_policy.json
```

---

## Module Structure

```
services/api/app/retopo/
├── __init__.py           # Package init
├── run.py                # Pipeline runner
├── qrm_adapter.py        # QuadRemesher adapter (hardened)
├── miq_adapter.py        # MIQ adapter (hardened)
├── util.py               # Subprocess helpers, sidecar logging
└── README.md             # This file

presets/retopo/
├── qrm/preset.json       # QRM preset
├── miq/preset.json       # MIQ preset
└── sidecar_logger.py     # Global run logging

examples/retopo/
├── run.sh                # Example runner
├── intake.obj            # Test mesh
└── out_*/                # Generated artifacts
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QRM_BIN` | Path to QuadRemesher CLI | (stub mode if unset) |
| `QRM_TIMEOUT_S` | QRM timeout in seconds | 300 |
| `MIQ_BIN` | Path to MIQ CLI | (stub mode if unset) |
| `PYTHON_MIQ` | Python MIQ entry point | (alternative to MIQ_BIN) |
| `MIQ_TIMEOUT_S` | MIQ timeout in seconds | 300 |

---

## Stub Mode

When `QRM_BIN`/`MIQ_BIN` is not set, adapters run in **stub mode**:
- Creates placeholder output mesh
- Returns `{"stub": True}` in metrics
- Allows CI/testing without licensed tools

---

## Outputs

### `qa_core.json`

Quality assessment with mesh healing, fields, and retopo metrics.

### `cam_policy.json`

Per-region CAM constraints from field coupling.

### `retopo_sidecar.json`

Execution log with command, timing, stdout/stderr.

---

## Integration Guide

See [docs/RETOPO_ADAPTERS.md](../../../docs/RETOPO_ADAPTERS.md) for:
- QRM CLI flag mapping
- MIQ Python binding setup
- Preset configuration
- CI strategy (fake engines)
- Troubleshooting

---

## See Also

- [RETOPO_ADAPTERS.md](../../../docs/RETOPO_ADAPTERS.md) — Full integration guide
- [qa_core.schema.json](../../../contracts/qa_core.schema.json) — QA contract
- [cam_policy.schema.json](../../../contracts/cam_policy.schema.json) — CAM policy contract
