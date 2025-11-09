
# N17 — Polygon Offset (join types + arc linkers + feed floors)

This update exposes **join_type** (`miter|round|bevel`) and **arc_tolerance** (mm),
and upgrades the emitter to produce **corner arcs (G2/G3)** with configurable **link_radius**
and **feed floors** for tight curvature.

## Endpoint
`POST /cam/polygon_offset.nc`

### Request
```json
{
  "polygon": [[0,0],[80,0],[80,50],[0,50],[0,0]],
  "tool_dia": 6.0,
  "stepover": 2.4,
  "inward": true,
  "z": -1.5,
  "safe_z": 5.0,
  "units": "mm",
  "feed": 600.0,
  "feed_arc": 500.0,
  "feed_floor": 300.0,
  "join_type": "round",
  "arc_tolerance": 0.15,
  "link_mode": "arc",
  "link_radius": 1.0
}
```

**Notes**
- Install `pyclipper` for robust offset geometry. Fallback is miter-only for simple shapes.
- `join_type=round` with a moderate `arc_tolerance` can smooth internal corners.
- `feed_floor` caps the minimum feed on tight arcs to reduce burning/chatter.
- Set `link_mode="line"` for legacy linear output.
