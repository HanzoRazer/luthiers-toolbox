# CAM Export Bundle — Complete Implementation Manifest

**Date:** December 15, 2025  
**Source:** CAM_Export_Bundle__OpPlan_files.docx (3126 lines parsed)  
**Status:** All code extracted and ready for integration

---

## Overview

This bundle adds a complete CAM export pipeline and mesh generation system:

1. **Export helpers** — JSON and text file export utilities
2. **CLI command** — `ig_export cam-profile-op` for batch exports
3. **Sidewall mesh** — Vertical walls only (CAM-friendly)
4. **Solid mesh** — Watertight with caps (fan or earclip triangulation)
5. **Polygon cleanup** — Remove duplicates, collinear vertices
6. **Self-intersection handling** — Detection and bow-tie splitting

All code is:
- **Dependency-free** — No Shapely, no triangulation libs
- **Deterministic** — Stable for golden tests
- **Pure Python** — Standard library only

---

## File Manifest

### Exports Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `exports/__init__.py` | `instrument_geometry/exports/__init__.py` | 0 | Package marker |
| `exports/paths.py` | `instrument_geometry/exports/paths.py` | ~25 | ExportPaths dataclass |
| `exports/cam_export.py` | `instrument_geometry/exports/cam_export.py` | ~25 | export_json, export_text |
| `exports/mesh_obj.py` | `instrument_geometry/exports/mesh_obj.py` | ~25 | OBJ mesh exporter |

### CLI Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `cli/__init__.py` | `instrument_geometry/cli/__init__.py` | 0 | Package marker |
| `cli/ig_export.py` | `instrument_geometry/cli/ig_export.py` | ~95 | CLI entry point |

### Models Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `models/__init__.py` | `instrument_geometry/models/__init__.py` | 0 | Package marker |
| `models/mesh.py` | `instrument_geometry/models/mesh.py` | ~35 | TriangleMesh dataclass |

### Queries Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `queries/__init__.py` | `instrument_geometry/queries/__init__.py` | 0 | Package marker |
| `queries/polygon_cleanup.py` | `instrument_geometry/queries/polygon_cleanup.py` | ~100 | Ring cleanup utilities |
| `queries/polygon_self_intersection.py` | `instrument_geometry/queries/polygon_self_intersection.py` | ~150 | Self-intersection detection |
| `queries/pocket_sidewall_mesh.py` | `instrument_geometry/queries/pocket_sidewall_mesh.py` | ~70 | Sidewall-only mesh |
| `queries/pocket_solid_mesh.py` | `instrument_geometry/queries/pocket_solid_mesh.py` | ~350 | Full solid mesh with all hardening |

### API Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `api/__init__.py` | `instrument_geometry/api/__init__.py` | 0 | Package marker |
| `api/keys.py` | `instrument_geometry/api/keys.py` | ~10 | Query key constants (additions) |
| `api/registry.py` | `instrument_geometry/api/registry.py` | ~25 | QuerySpec entries (additions) |

### Tests Package
| File | Target | Lines | Purpose |
|------|--------|-------|---------|
| `tests/__init__.py` | `instrument_geometry/tests/__init__.py` | 0 | Package marker |
| `tests/test_cam_export_pipeline.py` | `instrument_geometry/tests/test_cam_export_pipeline.py` | ~20 | Export smoke test |
| `tests/test_pocket_sidewall_mesh.py` | `instrument_geometry/tests/test_pocket_sidewall_mesh.py` | ~20 | Sidewall mesh test |
| `tests/test_pocket_solid_mesh.py` | `instrument_geometry/tests/test_pocket_solid_mesh.py` | ~30 | Solid mesh tests |
| `tests/test_polygon_cleanup.py` | `instrument_geometry/tests/test_polygon_cleanup.py` | ~35 | Cleanup tests |
| `tests/test_earclip_triangulation.py` | `instrument_geometry/tests/test_earclip_triangulation.py` | ~40 | Earclip tests |
| `tests/test_polygon_self_intersection.py` | `instrument_geometry/tests/test_polygon_self_intersection.py` | ~50 | Self-intersection tests |

**Total:** ~18 files, ~1100 lines of code

---

## Feature Summary

### 1. CAM Export Pipeline
```bash
python -m instrument_geometry.cli.ig_export cam-profile-op \
  --case ig_default_tele \
  --out exports/cam
```

Outputs:
- `{case}__{op_id}.opplan.json` — Operation plan
- `{case}__{op_id}.grbl.nc` — G-code

### 2. Mesh Generation

**Sidewall mesh** (vertical walls only):
```python
mesh = geom.api.get(
    K.TRUSS_UNION_SIDEWALL_MESH,
    z_top_mm=0.0,
    z_floor_mm=-10.0,
)
```

