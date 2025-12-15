 Short doc: docs/instrument/Neck_Taper_DXF_Export.md

So future-you (and GitHub) know what this is:

# Neck Taper DXF Export

**Goal:** Emit a minimal, R12-safe DXF file for tapered neck/fingerboard
geometry using the Neck Taper Suite.

## Files

- `services/api/app/instrument_geometry/neck_taper/dxf_exporter.py`
  - `build_r12_polyline_dxf(points, layer, closed)` – core R12 POLYLINE writer
  - `write_r12_polyline_dxf_file(points, out_path, layer, closed)`
  - `export_neck_outline_to_dxf(inputs, frets, out_path, layer)`

- `services/api/app/instrument_geometry/neck_taper/api_router.py`
  - `/instrument/neck_taper/outline` – JSON outline
  - `/instrument/neck_taper/outline.dxf` – DXF download (optional)

## DXF Strategy

- Uses **POLYLINE / VERTEX / SEQEND** for maximum R12 compatibility.
- Does **not** rely on LWPOLYLINE.
- Units are whatever the underlying math uses (mm or inches) – conventions
  must be respected by downstream CAM.

## Typical Workflow

1. User or RMOS supplies:
   - `scale_length`, `nut_width`, `end_fret`, `end_width`
2. Backend:
   - Computes tapered outline using `generate_neck_outline()`
   - Builds R12 DXF via `build_r12_polyline_dxf()`
3. Client:
   - Downloads `neck_taper.dxf`
   - Opens in CAD/CAM or passes to downstream pipeline.
