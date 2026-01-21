# Mesh Pipeline v0.1.0 — Scaffold

> **Status:** Scaffold only — algorithms are stubs, contracts are real.
> **Location:** ToolBox repo (`luthiers-toolbox`)

The Mesh Pipeline provides the healing → retopo → fields → CAM policy chain
for luthiery geometry. It couples grain direction, brace topology, and
thickness data to produce manufacturing constraints that standard mesh tools lack.

---

## Quick Start

```bash
# Run the scaffold example (produces stub artifacts)
make mesh-example

# Or manually:
bash examples/retopo/run.sh qrm    # Use QuadRemesher preset
bash examples/retopo/run.sh miq    # Use MIQ preset

# Validate outputs against contract schemas
python scripts/validate_schemas.py --out-root examples/retopo
```

---

## Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Mesh Pipeline                         │
                    │                                                          │
  ┌──────────┐      │   ┌────────┐    ┌────────┐    ┌────────┐    ┌─────────┐ │
  │ Input    │──────│──▶│  Heal  │───▶│ Retopo │───▶│ Fields │───▶│ CAM     │ │
  │ Mesh     │      │   │ (Open3D)   │(MIQ/QRM)│    │ Grain/ │    │ Policy  │ │
  │ (OBJ/STL)│      │   └────────┘    └────────┘    │ Brace/ │    │ Compose │ │
  └──────────┘      │                               │ Thick  │    └─────────┘ │
                    │                               └────────┘                │
                    └─────────────────────────────────────────────────────────┘
                                                         │
                                            ┌────────────┴────────────┐
                                            ▼                         ▼
                                     qa_core.json              cam_policy.json
```

---

## Contract Schemas

### `qa_core.json`

Quality assessment coupling mesh healing, thickness zones, grain analysis,
brace topology, and retopo metrics.

| Field | Description |
|-------|-------------|
| `mesh_healing` | Holes filled, non-manifold fixes, status |
| `thickness_zones` | Thickness map with min/max per region |
| `grain_analysis` | Grain confidence, runout/checking zones |
| `brace_graph` | Node/edge counts, topology validity |
| `retopo_metrics` | Aspect ratio P95, face counts |
| `overall_status` | `pass` / `warn` / `fail` |

Schema: [`contracts/qa_core.schema.json`](../../contracts/qa_core.schema.json)

### `cam_policy.json`

Per-region manufacturing constraints derived from fields coupling.

| Field | Description |
|-------|-------------|
| `global_defaults` | Stepdown, stepover, feed rate, spindle RPM |
| `regions[]` | Type, constraints, tool limits per region |
| `coupling_flags` | Which fields contributed to policy |

Schema: [`contracts/cam_policy.schema.json`](../../contracts/cam_policy.schema.json)

---

## Module Structure

```
services/api/app/
├── retopo/
│   ├── __init__.py          # Module docstring
│   ├── run.py               # Pipeline runner (intake → export)
│   ├── miq_adapter.py       # MIQ retopo adapter (stub)
│   └── qrm_adapter.py       # QRM retopo adapter (stub)
├── fields/
│   ├── __init__.py          # Fields namespace
│   ├── grain_field/         # Grain angle/confidence
│   │   ├── __init__.py
│   │   └── service.py       # GrainFieldService
│   ├── brace_graph/         # Brace topology
│   │   ├── __init__.py
│   │   └── service.py       # BraceGraphService
│   └── thickness_map/       # Thickness zones
│       ├── __init__.py
│       └── service.py       # ThicknessMapService
└── cam/
    └── (existing CAM modules)

presets/retopo/
├── miq/preset.json          # MIQ retopo preset
├── qrm/preset.json          # QRM retopo preset
└── sidecar_logger.py        # Run logging (JSONL)

examples/retopo/
├── run.sh                   # Example runner script
├── intake.obj               # Minimal test mesh
└── out_*/                   # Generated artifacts (gitignored)

contracts/
├── qa_core.schema.json      # QA Core contract
├── cam_policy.schema.json   # CAM Policy contract
└── schema_registry.json     # Schema registry

scripts/
└── validate_schemas.py      # Schema validation
```

---

## Presets

### MIQ (`presets/retopo/miq/preset.json`)

Mixed-Integer Quadrangulation — mathematically optimal quad layouts.
Best for topology-sensitive regions (bracing zones, edges).

### QRM (`presets/retopo/qrm/preset.json`)

QuadRemesher — fast, production-quality retopo.
Good for bulk geometry with less topological sensitivity.

---

## Implementation Roadmap

### Phase 1: Scaffold (✅ Current)
- Contract schemas defined
- Pipeline runner with stubs
- CI workflow wired
- Example + validation

### Phase 2: Healing
- [ ] Wire Open3D healing ops
- [ ] Emit real hole/non-manifold counts
- [ ] Add voxel remesh fallback

### Phase 3: Retopo Adapters
- [ ] Wire QRM CLI/bindings
- [ ] Wire MIQ CLI/bindings
- [ ] Add preset tuning for lutherie

### Phase 4: Field Coupling
- [ ] Grain field from tap_tone artifacts
- [ ] Brace graph from layout JSON
- [ ] Thickness from paired scans

### Phase 5: CAM Policy Intelligence
- [ ] Grain-sensitive cut direction
- [ ] Brace no-cut zones
- [ ] Thickness-critical stepdown limits

---

## CI

The `mesh-pipeline-ci` workflow runs on:
- PRs touching `services/api/app/fields/**`, `services/api/app/retopo/**`
- PRs touching contracts or presets
- Push to `main`

Steps:
1. Run example with QRM preset
2. Run example with MIQ preset
3. Validate all outputs against schemas

---

## Related Documentation

- [BOUNDARY_RULES.md](../../docs/BOUNDARY_RULES.md) — ToolBox ↔ Analyzer separation
- [qa_core.schema.json](../../contracts/qa_core.schema.json) — QA Core contract
- [cam_policy.schema.json](../../contracts/cam_policy.schema.json) — CAM Policy contract
- [Fields Module](../app/fields/__init__.py) — Grain/brace/thickness interpretation

---

## Development Notes

### Adding a New Field

1. Create `services/api/app/fields/new_field/`
2. Add `service.py` with dataclass results
3. Update `retopo/run.py` to call the service
4. Add field data to `qa_core.json` output
5. Add policy constraints to `cam_policy.json`

### Swapping Retopo Adapter

Edit `retopo/run.py` and implement the real call in the adapter:

```python
# miq_adapter.py
def run(input_mesh: str, preset_path: str, out_dir: str) -> dict:
    import subprocess
    result = subprocess.run(["miq", "--input", input_mesh, ...])
    # Parse output, return normalized dict
```

### Validating New Artifacts

```bash
# After pipeline changes, validate:
python scripts/validate_schemas.py --out-root examples/retopo

# Or target specific directory:
python scripts/validate_schemas.py --out-root path/to/artifacts
```
