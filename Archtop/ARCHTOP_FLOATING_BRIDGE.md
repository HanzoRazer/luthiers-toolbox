
# Archtop Floating Bridge – Generator

## Flow
1. Run **/archtop/fit** to compute neck angle, bridge height range, and compensation, which writes:
   `storage/exports/archtop_fit/archtop_fit.json`
2. Call **/archtop/bridge** with:
```json
{ "fit_json_path": "storage/exports/archtop_fit/archtop_fit.json" }
```
3. Outputs (to `storage/exports/archtop_bridge/`):
   - `FloatingBridge_Generated.dxf` (if `ezdxf` installed):  
     - `BRIDGE_BASE` layer: 2D rectangle (length × width) centered at bridge X  
     - `POSTS` layer: two circles at ±post_spacing/2 (Ø 3.2mm through suggested)  
     - `SADDLE_TICKS` + `SADDLE_LINE` layers: compensated string tick marks and a polyline through them
     - `UNDERSIDE_PROFILE` layer: Y–Z curve to make a sanding jig for the bridge base
   - TSV fallbacks if DXF backend not available.

## Customize
- Post spacing: set `post_spacing_mm` in the fit JSON.
- Base size: set `bridge_base_mm.length` / `.width` in the fit JSON.
- String spacing: `string_spacing_at_saddle_mm` (default 52 mm).
- Compensation: `saddle_line_mm_from_nut` (from fit; edit to taste).

> The underside profile is a **2D section** sampled at bridge X from your plate CSV.
> Use it to shape the base to the arch (sanding jig / spindle sander form).
