# ADR-002: Mesh Pipeline Coupling Design

## Status
Accepted

## Date
2025-12-28

## Context

The "Mesh_Pipeline 2.docx" document outlined a mesh healing and retopology
pipeline with ROI analysis. The key insight was that standard mesh tools
don't incorporate domain-specific constraints like wood grain orientation
or brace topology.

This ADR documents how ToolBox extends standard mesh processing with
luthier-specific field coupling.

## Decision

### 1. Standard Mesh Pipeline (External Tools)

Use existing tools for core mesh operations:

| Stage | Tool | Output |
|-------|------|--------|
| Preprocessing | trimesh | Cleaned OBJ |
| Healing | MeshLab/pymeshlab | Watertight mesh |
| Retopology | Instant Meshes / QuadRemesher | Quad mesh |
| Export | trimesh/assimp | FBX/GLTF |

These are called via subprocess or Python bindings.

### 2. ToolBox Coupling Layer

Before/after standard mesh ops, ToolBox adds:

**Pre-Retopo:**
- Ingest grain_field → tag faces with grain confidence
- Ingest brace_graph → mark no-retopo zones at intersections
- Ingest thickness_map → weight density by voicing importance

**Post-Retopo:**
- Validate edge flow respects grain direction
- Ensure brace zones have adequate resolution
- Generate QA report

**Policy Export:**
- Combine all fields → cam_policy.json
- Per-region constraints based on coupled analysis

### 3. Sidecar Pattern

Every mesh operation produces sidecars:

```
model_healed.obj
model_healed_qa.json        # QA assessment
model_healed_manifest.json  # Provenance
```

```
model_retopo.obj
model_retopo_qa.json
model_retopo_cam_policy.json  # CAM constraints
model_retopo_manifest.json
```

### 4. Pipeline API

```python
from app.fields import grain_field, brace_graph, thickness_map
from app.pipelines.mesh import MeshPipeline

pipeline = MeshPipeline(model_id="OM_top_001")

# Ingest field data
pipeline.add_field(grain_field.from_tap_peaks("tap_peaks.json"))
pipeline.add_field(brace_graph.from_layout("x_brace_layout.json"))
pipeline.add_field(thickness_map.from_moe_results("moe_batch.csv"))

# Run pipeline with coupling
result = pipeline.run(
    input_mesh="raw_scan.stl",
    heal=True,
    retopo_target_faces=15000,
    output_dir="./out"
)

# Outputs: healed mesh, retopo mesh, QA report, CAM policy
```

## Consequences

### Positive:
- Leverages battle-tested mesh tools
- Adds domain-specific value that competitors lack
- Auditable via sidecars and manifests
- Modular field system allows incremental adoption

### Negative:
- Depends on external tool availability (Instant Meshes, MeshLab)
- More complex than single-tool approach

### Neutral:
- Field coupling is optional; pipeline works without it (just no CAM policy output)

## ROI Impact (from Mesh_Pipeline doc)

| Metric | Without Coupling | With Coupling |
|--------|-----------------|---------------|
| Geometry errors | ~10% | <1% |
| CAM setup time | 30 min | 3 min |
| Scrap rate | 5% | <1% |
| Margin impact | baseline | +7-9 pts |

## Related
- ADR-001: Fields and Policy Ownership
- Mesh_Pipeline 2.docx (source document)
- qa_core.schema.json
- cam_policy.schema.json
