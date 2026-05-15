# Thickness Hierarchy Model

**Sprint:** MRP-5E  
**Status:** RESEARCH COMPLETE  
**Type:** Semantic Architecture

---

## Purpose

Define the progressive levels of thickness representation for acoustic body CAD translation. Each level adds complexity; translators may support any subset of levels.

---

## Hierarchy Levels

### Level 1: Uniform Thickness

**Description:** Single thickness value applied to entire body extrusion.

**Schema:**
```python
uniform_thickness_mm: float  # e.g., 45.0
```

**CAD Topology:** Simple extrusion of closed profile.

**Current Status:** IMPLEMENTED (MRP-5C flat-body translator)

**Use Cases:**
- Electric guitar bodies (solid or chambered)
- Prototype/visualization exports
- CNC roughing operations

---

### Level 2: Component Thickness

**Description:** Distinct thickness values for major body components.

**Schema:**
```python
class ComponentThickness:
    top_thickness_mm: float      # Soundboard thickness (2.5-3.5mm)
    back_thickness_mm: float     # Back plate thickness (2.0-3.0mm)
    side_depth_mm: float         # Rim height (varies 95-125mm)
```

**CAD Topology:** Multi-body assembly OR shell with variable walls.

**Current Status:** SCHEMA_READY (data exists in INSTRUMENT_SPECS)

**IBG Source Data:**
| Field | Source | Typical Value |
|-------|--------|---------------|
| top_thickness_mm | INSTRUMENT_SPECS | 2.8mm (dreadnought) |
| back_thickness_mm | INSTRUMENT_SPECS | 2.5mm (dreadnought) |
| butt_depth_mm | INSTRUMENT_SPECS | 121mm |
| shoulder_depth_mm | INSTRUMENT_SPECS | 105mm |

**Use Cases:**
- Acoustic guitar body shells
- Assembly planning
- Material estimation

---

### Level 3: Zonal Thickness

**Description:** Thickness varies by named zones on each component.

**Schema:**
```python
class ZonalThickness:
    top_zones: Dict[str, float]   # {"center": 2.8, "edge": 2.5, "soundhole_ring": 3.0}
    back_zones: Dict[str, float]  # {"center": 2.5, "edge": 2.2}
    side_zones: Dict[str, float]  # {"butt": 121, "waist": 115, "shoulder": 105}
```

**CAD Topology:** Lofted surfaces with zone-based thickness offsets.

**Current Status:** DERIVABLE (zone definitions exist, interpolation possible)

**Zone Definitions:**

**Top Zones:**
| Zone | Location | Typical Range |
|------|----------|---------------|
| center | Under bridge | 2.8-3.2mm |
| soundhole_ring | Around soundhole | 3.0-3.5mm |
| lower_bout | Below soundhole | 2.5-2.8mm |
| upper_bout | Above soundhole | 2.3-2.6mm |
| edge | Perimeter 10mm | 2.2-2.5mm |

**Back Zones:**
| Zone | Location | Typical Range |
|------|----------|---------------|
| center | Spine | 2.5-2.8mm |
| brace_landing | Under braces | 2.5-2.8mm |
| field | General area | 2.2-2.5mm |
| edge | Perimeter 10mm | 2.0-2.3mm |

**Side Zones:**
| Zone | Location | Typical Depth |
|------|----------|---------------|
| butt | Tail block | 121mm |
| lower_bout | Below waist | 118mm |
| waist | Narrowest point | 115mm |
| upper_bout | Above waist | 110mm |
| shoulder | Neck joint | 105mm |

**Use Cases:**
- Graduated tops/backs
- Tap-tuning guidance
- Material optimization

---

### Level 4: Continuous Thickness Field

**Description:** Thickness defined as continuous scalar field over surface.

**Schema:**
```python
class ContinuousThickness:
    top_field: SurfaceField      # f(u, v) → thickness_mm
    back_field: SurfaceField
    interpolation: Literal["linear", "spline", "rbf"]
```

**CAD Topology:** NURBS surfaces with parameterized thickness.

**Current Status:** RESEARCH_ONLY

**Barriers:**
- Requires NURBS/B-spline surface representation
- No current CAD kernel integration
- Tap-tuning feedback loop not implemented

**Research Direction:**
- Parametric surface representation
- Thickness gradient functions
- Acoustic optimization integration

**Target Sprint:** MRP-6+ (post-acoustic CAD prototype)

---

## Level Comparison Matrix

| Aspect | Level 1 | Level 2 | Level 3 | Level 4 |
|--------|---------|---------|---------|---------|
| Schema complexity | LOW | LOW | MEDIUM | HIGH |
| CAD complexity | SIMPLE | MEDIUM | HIGH | VERY HIGH |
| IBG data ready | YES | YES | PARTIAL | NO |
| Implementation status | DONE | SCHEMA_READY | DERIVABLE | RESEARCH |
| Use case | Electric | Acoustic shell | Graduated | Optimized |

---

## Translator Support Matrix

| Translator | Level 1 | Level 2 | Level 3 | Level 4 |
|------------|---------|---------|---------|---------|
| body_outline_dxf_r12 | YES | N/A | N/A | N/A |
| body_outline_dxf_r2000 | YES | N/A | N/A | N/A |
| body_outline_svg | YES | N/A | N/A | N/A |
| body_outline_step_ap203 | YES | FUTURE | FUTURE | NO |
| acoustic_body_step (proposed) | NO | YES | FUTURE | NO |

**Note:** 2D translators (DXF, SVG) only support Level 1 (profile + depth).

---

## Promotion Path

### Level 1 → Level 2

**Requirements:**
- [ ] Component thickness fields added to cad_semantics
- [ ] STEP translator generates multi-body or shell
- [ ] Regression tests for component separation

### Level 2 → Level 3

**Requirements:**
- [ ] Zone definitions standardized
- [ ] Interpolation between zones implemented
- [ ] Loft surface generation working
- [ ] Zonal thickness verified against lutherie specs

### Level 3 → Level 4

**Requirements:**
- [ ] NURBS surface representation
- [ ] CAD kernel integration (CadQuery/OCC)
- [ ] Parametric thickness functions
- [ ] Acoustic feedback integration

---

## Authority Model

| Level | Data Source | CAD Translator Role |
|-------|-------------|---------------------|
| 1 | cad_semantics.uniform_thickness_mm | CONSUME → EXTRUDE |
| 2 | INSTRUMENT_SPECS / cad_semantics | CONSUME → CONSTRUCT |
| 3 | User input / IBG zones | CONSUME → INTERPOLATE |
| 4 | Optimization engine | CONSUME → PARAMETERIZE |

**Key Rule:** Translator CONSUMES thickness data. It does NOT derive or estimate thickness values.

---

## Related Documents

- `ACOUSTIC_BODY_SEMANTIC_MODEL.md`
- `ACOUSTIC_CAD_SEMANTIC_RULES.md`
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md`
- `ACOUSTIC_CAD_READINESS_MATRIX.md`
