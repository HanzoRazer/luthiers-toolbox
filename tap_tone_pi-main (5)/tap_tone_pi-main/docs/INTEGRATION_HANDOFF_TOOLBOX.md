# Integration Handoff — Luthier’s ToolBox (Paste‑and‑Go)

This handoff bundles the minimal files and exact contents you can paste into the ToolBox repository to enable mesh retopo sidecars, CAM policy composition, presets, examples, and schema validation CI.

Repo assumptions:
- ToolBox root has: `services/api/app/…`, `contracts/`, `presets/`, `examples/`, `.github/workflows/`
- Analyzer (this repo) remains measurement‑only; do NOT import `services/api/app` here.

## Contracts (JSON Schemas)

Path: `contracts/qa_core.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "qa_core.schema.json",
  "title": "Mesh QA & Retopo Sidecar",
  "type": "object",
  "required": ["artifact_type", "mesh", "retopo", "fields", "qa"],
  "properties": {
    "artifact_type": { "const": "mesh_qa_sidecar" },
    "mesh": {
      "type": "object",
      "required": ["source_path","units"],
      "properties": {
        "source_path": {"type":"string"},
        "units": {"enum":["mm","cm","in"]},
        "bbox_mm": {"type":"array","items":{"type":"number"},"minItems":6,"maxItems":6}
      }
    },
    "retopo": {
      "type": "object",
      "required": ["engine","params","metrics"],
      "properties": {
        "engine": {"enum":["miq","qrm","instant_meshes"]},
        "params": {"type":"object"},
        "metrics": {
          "type":"object",
          "properties": {
            "quad_ratio":{"type":"number"},
            "avg_valence":{"type":"number"},
            "n_flips":{"type":"integer"},
            "anisotropy_gamma":{"type":"number"},
            "edge_len_target_mm":{"type":"number"}
          }
        }
      }
    },
    "fields": {
      "type":"object",
      "properties":{
        "grain_field_path":{"type":"string"},
        "thickness_map_path":{"type":"string"},
        "brace_graph_path":{"type":"string"}
      }
    },
    "qa": {
      "type":"object",
      "properties": {
        "nonmanifold_edges":{"type":"integer"},
        "holes_filled":{"type":"integer"},
        "thin_zones_mm2":{"type":"number"},
        "uv_ok":{"type":"boolean"}
      }
    }
  }
}
```

Path: `contracts/cam_policy.schema.json`
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "$id":"cam_policy.schema.json",
  "title":"CAM Policy (Per-Region Caps)",
  "type":"object",
  "required":["artifact_type","regions","provenance"],
  "properties":{
    "artifact_type":{"const":"cam_policy"},
    "regions":{
      "type":"array",
      "items":{
        "type":"object",
        "required":["name","geometry_ref","caps"],
        "properties":{
          "name":{"type":"string"},
          "geometry_ref":{"type":"string"},
          "caps":{
            "type":"object",
            "properties":{
              "max_stepdown_mm":{"type":"number"},
              "max_stepover_mm":{"type":"number"},
              "min_tool_diam_mm":{"type":"number"},
              "no_cut":{"type":"boolean"},
              "spring_pass":{"type":"boolean"}
            },
            "required":["max_stepdown_mm","max_stepover_mm","min_tool_diam_mm"]
          }
        }
      }
    },
    "provenance":{
      "type":"object",
      "properties":{
        "grain_field":{"type":"string"},
        "thickness_map":{"type":"string"},
        "brace_graph":{"type":"string"},
        "analyzer_facts":{"type":"array","items":{"type":"string"}}
      }
    }
  }
}
```

## Services (API app)

Path: `services/api/app/retopo/sidecar_logger.py`
```python
from __future__ import annotations
import json, time, pathlib
from dataclasses import dataclass, asdict

@dataclass
class RetopoParams:
    engine: str           # "miq" | "qrm" | "instant_meshes"
    params: dict

@dataclass
class RetopoMetrics:
    quad_ratio: float | None = None
    avg_valence: float | None = None
    n_flips: int | None = None
    anisotropy_gamma: float | None = None
    edge_len_target_mm: float | None = None

