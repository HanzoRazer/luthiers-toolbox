# Spiral Soundhole Design — Developer Handoff

**Date:** 2026-04-30  
**Status:** Complete and production-ready  
**Sprint:** Part of soundhole type system (commit 985e2ad7)

---

## Executive Summary

The spiral soundhole is a logarithmic spiral slot design based on Williams 2019 acoustic research. It achieves higher perimeter-to-area (P:A) ratio than traditional round soundholes, improving acoustic coupling efficiency. The implementation supports both single spirals and dual-spiral configurations (e.g., Carlos Jumbo body with displaced f-hole logic).

---

## Physics Foundation

**Logarithmic spiral equation:**
```
r(θ) = r₀ × e^(k×θ)
```

**Closed-form acoustic metrics:**
```
Perimeter:  P = 2 × (r_end - r₀) / sin(atan(1/k))
Area:       A = slot_width × (r_end - r₀) / sin(atan(1/k))
P:A ratio:  P/A = 2 / slot_width   (independent of k, turns, size)
```

**Williams threshold:** P:A > 0.10 mm⁻¹ for significant efficiency gain over round hole.

| Slot Width | P:A Ratio | Verdict |
|------------|-----------|---------|
| 14mm | 0.143 | Above threshold |
| 18mm | 0.111 | Just above |
| 20mm | 0.100 | At threshold |
| 25mm | 0.080 | Below threshold |

---

## File Architecture

### Core Geometry Engine
**`services/api/app/instrument_geometry/soundhole/spiral_geometry.py`**

| Class/Function | Purpose |
|----------------|---------|
| `SpiralSpec` | Dataclass — single spiral parameters (center, r₀, k, turns, slot_width, rotation) |
| `SpiralGeometry` | Dataclass — computed points (centerline, walls) and metrics (area, perimeter, P:A) |
| `DualSpiralSpec` | Dataclass — upper + lower spirals for dual-spiral bodies |
| `DualSpiralGeometry` | Dataclass — combined geometry with total area |
| `compute_spiral_geometry(spec)` | Core computation — returns `SpiralGeometry` |
| `compute_dual_geometry(dual)` | Computes both spirals and combined stats |
| `generate_dxf(dual_spec, path)` | Exports DXF R12 via `dxf_writer.py` |
| `default_carlos_jumbo_spec()` | Factory — returns preset Carlos Jumbo dual-spiral |

**Key internal functions:**
- `_spiral_points()` — generates centerline points
- `_spiral_walls()` — offsets ±slot_width/2 perpendicular to tangent
- `_closed_form_stats()` — closed-form P, A, P:A calculation

### Facade Layer
**`services/api/app/calculators/soundhole_facade.py`**

| Entity | Purpose |
|--------|---------|
| `SoundholeType` | Enum: ROUND, OVAL, SPIRAL, FHOLE |
| `SpiralParams` | Dataclass — API-facing spiral parameters |
| `compute_soundhole_spec()` | Unified entry point — handles all soundhole types |
| `list_soundhole_types()` | Returns dropdown options with descriptions |

**Spiral-specific logic in `compute_soundhole_spec()`:**
- Computes closed-form geometry inline
- Calculates equivalent diameter for position calculations
- Gates on P:A threshold and slot width validation

### Presets
**`services/api/app/calculators/soundhole_presets.py`**

| Preset ID | Slot Width | P:A | Notes |
|-----------|------------|-----|-------|
| `standard_14mm` | 14mm | 0.143 | Default — good for most bodies |
| `compact_12mm` | 12mm | 0.167 | High P:A, smaller footprint |
| `wide_18mm` | 18mm | 0.111 | More area for bass |
| `carlos_jumbo_upper` | 14mm | 0.143 | Bass side, rotation 270° |
| `carlos_jumbo_lower` | 14mm | 0.143 | Treble side, rotation 90° |

