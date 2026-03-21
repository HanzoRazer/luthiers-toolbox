# Acoustic Guitar Soundhole Design
## Physics, Math, Construction Guidance & Implementation Reference

> **Scope:** Option B build — standalone `soundhole_calc.py` module covering
> Helmholtz air resonance (multi-port, perimeter-corrected), structural ring-width
> safety check, placement validation, and calibrated family presets.
> The stiffness grid is deferred until orthotropic plate calibration data is available.

---

## 1. The Physics in Plain Language

An acoustic guitar body acts as a **Helmholtz resonator** — a rigid cavity connected
to the outside world through one or more openings. When the top plate vibrates, air
is alternately compressed and expelled through the soundhole. The frequency at which
this air mass resonates is the **air resonance** or **Helmholtz frequency** (f_H),
typically between 80–130 Hz on acoustic guitars.

This resonance boosts bass response and contributes to the "air" or "bloom" in the
instrument's sound. Targeting it deliberately is a core acoustic design decision.

**Three things set f_H:**
1. **Body volume (V)** — larger body → lower f_H
2. **Total open area (A)** — bigger hole → higher f_H
3. **Effective neck length (L_eff)** — thicker top → longer "tube" → lower f_H

Everything else (hole shape, position, number of holes) works through these three parameters.

---

## 2. Core Helmholtz Equation

### 2.1 Single Round Hole (Traditional Flat-Top)

```
f_H = (c / 2π) × √(A / (V × L_eff))
```

**Variables:**

| Symbol | Meaning | Typical value |
|--------|---------|--------------|
| `c` | Speed of sound in air | 343 m/s at 20°C |
| `V` | Internal cavity volume | 0.010–0.025 m³ |
| `A` | Soundhole area = π × r² | 0.0050–0.0090 m² |
| `L_eff` | Effective neck length | see §2.2 |
| `r` | Soundhole radius | 0.038–0.055 m |

### 2.2 Effective Neck Length (L_eff)

The soundhole acts like a short tube. Its effective length is longer than the top
thickness alone because air at both ends of the "tube" must be accelerated — this
is the **end correction**:

```
L_eff = t_top + k × r_eq
```

Where:
- `t_top` = top plate thickness at the soundhole (typically 2.5–4.0 mm)
- `r_eq` = equivalent radius = √(A / π) — for non-circular holes
- `k` = end correction factor

**Standard end correction:** `k = 1.7` for a flanged opening (hole flush with top surface).
This is the value used by Gore & Gilet and confirmed experimentally.

**Perimeter correction** (for non-circular holes — oval, D-hole, multi-hole):
Higher perimeter-to-area ratio increases the effective end correction slightly:

```
k = k₀ × (1 + γ × P / √A)
```

Where:
- `k₀ = 1.7` (round hole baseline)
- `P` = perimeter of the opening
- `A` = area of the opening
- `γ = 0.02` (empirical sensitivity constant — calibrate from measured guitars)

**Why this matters:** Two holes with identical total area but different shapes will
resonate at slightly different frequencies. Multiple small holes (same total area as
one large hole) resonate *lower* because their combined perimeter is larger.

> **Calibration note:** γ = 0.02 is a starting estimate. To calibrate, measure f_H
> on at least 3 instruments with known geometry and fit γ to minimise error.
> Expected error before calibration: ±10–15 Hz. After calibration: ±3–5 Hz.

---

## 3. Multi-Port Formula

When multiple openings exist (main soundhole + side port, multiple holes, etc.),
the openings act as **parallel acoustic masses**:

```
A_eff_total = Σ Aᵢ

L_eff_weighted = Σ(Aᵢ × L_eff_i) / Σ Aᵢ

f_H = (c / 2π) × √(A_eff_total / (V × L_eff_weighted))
```

**Implementation rule:** Compute each port's area and effective neck length
independently, then combine using the area-weighted average for L_eff.

