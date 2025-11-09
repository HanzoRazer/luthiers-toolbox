
# v16.1 — Helical Ramping (Alpha Nightingale)

This feature adds a **helical ramp** entry strategy for hardwoods to avoid straight plunges.
It generates a 3D polyline helix and emits controller-agnostic G-code (`G1`) that your posts
can further optimize (e.g., true helical `G2/G3` if supported).

## API
`POST /cam/helical_ramp.nc` → returns `text/plain` G-code

**Request:**
```json
{
  "center": [0,0],
  "start_xy": [6,0],
  "z_top": 2.0,
  "z_bottom": -3.0,
  "pitch": 3.0,
  "radius": 6.0,
  "ccw": true,
  "segments_per_rev": 64,
  "units": "mm",
  "safe_z": 5.0,
  "feed_xy": 600.0,
  "feed_z": 180.0,
  "spindle": 12000,
  "coolant": false
}
```

**Notes**
- `pitch` controls Z drop per revolution (mm).
- `radius` should be ≥ tool radius; adjust for stock clearance.
- Posts can inject headers/footers and convert the helix to arc motions when supported.
- Safe, conservative feeds are used for entry; override as needed in UI/post.

## UI
Use `<CamHelicalRampingToggle />` in **CamSettings.vue** — the included diff inserts it.
The button exports an `.nc` using the current widget parameters.

## Smoke
Run:
```bash
python scripts/smoke_v16_1_helical.py
```