def write_sidecar(mesh_path: str, units: str, out_path: str, rp: RetopoParams, rm: RetopoMetrics,
                  field_refs: dict | None = None, qa: dict | None = None):
    sidecar = {
        "artifact_type":"mesh_qa_sidecar",
        "mesh":{"source_path":mesh_path,"units":units},
        "retopo":{"engine":rp.engine,"params":rp.params,"metrics":asdict(rm)},
        "fields": field_refs or {},
        "qa": qa or {},
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(sidecar,f,indent=2)
    return out_path
```

Path: `services/api/app/retopo/select_retopo.py`
```python
import argparse, json
from .sidecar_logger import RetopoParams, RetopoMetrics, write_sidecar

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["miq","qrm","instant_meshes"], required=True)
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--units", default="mm")
    ap.add_argument("--params", help="JSON string of engine params", default="{}")
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    rp = RetopoParams(engine=a.engine, params=json.loads(a.params))
    rm = RetopoMetrics()  # fill after retopo run if available
    write_sidecar(a.mesh, a.units, a.out, rp, rm)

if __name__ == "__main__":
    main()
```

Path: `services/api/app/cam/policy/compose_policy.py`
```python
import json, argparse, math

def choose_caps(grain_gamma: float | None, density_g_cm3: float | None):
    # conservative example; wire real mapping later
    stepdown = 0.6 if (grain_gamma and grain_gamma > 1.5) else 0.8
    stepover = 35.0
    return {"max_stepdown_mm": stepdown, "max_stepover_mm": stepover, "min_tool_diam_mm": 1.0, "spring_pass": True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--qa-sidecar", required=True)
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    sidecar = json.load(open(a.qa_sidecar, "r", encoding="utf-8"))
    gamma = sidecar.get("retopo",{}).get("metrics",{}).get("anisotropy_gamma")
    caps = choose_caps(gamma, None)
    policy = {
      "artifact_type":"cam_policy",
      "regions":[
        {"name":"binding_channel","geometry_ref":"rim_binding_zone","caps":caps},
        {"name":"rosette_inlay","geometry_ref":"rosette_zone","caps":caps}
      ],
      "provenance":{
        "grain_field": sidecar.get("fields",{}).get("grain_field_path"),
        "thickness_map": sidecar.get("fields",{}).get("thickness_map_path"),
        "brace_graph": sidecar.get("fields",{}).get("brace_graph_path"),
        "analyzer_facts":[]
      }
    }
    json.dump(policy, open(a.out,"w",encoding="utf-8"), indent=2)

if __name__=="__main__":
    main()
```

## Presets

Path: `presets/retopo/qrm/QRM-Rim.json`
```json
{"target_edge_mm": 2.5, "preserve_sharp": true, "symmetry": "none"}
```

Path: `presets/retopo/miq/MIQ-RosetteInlay.json`
```json
{"edge_target_mm": 1.2, "align_field": "grain", "singularity_penalty": 0.3}
```

## Examples

Path: `examples/retopo/miq_example_result.json`
```json
{
  "artifact_type": "mesh_qa_sidecar",
  "mesh": {"source_path": "rim_highpoly.obj", "units": "mm"},
  "retopo": {
    "engine": "miq",
    "params": {"edge_target_mm": 2.0, "align_field": "grain"},
    "metrics": {"quad_ratio": 0.94, "avg_valence": 4.1, "n_flips": 0, "anisotropy_gamma": 1.6}
  },
  "fields": {"grain_field_path": "fields/rim_grain.exr"},
  "qa": {"nonmanifold_edges": 0, "holes_filled": 3, "thin_zones_mm2": 0.0}
}
```

## Schema Validation CI

Path: `.github/workflows/contracts_validate.yml`
```yaml
name: contracts-validate
on: [push, pull_request]
jobs:
  jsonschema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install jsonschema
      - name: Validate retopo examples
        run: |
          python - <<'PY'
          import json, sys, glob
          from jsonschema import validate
          qa = json.load(open('contracts/qa_core.schema.json'))
          for f in glob.glob('examples/retopo/*result*.json'):
              data=json.load(open(f))
              validate(data, qa)
          print("QA examples valid")
          PY
```

## Notes
- Keep these files exclusively in ToolBox; Analyzer should only reference contracts conceptually.
- After paste‑in, run CI locally:
```bash
python - <<'PY'
import json, glob
from jsonschema import validate
qa = json.load(open('contracts/qa_core.schema.json'))
for f in glob.glob('examples/retopo/*result*.json'):
    validate(json.load(open(f)), qa)
print('QA examples valid')
PY
```
- Wire your retopo runner to record real `RetopoMetrics` after execution and re‑write the sidecar.

---

## Attachment Meta Index Integration (RMOS Acoustics)

This section documents the contract for ToolBox endpoints that consume the attachment meta index produced by tap_tone_pi viewer packs.

### Source Contract (Analyzer-side)

The analyzer exports `viewer_pack_v1` ZIPs containing `viewer_pack.json` manifests. The ToolBox ingests these and builds an attachment meta index.

**Index fields available for faceting/filtering:**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `kind` | string | `files[].kind` | Viewer-facing classification (non-interpretive) |
| `mime` | string | `files[].mime` | MIME type |
| `bytes` | int | `files[].bytes` | File size |
| `sha256` | string | `files[].sha256` | Content hash |
| `relpath` | string | `files[].relpath` | Path within ZIP |

**Valid `kind` values** (from `contracts/viewer_pack_v1.schema.json`):
```
audio_raw, spectrum_csv, analysis_peaks, coherence,
transfer_function, wolf_candidates, wsi_curve,
provenance, plot_png, session_meta, manifest, unknown
```

### ToolBox Endpoint: Attachment Meta Facets

**Purpose:** Return counts and unique values over the attachment meta index for UI orientation.

**Route:**
```
GET /api/rmos/acoustics/index/attachment_meta/facets
```

**Response Schema:**
```json
{
  "facets": {
    "kind": {
      "audio_raw": 128,
      "spectrum_csv": 128,
      "analysis_peaks": 128,
      "wsi_curve": 16,
      "wolf_candidates": 16,
      "plot_png": 64
    },
    "mime": {
      "audio/wav": 128,
      "text/csv": 144,
      "application/json": 64,
      "image/png": 64
    }
  },
  "total_attachments": 448,
  "index_version": "attachment_meta_v1"
}
```

**Rules (measurement-only):**
- Counts only, no interpretation
- Keys come directly from indexed metadata
- Missing categories omitted (no zero rows)
- Deterministic ordering (sorted keys)
- No filesystem access — index-only
- No shard paths disclosed

**Pydantic schemas for ToolBox:**
```python
# services/api/app/rmos/acoustics/acoustics_schemas.py

from pydantic import BaseModel
from typing import Dict

class AttachmentMetaFacetCounts(BaseModel):
    kind: Dict[str, int]
    mime: Dict[str, int]

class AttachmentMetaFacetsOut(BaseModel):
    facets: AttachmentMetaFacetCounts
    total_attachments: int
    index_version: str
```

**Implementation sketch:**
```python
# services/api/app/rmos/acoustics/attachment_meta.py

from collections import Counter
from typing import Dict, Any

def compute_facets(index: list[dict]) -> dict:
    """Compute facet counts from attachment meta index.
    
    Args:
        index: List of attachment meta records (from ingested viewer packs)
        
    Returns:
        Facet counts dict suitable for AttachmentMetaFacetsOut
    """
    kind_counts: Counter = Counter()
    mime_counts: Counter = Counter()
    
    for record in index:
        kind_counts[record.get("kind", "unknown")] += 1
        mime_counts[record.get("mime", "application/octet-stream")] += 1
    
    return {
        "facets": {
            "kind": dict(sorted(kind_counts.items())),
            "mime": dict(sorted(mime_counts.items())),
        },
        "total_attachments": len(index),
        "index_version": "attachment_meta_v1",
    }
```

**Router addition:**
```python
# services/api/app/rmos/acoustics/acoustics_router.py

@router.get("/index/attachment_meta/facets", response_model=AttachmentMetaFacetsOut)
async def get_attachment_meta_facets():
    """Return facet counts for attachment meta index."""
    index = load_attachment_meta_index()  # Your index loader
    return compute_facets(index)
```

### Future: Recent Attachments Endpoint

After facets, the next endpoint reuses the same index:

```
GET /api/rmos/acoustics/index/attachment_meta/recent?kind=...&limit=...
```

**Query params:**
- `kind`: Filter by attachment kind (optional)
- `limit`: Max results (default 20, max 100)

**Response:** Same structure as browse, ordered by ingestion timestamp descending.