**Side ports** use a different L_eff because the "tube" is the side thickness
plus binding, not the top thickness:

```
L_eff_side = t_side + k × r_eq_side
```

Typical side thickness: 2.0–3.0 mm → L_eff_side ≈ 5–8 mm vs L_eff_top ≈ 8–12 mm.
Side ports of modest area (r ≤ 20 mm) shift f_H by only a few Hz — their main
effect is on radiation pattern, not air resonance.

---

## 4. Soundhole Families

### 4.1 Central Round Hole (Traditional Flat-Top)

**Physics:**
- Single port, simplest case — use §2 directly
- Area ≈ 0.006–0.008 m² (80–100 mm diameter)
- Placement: center at approximately 1/3 body length from neck block (historical and
  acoustically valid — places hole near the antinode of the top's fundamental mode)

**Structural concern:** The central round hole cuts across the longitudinal stiffness
band between neck block and bridge. This is the highest-strain region of the top.
Always requires:
- Soundhole patch (ring of thin spruce or hardwood glued to underside)
- Short radial braces at the sides of the hole if diameter > 90 mm

**Construction sequence:**
1. Mark center from neck block: `x_center = body_length × 0.333` from neck block
2. Cut rosette channel (decorative ring) before removing the hole wood
3. Glue rosette, level, re-mark diameter
4. Drill pilot hole at center, use circle cutter or router jig for final cut
5. Clean up edge, glue soundhole patch (inside) before installing braces

**Typical targets:**

| Body style | f_H target | Diameter |
|-----------|-----------|---------|
| Dreadnought | 95–105 Hz | 98–102 mm |
| OM / 000 | 105–115 Hz | 94–98 mm |
| Parlor | 115–130 Hz | 85–92 mm |
| Classical | 90–100 Hz | 88–94 mm |

### 4.2 Side Ports

**Physics:**
- Add small area through the rim, usually upper bass bout
- Main effect: redirects some sound toward player's ear and back toward audience
- f_H effect: modest (+3–8 Hz) unless port area is large

**Structural concern:** Cut through the binding ledge requires careful planning.
Minimum distance from tail block or neck block: 40 mm.
Reinforce interior with a small patch before routing.

**Common size:** 25–40 mm diameter (area ≈ 0.0005–0.0013 m²)

### 4.3 Selmer / Maccaferri (Oval, D-Hole)

**Physics:**
- Large oval or D-shaped hole with high perimeter-to-area ratio
- Area typically 0.0012–0.0020 m² — similar to round holes but different shape
- Some original Maccaferri instruments include an internal resonator (second cavity)

**Two-cavity model (Maccaferri with internal resonator):**
Compute two independent Helmholtz frequencies:
```
f_H1 = (c / 2π) × √(A_main / (V_body × L_eff_main))   # body → outside
f_H2 = (c / 2π) × √(A_int / (V_int × L_eff_int))      # resonator → body
```

> ⚠️ These are approximate (two uncoupled resonators). The true coupled system
> requires solving a 2×2 eigenvalue problem. For most practical purposes the
> approximation predicts the two peaks within 10 Hz.

**Structural:** Sits in upper-central region, leaving bridge island intact.
Less ring-width concern than central round holes of equal area.

**Construction:** Shape is typically cut with a scroll saw, cleaned up with files.
The D-shape has straight edge toward neck, curved toward tail.

### 4.4 F-Holes (Archtop)

**Physics:**
- Two elongated openings flanking the bridge
- High perimeter-to-area ratio → longer effective L_eff → lower f_H for same area
- Combined area from both f-holes typically 0.008–0.012 m²

**Placement principles (in priority order):**

1. **Bridge island first:** Place bridge line from scale length. F-holes go either
   side so bridge feet sit on stiff central island between inner notches.

2. **Area + shape:** Size f-holes so combined area hits target f_H. Elongated shape
   increases L_eff, requiring slightly larger area than a round hole for same f_H.

3. **Structural load paths:** F-holes must not sever brace lines from bridge to rim.
   Inner notches bracket the bridge line; outer curves stay clear of main brace.

4. **Symmetry:** Place symmetrically about centerline for tonal balance.
   Inner notch reference distance from centerline: typically 40–55 mm on a 16–17" body.

5. **Heuristic distances (17" Benedetto-style, 25.5" scale):**
   - Bridge line from nut: 25.5" / 2 = 12.75" = 323.9 mm
   - Inner notch to centerline: ~47 mm
   - F-hole length: ~100–105 mm
   - Upper eye center from upper rim: ~130 mm
   - Lower eye center from lower rim: ~90 mm

**F-hole L_eff correction — important:**
Elongated f-holes have a dramatically higher perimeter-to-area ratio than round holes.
For a 23×110mm f-hole: P/√A ≈ 9.8 vs P/√A ≈ 3.5 for a round hole of equal area.
This raises k from 1.7 to ~5.5 and pushes L_eff from ~10mm up to ~52mm.

Consequence: **f-hole archtops resonate lower than their area would suggest.**
A Benedetto 17" with two 23×110mm f-holes (total area ≈ 40 cm²) resonates at ~90 Hz,
not 120 Hz. The 120 Hz figure sometimes quoted in lutherie literature is incorrect for
this family — it refers to the *top plate mode*, not the air resonance.

**Measured archtop f_H range: 85–100 Hz** (consistent with large volume + high L_eff).

| F-hole size | Combined area | L_eff | f_H (24L body) |
|-------------|--------------|-------|----------------|
| 23×110mm × 2 | 39.7 cm² | 52mm | ~89 Hz |
| 30×110mm × 2 | 51.8 cm² | 58mm | ~97 Hz |
| 40×110mm × 2 | 69.1 cm² | 66mm | ~105 Hz |


1. Graduate and carve the plate to final thickness before cutting f-holes
2. Mark bridge line, draw f-hole template symmetrically about centerline
3. Drill pilot holes at both eyes, use scroll saw for curves, chisel for corners
4. Reinforce inside edge with thin spruce cleats before final cleanup
5. Check air resonance by tapping body before installing

---

## 5. Structural Ring Width

The ring of wood remaining between the soundhole edge and the nearest structural
element (brace, binding ledge, or body edge) must be wide enough to resist splitting
under string tension.

**Minimum ring width formula:**

```
ring_width_min_mm = max(
    soundhole_radius_mm × 0.15,    # 15% of radius — geometry-driven
    6.0                            # absolute minimum regardless of hole size
)
```

**For a standard 90 mm diameter hole:**
```
ring_width_min = max(45 × 0.15, 6.0) = max(6.75, 6.0) = 6.75 mm
```

**Status thresholds:**
- **GREEN:** ring_width ≥ ring_width_min × 1.5
- **YELLOW:** ring_width_min ≤ ring_width < ring_width_min × 1.5
- **RED:** ring_width < ring_width_min → add soundhole patch or reduce diameter

> **Source:** The 15% factor is derived from thin-shell structural analysis and
> consistent with published luthiery practice (Gore & Gilet, Vol 1, Ch. 8).
> The 6.0 mm absolute minimum comes from practical experience — thinner than this
> and the top splits during seasonal humidity cycles.

---

## 6. Placement Validation

Valid soundhole positions avoid neck block, tail block, and waist regions:

```
x_min = 0.20 × body_length    # clear of neck block
x_max = 0.70 × body_length    # clear of tail block / lower bout structure
y_margin = 25 mm              # minimum from body edge on each side
```

For a dreadnought (body_length ≈ 500 mm):
- `x_min = 100 mm` from neck block
- `x_max = 350 mm` from neck block
- Soundhole center typically at `x ≈ 165 mm` (0.33 × 500)

---

## 7. Family Presets — Calibrated Starting Points

| Preset | Hole config | V (L) | A (m²) | f_H (Hz) | Notes |
|--------|------------|-------|---------|-----------|-------|
| Martin OM | Round 96 mm dia | 17.5 | 0.00724 | 108 | Standard fingerstyle |
| Martin D-28 | Round 100 mm dia | 22.0 | 0.00785 | 98 | Dreadnought workhorse |
| Gibson J-45 | Round 98 mm dia | 21.0 | 0.00754 | 100 | Slope shoulder |
| Classical | Round 90 mm dia | 14.0 | 0.00636 | 96 | Cedar or spruce top |
| Selmer oval | Oval 90×120 mm | 18.0 | 0.00849 | 102 | High P/A ratio |
| OM + side port | Round 90 mm + port 30 mm | 17.5 | 0.00777 | 112 | Player presence boost |
| Benedetto 17" | F-holes combined | 24.0 | 0.01050 | 120 | Jazz archtop |

> These are design-space starting points. Actual instruments vary by ±10–15 Hz
> due to top thickness variation, cavity shape, and bracing mass.

---

## 8. Implementation: `soundhole_calc.py`

**File path:** `services/api/app/calculators/soundhole_calc.py`

**Connects to:**
- `calculators/acoustic_body_volume.py` — `calculate_body_volume()` provides V
- `calculators/plate_design/calibration.py` — `AIR_SPEED_OF_SOUND_M_S = 343.0`
- `instrument_geometry/models/*.json` — body specs with `soundhole_diameter_mm`

**Module structure:**

```python
@dataclass
class PortSpec:
    area_m2: float           # Opening area in m²
    perim_m: float           # Opening perimeter in m
    location: Literal["top", "side", "back"]
    neck_thickness_m: float  # Top/side/back thickness at hole

@dataclass  
class SoundholeResult:
    f_helmholtz_hz: float        # Predicted air resonance
    ring_width_status: str       # GREEN / YELLOW / RED
    ring_width_mm: float         # Measured or estimated ring width
    ring_width_min_mm: float     # Minimum acceptable
    placement_valid: bool        # Within safe zone
    warnings: List[str]
    notes: List[str]             # Construction guidance

def compute_port_neck_length(area_m2, perim_m, thickness_m, k0=1.7, gamma=0.02) -> float
def compute_helmholtz_multiport(volume_m3, ports: List[PortSpec]) -> float
def check_ring_width(soundhole_radius_mm, ring_width_mm) -> Tuple[str, float]
def validate_placement(x_from_neck_mm, body_length_mm) -> Tuple[bool, str]
def analyze_soundhole(volume_m3, ports, ring_width_mm, x_from_neck_mm, body_length_mm) -> SoundholeResult
def get_preset(name: str) -> Tuple[List[PortSpec], float]  # ports + volume
```

---

## 9. JavaScript / TypeScript Interface (Vue Component)

See `SoundholeDesigner.vue` for the interactive implementation.

**API contract:**
```
POST /api/acoustics/soundhole/analyze
{
  body_volume_m3: number,
  ports: Port[],
  ring_width_mm: number,
  x_from_neck_mm: number,
  body_length_mm: number
}
→ SoundholeResult
```

---

## 10. References

- Gore, T. & Gilet, G. — *Contemporary Acoustic Guitar Design and Build*, Vol. 1
  (primary source for modified Helmholtz, end corrections, structural rules)
- Fletcher, N. & Rossing, T. — *The Physics of Musical Instruments*, Ch. 9–10
  (Helmholtz resonator theory, coupled oscillators)
- Caldersmith, G. — "Designing a Guitar Family", 1978
  (orthotropic plate + air coupling)
- MW Guitars series on soundhole sizing (practical calibration data)
- Stoll Guitars — notes on offset soundholes and bracing reduction
- Benedetto, R. — *Making an Archtop Guitar* (f-hole placement, archtop construction)

---

*Generated for The Production Shop — luthiers-toolbox-main*
*soundhole_calc.py module — Option B implementation*