### Router / API Endpoints
**`services/api/app/routers/instrument_geometry/soundhole_router.py`**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/soundhole` | POST | Calculate soundhole spec (all types) |
| `/soundhole/types` | GET | List types + spiral presets |
| `/soundhole/spiral/default` | GET | Carlos Jumbo default spec |
| `/soundhole/spiral/geometry` | POST | Compute dual-spiral geometry (JSON) |
| `/soundhole/spiral/dxf` | POST | Export dual-spiral DXF |
| `/soundhole/spiral/validate` | POST | Validate spec, return warnings |

**Request/Response models:**
- `SpiralParamsRequest` — Pydantic model with validation (8-30mm slot, 0.05-0.40 k)
- `SpiralSpecRequest` — Extended spec with center position
- `DualSpiralRequest` — Upper + lower specs + body_type
- Validation warns on narrow slots (<10mm) and high growth rates (>0.35)

---

## DXF Output

**Layers produced:**
| Layer | Purpose | Color |
|-------|---------|-------|
| `SPIRAL_OUTER_WALL` | CNC cut path | 1 (red) |
| `SPIRAL_INNER_WALL` | CNC cut path | 2 (yellow) |
| `SPIRAL_CENTERLINE` | Reference only | 3 (green) |
| `BODY_REFERENCE` | Body outline | 5 (blue) |
| `BRACE_KEEPOUT` | Brace zones | 6 (magenta) |

**Format:** R12 (AC1009) with LINE entities via `dxf_writer.py`  
**Coordinate system:** Origin at bridge centerline, mm units

---

## Test Coverage

**`services/api/tests/test_soundhole_spiral.py`**

| Test Class | Coverage |
|------------|----------|
| `TestSpiralGeometryBasic` | Points generated, area positive, spiral grows outward |
| `TestPARatio` | P:A above 0.10, narrow slots have higher P:A |
| `TestDXFExport` | File created, contains expected layers |
| `TestEdgeCases` | Zero turns, small start radius, offset center |

**`services/api/tests/test_soundhole_spiral_endpoint.py`** — API integration tests

---

## Default Carlos Jumbo Configuration

```python
DualSpiralSpec(
    upper=SpiralSpec(
        center_x_mm=-88.0,      # Bass side
        center_y_mm=-62.0,      # Above bridge
        start_radius_mm=10.0,
        growth_rate_k=0.18,
        turns=1.1,
        slot_width_mm=14.0,
        rotation_deg=270.0,     # Opens toward neck
        label="Upper bass-side spiral"
    ),
    lower=SpiralSpec(
        center_x_mm=78.0,       # Treble side
        center_y_mm=112.0,      # Below bridge
        start_radius_mm=10.0,
        growth_rate_k=0.18,
        turns=1.1,
        slot_width_mm=14.0,
        rotation_deg=90.0,      # Opens toward bridge
        label="Lower treble-side spiral"
    ),
    body_type="carlos_jumbo",
    notes="Displaced f-hole logic. Upper follows rim toward neck, lower toward bridge."
)
```

---

## Integration Points

### With Soundhole Type System
Spiral is one option in `SoundholeType` enum. The unified `compute_soundhole_spec()` dispatches to spiral-specific logic when `soundhole_type=SPIRAL`.

### With DXF Writer
Uses central `dxf_writer.py` (R12 format) — complies with CLAUDE.md DXF output standard.

### With Helmholtz Calculator
Spiral area feeds into `soundhole_calc.py` multiport Helmholtz calculation. Equivalent diameter computed as `2 × √(area/π)`.

---

## Design Decisions

1. **Closed-form P:A** — P:A = 2/slot_width is exact for constant-width spirals. No numerical integration needed.

2. **Wall offset via tangent normal** — Outer/inner walls computed by offsetting perpendicular to spiral tangent at each point, maintaining constant slot width.

3. **Dual-spiral as first-class** — Carlos Jumbo dual-spiral is the primary use case; single spiral supported through partial configuration.

4. **Pydantic validation** — Slot width 8-30mm, growth rate k 0.05-0.40, turns 0.5-2.5 enforced at API boundary.

5. **Acoustic verdict in response** — Endpoints return `above_threshold`, `approaching_threshold`, or `below_threshold` for each spiral.

---

## Extension Points

| Extension | Implementation Notes |
|-----------|---------------------|
| Single-spiral endpoint | Add `/soundhole/spiral/single/geometry` using `compute_spiral_geometry()` directly |
| Variable slot width | Replace constant `slot_width_mm` with function `slot_width(θ)` in wall offset |
| Spiral + round hybrid | Compute combined area for Helmholtz; separate DXF layers |
| G-code output | Add CAM adapter calling spiral geometry → toolpath |

---

## Reference

**Williams 2019 research:** mwguitars.com.au Parts 7-8  
**Math documentation:** `docs/LUTHERIE_MATH.md` (not yet added — spiral formulas inline in code)  
**CLAUDE.md:** Spiral is one option in `SoundholeType` dropdown, not standalone tool

---

*Handoff prepared by Claude Code*  
*For The Production Shop — luthiers-toolbox*
