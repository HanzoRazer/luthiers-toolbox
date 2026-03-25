# DXF Service — Integration Notes

## Slot into Production Shop FastAPI

```python
# main.py (your existing FastAPI app)
from dxf_service import router as dxf_router
app.include_router(dxf_router, prefix="/api/dxf")
```

## Three endpoints

| Route | Purpose |
|---|---|
| `POST /api/dxf/spline/evaluate` | Single SPLINE entity from browser dxf-parser → NURBS polyline |
| `POST /api/dxf/parse` | Full DXF file → raw entity paths + bbox + layer info |
| `POST /api/dxf/parse-and-normalize` | Full pipeline → normalized to 200×320 target space |

## Browser client modes

**`preferServer: true` (default, production)**
DXF files go entirely through the FastAPI backend. ezdxf handles all
entity types including NURBS splines. Browser does zero DXF math.

**`preferServer: false` (offline/dev)**
Browser handles LINE, LWPOLYLINE, CIRCLE, ARC in JS.
SPLINE entities POST to `/spline/evaluate` individually.
SVG files always handled in-browser.

## SPLINE evaluation path

```
Browser dxf-parser sees SPLINE entity
  ↓
forwards control_points + knot_values + degree to /api/dxf/spline/evaluate
  ↓
ezdxf BSpline(control_points, order=degree+1, knots=knot_values).approximate(n)
  ↓
returns {d: "M...L...Z", points: [{x,y}...], method: "ezdxf_bspline"}
  ↓
browser renders on Konva canvas
```

## DXF entity support

| Entity | Browser | Server |
|---|---|---|
| LINE | ✓ | ✓ |
| LWPOLYLINE (+ bulge arcs) | ✓ | ✓ |
| POLYLINE | ✓ | ✓ |
| CIRCLE | ✓ | ✓ |
| ARC | ✓ | ✓ |
| ELLIPSE | ✓ | ✓ |
| SPLINE / NURBS | approx only | ✓ full NURBS |
| INSERT (blocks) | ✗ | ✓ (flattened) |
| HATCH, TEXT, DIM | ✗ | ✗ (skipped) |

## Coordinate system

DXF uses Y-up; SVG uses Y-down.
`flip_y=True` (default) mirrors geometry across the horizontal axis
during normalization. Override with `flip_y=False` if your DXF
was already prepared for SVG coordinates.

## CORS (if browser is on different port)

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```