**Solid mesh** (watertight with caps):
```python
mesh = geom.api.get(
    K.TRUSS_UNION_SOLID_MESH,
    z_top_mm=0.0,
    z_floor_mm=-10.0,
    cap_mode="earclip",  # or "fan"
)
```

### 3. Cap Triangulation Modes

| Mode | Use Case | Handles Concave? |
|------|----------|------------------|
| `fan` | Convex polygons only | ❌ |
| `earclip` | Any simple polygon | ✅ |

### 4. Hardening Features

| Feature | Default | Purpose |
|---------|---------|---------|
| `cleanup_tol_mm` | 1e-6 | Remove near-duplicate vertices |
| `collinear_eps` | 1e-12 | Remove collinear vertices |
| `fallback_on_fail` | True | Return sidewalls-only if earclip fails |
| `reject_self_intersections` | True | Refuse to cap self-intersecting rings |
| `auto_split_self_intersections` | False | Split bow-ties into two valid rings |

### 5. OBJ Export

```python
from instrument_geometry.exports.mesh_obj import export_obj

mesh = geom.api.get(K.TRUSS_UNION_SOLID_MESH, z_top_mm=0.0, z_floor_mm=-10.0)
export_obj(mesh, Path("exports/cam/truss_union_solid.obj"))
```

Compatible with: Blender, FreeCAD, Fusion 360, MeshLab

---

## Mesh Metadata

All meshes include metadata for debugging:

```json
{
  "type": "triangle_mesh",
  "vertex_count": 48,
  "triangle_count": 92,
  "meta": {
    "cap_mode": "earclip",
    "ccw": true,
    "cap_status": "ok_earclip",
    "input_count": 26,
    "removed_duplicates": 2,
    "removed_collinear": 0,
    "self_intersection": {"status": "none"}
  }
}
```

---

## Integration Steps

### 1. Copy Files

```bash
# From this bundle to your instrument_geometry package
cp -r exports/ /path/to/instrument_geometry/
cp -r cli/ /path/to/instrument_geometry/
cp -r models/ /path/to/instrument_geometry/
cp -r queries/ /path/to/instrument_geometry/
cp -r tests/ /path/to/instrument_geometry/
```

### 2. Update API Keys

Add to `instrument_geometry/api/keys.py`:
```python
TRUSS_UNION_SIDEWALL_MESH = "truss_union_sidewall_mesh"
TRUSS_UNION_SOLID_MESH = "truss_union_solid_mesh"
```

### 3. Update Registry

Add to `instrument_geometry/api/registry.py`:
```python
from ..queries.pocket_sidewall_mesh import build_pocket_sidewall_mesh
from ..queries.pocket_solid_mesh import build_pocket_solid_mesh

# In REGISTRY dict:
K.TRUSS_UNION_SIDEWALL_MESH: QuerySpec(...),
K.TRUSS_UNION_SOLID_MESH: QuerySpec(...),
```

### 4. Add Dependency (if missing)

The only import that needs to exist is:
```python
from ..queries.truss_union_outline_pipeline2d import get_truss_union_outline_final_2d
```

If this doesn't exist, create a stub or adjust the import.

### 5. Run Tests

```bash
pytest instrument_geometry/tests/test_polygon_cleanup.py -v
pytest instrument_geometry/tests/test_earclip_triangulation.py -v
pytest instrument_geometry/tests/test_polygon_self_intersection.py -v
pytest instrument_geometry/tests/test_pocket_solid_mesh.py -v
```

---

## Algorithm Details

### Ear Clipping

1. Ensure ring is CCW (reverse if CW)
2. Find a "convex" vertex (positive cross product)
3. Check no other vertex lies inside the ear triangle
4. Clip the ear, repeat until 3 vertices remain
5. Deterministic: always clips first valid ear found

### Self-Intersection Detection

1. O(n²) segment-segment intersection test
2. Skip adjacent segments
3. Return first hit (lowest i, then j)

### Bow-Tie Splitting

1. Find intersection point P
2. Split ring at P into two paths
3. Each path becomes a separate valid ring
4. Clean both rings, build separate solids, merge

---

## Future Extensions

From the source document, these are the "next shipments" mentioned:

1. **Vertex normals + smooth/flat shading groups** — For cleaner previews
2. **Multi-intersection planar graph split** — Handles complex self-intersections
3. **Top/bottom caps with draft angle** — Tapered pockets
4. **Mesh-based collision envelopes** — Tool holder clearance

---

## Verification Checklist

- [ ] All 18 files copied to correct locations
- [ ] API keys added
- [ ] Registry entries added
- [ ] Import path for `get_truss_union_outline_final_2d` verified
- [ ] Polygon cleanup tests pass
- [ ] Earclip tests pass
- [ ] Self-intersection tests pass
- [ ] Solid mesh tests pass
- [ ] CLI export works
- [ ] OBJ files open in Blender/MeshLab
